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
    .header { text-align: center; color: #4B0082; font-size: 30px; font-weight: bold; }
    .content { border: 2px solid #4B0082; padding: 20px; border-radius: 10px; background-color: #F3F4F6; }
    .submission-title { font-size: 24px; color: #4B0082; }
    .submission-text { font-size: 20px; border: 2px solid #4B0082; padding: 10px; background-color: #E6E6FA; border-radius: 10px; color: #333; font-weight: bold; }
    .feedback-title { color: #FF4500; font-weight: bold; }
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

# Function to generate grading and feedback using OpenAI
def generate_grading_feedback(submission_text, proposed_answer):
    if openai.api_key is None:
        st.error("OpenAI API key is missing.")
        return None, None

    prompt = (
        f"Evaluate the following student's submission against the proposed answer. "
        f"Provide feedback and a grade between 0 and 100.\n\n"
        f"Submission: {submission_text}\n"
        f"Proposed Answer: {proposed_answer}\n\n"
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    feedback_content = response['choices'][0]['message']['content'].strip()
    
    grade = None
    feedback = feedback_content
    if "Grade:" in feedback_content:
        try:
            grade_line = feedback_content.splitlines()[0]
            grade = int(grade_line.split(": ")[1])
            feedback = "\n".join(feedback_content.splitlines()[1:]).strip()
        except (IndexError, ValueError):
            grade = "Not Assigned"
    
    return grade, feedback

# Function to submit feedback to Canvas
# Function to submit feedback to Canvas
def submit_feedback_to_canvas(course_id, assignment_id, user_id, grade, feedback):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    submission_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"

    # Prepare payload with both grade and feedback (comment)
    payload = {
        "submission": {
            "posted_grade": grade if grade else None  # Assign grade if available
        },
        "comment": {
            "text_comment": feedback  # Add feedback as a comment
        }
    }

    # Remove 'submission' field if no grade is assigned to avoid payload issues
    if not grade:
        payload.pop("submission")

    response = requests.put(submission_url, headers=headers, json=payload)
    
    # Check response and provide feedback in Streamlit for debugging
    if response.status_code == 200:
        st.success(f"Feedback successfully submitted for user ID {user_id}.")
        return True
    else:
        st.error(f"Failed to submit feedback for user ID {user_id}. Status code: {response.status_code}")
        st.error(f"Response: {response.text}")
        return False
