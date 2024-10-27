import streamlit as st 
import requests
import os
import io  # Import io to handle in-memory byte streams
from docx import Document
import openai
import pandas as pd

# Canvas API token and base URL
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'  # Replace with your Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

# OpenAI API Key from Streamlit secrets
openai.api_key = st.secrets.get("openai", {}).get("api_key")

# Streamlit styling
st.set_page_config(page_title="Kepler College Grading System", page_icon="📚", layout="wide")
st.markdown("""
<style>
    .header {
        text-align: center;
        color: #4B0082;
        font-size: 30px;
        font-weight: bold;
    }
    .content {
        border: 2px solid #4B0082;
        padding: 20px;
        border-radius: 10px;
        background-color: #F3F4F6;
    }
    .submission-title {
        font-size: 24px;
        color: #4B0082;
    }
    .feedback-title {
        color: #FF4500;
        font-weight: bold;
    }
    .btn {
        background-color: #4B0082;
        color: white;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
    }
    .btn:hover {
        background-color: #5E2B91;
    }
</style>
""", unsafe_allow_html=True)

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
def download_submission_file(file_url):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(file_url, headers=headers)
    return response.content if response.status_code == 200 else None

# Function to generate grading and feedback using OpenAI
def generate_grading_feedback(submission_text, proposed_answer):
    if openai.api_key is None:
        st.error("OpenAI API key is missing. Please configure it to proceed.")
        return None, None

    prompt = (
        f"Evaluate the following student's submission against the proposed answer. "
        f"Assess alignment and rate it from 0 to 100. Provide feedback.\n\n"
        f"Submission: {submission_text}\n"
        f"Proposed Answer: {proposed_answer}\n\n"
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    feedback_content = response['choices'][0]['message']['content'].strip()
    lines = feedback_content.split("\n")
    grade = lines[0].split(": ")[1].strip() if "Grade:" in lines[0] else "0"
    feedback = "\n".join(lines[1:]).strip()
    return grade, feedback

# Function to submit feedback to Canvas
def submit_feedback_to_canvas(course_id, assignment_id, user_id, grade, feedback):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    submission_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    payload = {
        "submission": {"posted_grade": grade},
        "comment": {"text_comment": feedback}
    }
    response = requests.put(submission_url, headers=headers, json=payload)
    return response.status_code == 200

# Streamlit UI
st.image("header.png", use_column_width=True)  # Display header image
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

# Set Course and Assignment IDs
course_id = 2850  # Replace with your course ID
assignment_id = 45964  # Replace with your assignment ID

# Proposed Answer Input
proposed_answer = st.text_area("Proposed Answer for Evaluation:", height=100)
if not proposed_answer:
    st.warning("Please enter the proposed answer before downloading submissions.")

# Download submissions only if proposed answer is provided
if st.button("Download and Grade Submissions", key="download_btn") and proposed_answer:
    submissions = get_submissions(course_id, assignment_id)
    if submissions:
        feedback_data = []

        for submission in submissions:
            user_id = submission['user_id']
            user_name = submission['user']['name'] if 'user' in submission else f"User {user_id}"
            attachments = submission.get('attachments', [])
            submission_text = ""

            # Download submission file content
            for attachment in attachments:
                file_content = download_submission_file(attachment['url'])
                filename = attachment['filename']
                
                # Process file content based on file type
                if filename.endswith(".txt") and file_content:
                    submission_text = file_content.decode('utf-8')
                elif filename.endswith(".docx") and file_content:
                    doc = Document(io.BytesIO(file_content))
                    submission_text = "\n".join([para.text for para in doc.paragraphs])
            
            if submission_text:
                # Display submission and auto-generate grade and feedback
                st.markdown(f'<div class="content"><h2 class="submission-title">Submission by {user_name}</h2>', unsafe_allow_html=True)
                st.text_area("Submission Text", submission_text, height=200, disabled=True)
                
                grade = st.text_input(f"Grade for {user_name}", value=generate_grading_feedback(submission_text, proposed_answer)[0], key=f"grade_{user_id}")
                feedback = st.text_area(f"Feedback for {user_name}", value=generate_grading_feedback(submission_text, proposed_answer)[1], height=100, key=f"feedback_{user_id}")
                
                feedback_data.append({
                    "Student Name": user_name,
                    "Grade": grade,
                    "Feedback": feedback,
                    "User ID": user_id
                })
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Submit feedback to Canvas for each student when button is clicked
        if st.button("Submit Feedback to Canvas", key="submit_btn"):
            for entry in feedback_data:
                user_id = entry["User ID"]
                grade = entry["Grade"]
                feedback = entry["Feedback"]
                
                if submit_feedback_to_canvas(course_id, assignment_id, user_id, grade, feedback):
                    st.success(f"Feedback submitted for {entry['Student Name']}")
                else:
                    st.error(f"Failed to submit feedback for {entry['Student Name']}")
