import streamlit as st 
import requests
import os
from docx import Document
import openai
import pandas as pd

# Canvas API token and base URL
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'  # Replace with your Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

# OpenAI API Key from Streamlit secrets
try:
    openai.api_key = st.secrets["openai"]["api_key"]
except KeyError:
    st.error("OpenAI API key is missing. Please check your configuration.")
    openai.api_key = None

# Function to get submissions for an assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    submissions_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    
    try:
        response = requests.get(submissions_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.error(f"An error occurred: {err}")
    return []

# Function to download a submission file
def download_submission_file(file_url, filename):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.get(file_url, headers=headers)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred while downloading: {http_err}")
    except Exception as err:
        st.error(f"An error occurred while downloading: {err}")
    return False

# Function to generate grading and feedback using OpenAI
def generate_grading_feedback(submission_text, proposed_answer):
    if openai.api_key is None:
        st.error("OpenAI API key is not configured. Cannot generate feedback.")
        return None, None

    prompt = (
        f"Evaluate the following student's submission against the proposed answer. "
        f"Assess how well the submission aligns with the proposed answer and rate it on a scale of 0 to 100. "
        f"If the submission does not directly respond to the proposed answer, give zero and provide detailed feedback.\n\n"
        f"Submission: {submission_text}\n"
        f"Proposed Answer: {proposed_answer}\n\n"
        f"Provide a detailed assessment of the alignment, including strengths, weaknesses, and areas for improvement."
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        feedback_content = response['choices'][0]['message']['content'].strip()
        
        grade_line = feedback_content.split("\n")[0]
        grade = grade_line.split(": ")[1].split("/")[0] if "Grade:" in grade_line else "0"
        feedback = "\n".join(feedback_content.split("\n")[1:])
        
        return grade, feedback
    except Exception as e:
        st.error(f"Error in OpenAI API call: {e}")
        return None, None

# Function to submit grades and feedback to Canvas
def submit_feedback_to_canvas(course_id, assignment_id, user_id, grade, feedback):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    submission_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    payload = {
        "submission": {
            "posted_grade": grade
        },
        "comment": {
            "text_comment": feedback
        }
    }
    
    try:
        response = requests.put(submission_url, headers=headers, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred while submitting feedback: {http_err}")
    except Exception as err:
        st.error(f"An error occurred while submitting feedback: {err}")
    return False

# Streamlit UI
st.title("Canvas Assignment Submissions Downloader, Grader, and Preview")

# Set Course and Assignment IDs
course_id = 2850  # Replace with your course ID
assignment_id = 45964  # Replace with your assignment ID

# Download submissions when the button is pressed
if st.button("Download All Submissions", key='download_button'):
    submissions = get_submissions(course_id, assignment_id)
    
    if submissions:
        download_folder = "submissions"
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        table_data = []

        for submission in submissions:
            user_id = submission['user_id']
            user_name = submission['user']['name'] if 'user' in submission else f"User {user_id}"
            attachments = submission.get('attachments', [])
            
            submission_text = ""
            for attachment in attachments:
                file_url = attachment['url']
                filename = os.path.join(download_folder, f"{user_id}_{attachment['filename']}")
                
                if download_submission_file(file_url, filename):
                    st.success(f"Downloaded {filename}")
                    
                    if filename.endswith(".txt"):
                        with open(filename, "r") as f:
                            submission_text = f.read()
                    elif filename.endswith(".docx"):
                        doc = Document(filename)
                        submission_text = "\n".join([para.text for para in doc.paragraphs])
                
                table_data.append({"Student Name": user_name, "Submission": submission_text, "User ID": user_id})
        
        st.success("All submissions downloaded successfully.")
        
        submissions_df = pd.DataFrame(table_data)
        st.dataframe(submissions_df)

        submissions_df.to_csv("submissions_data.csv", index=False)

# Grading and Feedback Section
st.header("Grade and Provide Feedback on Submission")

# Proposed answers input
proposed_answer = st.text_area("Enter Proposed Answer:", height=100)

if 'submissions' in locals() and submissions:
    if proposed_answer:
        feedback_data = []

        submissions_df = pd.read_csv("submissions_data.csv")

        for index, row in submissions_df.iterrows():
            submission_text = row['Submission']
            user_name = row['Student Name']
            user_id = row['User ID']

            auto_grade, auto_feedback = generate_grading_feedback(submission_text, proposed_answer)
            
            st.text_area(f"Submission by {user_name}", submission_text, height=200, disabled=True, key=f"submission_{index}")
            grade = st.text_input("Grade", value=auto_grade if auto_grade else "Enter grade here", key=f"grade_{index}")
            feedback = st.text_area("Feedback", value=auto_feedback if auto_feedback else "Enter feedback here", height=100, key=f"feedback_{index}")

            feedback_data.append({
                "Student Name": user_name,
                "Submission": submission_text,
                "Grade": grade,
                "Feedback": feedback,
                "User ID": user_id
            })

        feedback_df = pd.DataFrame(feedback_data)
        st.dataframe(feedback_df)

        if st.button("Submit Feedback to Canvas"):
            for _, row in feedback_df.iterrows():
                user_id = row["User ID"]
                grade = row["Grade"]
                feedback = row["Feedback"]
                
                if submit_feedback_to_canvas(course_id, assignment_id, user_id, grade, feedback):
                    st.success(f"Feedback submitted for {row['Student Name']}")
                else:
                    st.error(f"Failed to submit feedback for {row['Student Name']}")
