import streamlit as st 
import requests
import os
import io
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
    .submission-text {
        font-size: 20px;
        border: 2px solid #4B0082;
        padding: 10px;
        background-color: #E6E6FA;
        border-radius: 10px;
        color: #333;
        font-weight: bold;
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

# Function to extract and display Excel content in columns
def display_excel_content(file_content):
    df = pd.read_excel(io.BytesIO(file_content))
    st.dataframe(df)  # Display as a structured table in columns

# Function to generate grading and feedback using OpenAI
def generate_grading_feedback(submission_text, proposed_answer):
    if openai.api_key is None:
        st.error("OpenAI API key is missing. Please configure it to proceed.")
        return None, None

    prompt = (
        f"Evaluate the following student's submission against the proposed answer. "
        f"Assess alignment and rate it from 0 to 100. If there is no alignment, respond that there is no alignment and don't give a grade.\n\n"
        f"Submission: {submission_text}\n"
        f"Proposed Answer: {proposed_answer}\n\n"
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    feedback_content = response['choices'][0]['message']['content'].strip()
    
    if "no alignment" in feedback_content.lower():
        grade = None  # No grade if no alignment
        feedback = "No alignment with the proposed answer."
    else:
        lines = feedback_content.split("\n")
        grade = lines[0].split(": ")[1].strip() if "Grade:" in lines[0] else "Not Assigned"
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
        "submission": {"posted_grade": grade} if grade else {},
        "comment": {"text_comment": feedback}
    }
    response = requests.put(submission_url, headers=headers, json=payload)
    return response.status_code == 200

# Streamlit UI
st.image("header.png", use_column_width=True)  # Display header image
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

# User selects file source
source = st.radio("Choose file source:", ("Canvas", "Upload from Local"))

if source == "Upload from Local":
    uploaded_file = st.file_uploader("Upload student submission file")
    if uploaded_file:
        file_content = uploaded_file.read()
        filename = uploaded_file.name
        
        # Process based on file type
        if filename.endswith(".txt"):
            submission_text = file_content.decode('utf-8')
            st.text_area("Text Submission", submission_text, height=200)
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(file_content))
            submission_text = "\n".join([para.text for para in doc.paragraphs])
            st.text_area("Word Document Submission", submission_text, height=200)
        elif filename.endswith(".xlsx"):
            st.markdown(f'<div class="submission-title">Excel Submission</div>', unsafe_allow_html=True)
            display_excel_content(file_content)
        
        # Process grading if submission is text-based
        if submission_text:
            proposed_answer = st.text_area("Enter Proposed Answer for Evaluation:", height=100)
            if proposed_answer:
                grade, feedback = generate_grading_feedback(submission_text, proposed_answer)
                st.write("Grade:", grade if grade else "Not Assigned")
                st.write("Feedback:", feedback)
else:
    # Download from Canvas
    course_id = 2850  # Replace with your course ID
    assignment_id = 45964  # Replace with your assignment ID
    submissions = get_submissions(course_id, assignment_id)
    if submissions:
        proposed_answer = st.text_area("Enter Proposed Answer for Evaluation:", height=100)
        feedback_data = []

        if proposed_answer:
            for submission in submissions:
                user_id = submission['user_id']
                user_name = submission['user']['name'] if 'user' in submission else f"User {user_id}"
                attachments = submission.get('attachments', [])
                
                # Process each attachment
                for attachment in attachments:
                    file_content = download_submission_file(attachment['url'])
                    filename = attachment['filename']
                    submission_text = ""

                    if filename.endswith(".txt") and file_content:
                        submission_text = file_content.decode('utf-8')
                    elif filename.endswith(".docx") and file_content:
                        doc = Document(io.BytesIO(file_content))
                        submission_text = "\n".join([para.text for para in doc.paragraphs])
                    elif filename.endswith(".xlsx") and file_content:
                        st.markdown(f'<div class="submission-title">Excel Submission from {user_name}</div>', unsafe_allow_html=True)
                        display_excel_content(file_content)
                    
                    if submission_text:
                        grade, feedback = generate_grading_feedback(submission_text, proposed_answer)
                        st.write(f"**{user_name}** - Grade: {grade if grade else 'Not Assigned'}, Feedback: {feedback}")
                        feedback_data.append((user_id, grade, feedback))

            # Option to submit all feedback at once
            if st.button("Submit All Feedback to Canvas"):
                for user_id, grade, feedback in feedback_data:
                    submit_feedback_to_canvas(course_id, assignment_id, user_id, grade, feedback)
                    st.success(f"Feedback submitted for User {user_id}")
