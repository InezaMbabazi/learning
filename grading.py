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
        response.raise_for_status()  # Raise an error for HTTP errors
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
        return None

    prompt = (
        f"Evaluate the following student's submission against the proposed answer. "
        f"Assess how well the submission aligns with the proposed answer and rate it on a scale of 0 to 100. "
        f"If the submission does not directly respond to the proposed answer, give zero and provide detailed feedback.\n\n"
        f"Submission: {submission_text}\n"
        f"Proposed Answer: {proposed_answer}\n\n"
        f"Provide a detailed assessment of the alignment, including strengths, weaknesses, and areas for improvement. "
        f"Do not mention 'Strengths' if there is no alignment with the proposed answer."
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        st.error(f"Error in OpenAI API call: {e}")
        return None

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
        
        # Prepare data for displaying in a table
        table_data = []

        for submission in submissions:
            user_id = submission['user_id']
            user_name = submission['user']['name'] if 'user' in submission else f"User {user_id}"
            originality_score = submission.get('originality_score', 'N/A')  # Retrieve originality score if available
            attachments = submission.get('attachments', [])
            
            submission_text = ""
            for attachment in attachments:
                file_url = attachment['url']
                filename = os.path.join(download_folder, f"{user_id}_{attachment['filename']}")
                
                if download_submission_file(file_url, filename):
                    st.success(f"Downloaded {filename}")
                    
                    # Display the content of the downloaded file
                    if filename.endswith(".txt"):
                        with open(filename, "r") as f:
                            submission_text = f.read()
                    elif filename.endswith(".docx"):
                        doc = Document(filename)
                        submission_text = "\n".join([para.text for para in doc.paragraphs])
                
            # Collect data for the table, including the originality score
            table_data.append({
                "Student Name": user_name,
                "Submission": submission_text,
                "Originality Score (%)": originality_score
            })
        
        st.success("All submissions downloaded successfully.")
        
        # Display submissions in a table with the originality score column
        submissions_df = pd.DataFrame(table_data)
        st.dataframe(submissions_df)

        # Save submissions to a CSV file for later comparison
        submissions_df.to_csv("submissions_data.csv", index=False)

# Grading and Feedback Section
st.header("Grade and Provide Feedback on Submission")

# Proposed answers input
proposed_answer = st.text_area("Enter Proposed Answer:", height=100)

# Check if submissions were retrieved before displaying grading options
if 'submissions' in locals() and submissions:
    # Automatically generate grades and feedback for all submissions
    if proposed_answer:
        feedback_data = []

        # Load submissions from the saved CSV file
        submissions_df = pd.read_csv("submissions_data.csv")

        for index, row in submissions_df.iterrows():
            submission_text = row['Submission']
            user_name = row['Student Name']

            # Generate feedback from OpenAI
            feedback_output = generate_grading_feedback(submission_text, proposed_answer)
            if feedback_output:
                try:
                    # Split into grade and feedback
                    grade, feedback = feedback_output.split('\n', 1)  
                    
                    # Check if the grade is not valid and set to zero if there's no alignment
                    if "no alignment" in feedback.lower() or "zero" in feedback.lower():
                        grade = "0"
                except ValueError:
                    st.error(f"Failed to parse feedback for {user_name}: {feedback_output}")
                    grade, feedback = "N/A", "Feedback generation error."

                # Append feedback data
                feedback_data.append({
                    "Student Name": user_name,
                    "Submission": submission_text,
                    "Grade": grade,
                    "Feedback": feedback
                })

        # Display feedback in a table
        feedback_df = pd.DataFrame(feedback_data)
        st.dataframe(feedback_df)

# Add some color for better user experience
st.markdown(""" 
<style>
body {
    background-color: #f0f4f7; /* Light background color */
}
h1 {
    color: #2c3e50; /* Darker text for headings */
}
h2 {
    color: #34495e; /* Darker text for subheadings */
}
.stButton {
    background-color: #3498db; /* Button color */
    color: white; /* Button text color */
}
.stButton:hover {
    background-color: #2980b9; /* Button hover color */
}
</style>
""", unsafe_allow_html=True)
