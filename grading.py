import streamlit as st
import requests
import os
from docx import Document
import openai

# Canvas API token and base URL
API_TOKEN = 'your_canvas_api_token'  # Replace with your actual Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

# OpenAI API Key
OPENAI_API_KEY = 'your_openai_api_key'  # Replace with your OpenAI API key
openai.api_key = OPENAI_API_KEY

# Function to get submissions for an assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    submissions_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    
    response = requests.get(submissions_url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to retrieve submissions.")
        return []

# Function to download a submission file
def download_submission_file(file_url, filename):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(file_url, headers=headers)
    
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    else:
        return False

# Function to grade and provide feedback using OpenAI API
def grade_with_openai(submission_text, proposed_answer):
    prompt = f"Grade the following submission based on the provided answer:\n\nSubmission:\n{submission_text}\n\nProposed Answer:\n{proposed_answer}\n\nProvide a grade out of 100 and feedback on how closely it matches the proposed answer."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    feedback = response.choices[0].message['content']
    return feedback

# Function to submit grade and feedback to Canvas
def submit_grade_feedback(course_id, assignment_id, user_id, grade, feedback):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    grade_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    
    data = {
        "submission": {
            "posted_grade": grade,
            "comment": {
                "text_comment": feedback
            }
        }
    }
    
    response = requests.put(grade_url, headers=headers, json=data)
    return response.status_code == 200

# Streamlit UI
st.title("Canvas Assignment Submissions with Automated Grading and Feedback")

# Course and Assignment ID
course_id = 2850  # Replace with your course ID
assignment_id = 45964  # Replace with your assignment ID

# Fetch and display submissions
if st.button("Download All Submissions"):
    submissions = get_submissions(course_id, assignment_id)
    
    if submissions:
        download_folder = "submissions"
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        for submission in submissions:
            user_id = submission['user_id']
            attachments = submission.get('attachments', [])
            
            for attachment in attachments:
                file_url = attachment['url']
                filename = os.path.join(download_folder, f"{user_id}_{attachment['filename']}")
                
                if download_submission_file(file_url, filename):
                    st.write(f"Downloaded {filename}")
                else:
                    st.write(f"Failed to download file for user {user_id}")
        
        st.success("All submissions downloaded successfully.")
    else:
        st.warning("No submissions found for this assignment.")

# Input for the correct answer
st.header("Provide the Correct Answer")
proposed_answer = st.text_area("Enter the ideal answer for automatic grading:", "")

# Grading and Feedback Section
st.header("Grade, Provide Feedback, and Preview Submission")

if submissions and proposed_answer:
    for submission in submissions:
        user_id = submission['user_id']
        st.subheader(f"Submission for User {user_id}")
        
        # Find downloaded files
        download_folder = "submissions"
        user_files = [f for f in os.listdir(download_folder) if f.startswith(str(user_id))]

        for user_file in user_files:
            file_path = os.path.join(download_folder, user_file)
            if user_file.endswith(".docx"):
                # Read and display .docx content
                doc = Document(file_path)
                submission_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                st.text(submission_text)

                # Use OpenAI to grade and give feedback
                feedback = grade_with_openai(submission_text, proposed_answer)
                
                # Parse grade and feedback from OpenAI response
                grade = feedback.split("\n")[0].replace("Grade:", "").strip()
                detailed_feedback = "\n".join(feedback.split("\n")[1:])

                st.write(f"Generated Grade: {grade}")
                st.write("Feedback:")
                st.write(detailed_feedback)

                # Submit grade and feedback
                if st.button(f"Submit Grade and Feedback for User {user_id}", key=f"{user_id}_submit"):
                    if submit_grade_feedback(course_id, assignment_id, user_id, grade, detailed_feedback):
                        st.success(f"Grade and feedback submitted for User {user_id}")
                    else:
                        st.error(f"Failed to submit grade and feedback for User {user_id}")
            else:
                st.write(f"File type not supported for preview: {user_file}")
else:
    st.warning("Please download submissions and enter the proposed answer before grading.")
