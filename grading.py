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
openai.api_key = st.secrets["openai"]["api_key"]

# Streamlit styling
st.set_page_config(page_title="Kepler College Grading System", page_icon="📚", layout="wide")
st.markdown("""
<style>
    .header { text-align: center; color: #4B0082; font-size: 30px; font-weight: bold; }
    .content { border: 2px solid #4B0082; padding: 20px; border-radius: 10px; background-color: #F3F4F6; }
    .submission-title { font-size: 24px; color: #4B0082; }
    .submission-text { font-size: 20px; border: 2px solid #4B0082; padding: 10px; background-color: #E6E6FA; border-radius: 10px; color: #333; font-weight: bold; }
    .feedback-title { color: #FF4500; font-weight: bold; }
    .feedback { border: 2px solid #4B0082; padding: 10px; border-radius: 10px; background-color: #E6FFE6; color: #333; }
</style>
""", unsafe_allow_html=True)

# Function to get submissions for an assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions", headers=headers)
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

# Function to display Excel content
def display_excel_content(file_content):
    df = pd.read_excel(io.BytesIO(file_content))
    st.dataframe(df)

# Function to submit feedback to Canvas
def submit_feedback(course_id, assignment_id, user_id, feedback, grade):
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "comment": {
            "text_comment": feedback
        },
        "submission": {
            "posted_grade": grade  # Include the grade in the payload
        }
    }
    url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        return True, f"Successfully submitted feedback for user ID {user_id}."
    else:
        return False, f"Failed to submit feedback for user ID {user_id}. Status code: {response.status_code} Response: {response.text}"

# Function to get grading from OpenAI based on student submissions and proposed answers
def get_grading(student_submission, proposed_answer, content_type):
    grading_prompt = (
        "Please evaluate the student's submission in comparison to the provided answer.\n"
        "Consider the correctness, relevance, completeness, and suggest specific improvements.\n\n"
        f"**Proposed Answer**: {proposed_answer}\n\n"
        f"**Student Submission**: {student_submission}\n\n"
    )
    if content_type == "Math (LaTeX)":
        grading_prompt += (
            "This is a LaTeX-based mathematical answer. Evaluate accuracy in mathematical logic, symbols, "
            "and steps in comparison to the proposed solution. Provide a grade out of 10 and specific feedback."
        )
    elif content_type == "Programming (Code)":
        grading_prompt += (
            "This is a code-based response. Check for logic, efficiency, syntax, and correctness compared to "
            "the proposed solution. Provide a grade out of 10 and feedback on improvements."
        )
    else:
        grading_prompt += (
            "Evaluate the student's answer based on its accuracy, completeness, and relevance compared to the proposed answer. "
            "Provide a grade out of 10 and detailed feedback on improvements."
        )
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    
    feedback = response['choices'][0]['message']['content']
    return feedback

# Streamlit UI
st.image("header.png", use_column_width=True)
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

course_id = st.number_input("Enter Course ID:", min_value=1, step=1, value=2906)
assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1, value=47134)

# Proposed answer and content type input
proposed_answer = st.text_area("Enter the proposed answer for evaluation:", "")
content_type = st.selectbox("Select the content type for grading:", ["General", "Math (LaTeX)", "Programming (Code)"])

# Initialize session state for feedback
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []

if st.button("Download and Grade Submissions"):
    submissions = get_submissions(course_id, assignment_id)
    if submissions:
        for submission in submissions:
            user_id = submission['user_id']
            user_name = submission.get('user', {}).get('name', f"User {user_id}")
            attachments = submission.get('attachments', [])
            submission_text = ""

            for attachment in attachments:
                file_content = download_submission_file(attachment['url'])
                filename = attachment['filename']
                if filename.endswith(".txt") and file_content:
                    submission_text = file_content.decode('utf-8')
                elif filename.endswith(".docx") and file_content:
                    doc = Document(io.BytesIO(file_content))
                    submission_text = "\n".join([para.text for para in doc.paragraphs])
                elif filename.endswith(".xlsx") and file_content:
                    st.markdown(f'<div class="submission-title">Excel Submission from {user_name}</div>', unsafe_allow_html=True)
                    display_excel_content(file_content)
                    continue

                if submission_text:
                    st.markdown(f'<div class="submission-title">Submission by {user_name} (User ID: {user_id})</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="submission-text">{submission_text}</div>', unsafe_allow_html=True)

                    # Generate grading and feedback based on the content type
                    feedback_and_grade = get_grading(submission_text, proposed_answer, content_type)
                    
                    # Display feedback and grade
                    st.markdown(f'<div class="feedback-title">Feedback:</div><div class="feedback">{feedback_and_grade}</div>', unsafe_allow_html=True)

                    # Input for grade
                    grade_input = st.number_input(
                        f"Grade for {user_name} (0-10)", 
                        value=float(feedback_and_grade.split()[-1]), 
                        min_value=0.0, 
                        max_value=10.0, 
                        step=0.1, 
                        key=f"grade_{user_id}"
                    )

                    # Input for feedback
                    feedback_input = st.text_area(f"Feedback for {user_name}", value=feedback_and_grade, height=100, key=f"feedback_{user_id}")

                    # Update session state
                    feedback_entry = {
                        "Student Name": user_name,
                        "Feedback": feedback_input,
                        "User ID": user_id,
                        "Grade": grade_input
                    }
                    st.session_state.feedback_data.append(feedback_entry)

# Button to submit feedback to Canvas
if st.button("Submit Feedback to Canvas"):
    if not st.session_state.feedback_data:
        st.warning("No feedback available to submit.")
    else:
        for entry in st.session_state.feedback_data:
            success, message = submit_feedback(course_id, assignment_id, entry["User ID"], entry["Feedback"], entry["Grade"])
            if success:
                st.success(message)
            else:
                st.error(message)
