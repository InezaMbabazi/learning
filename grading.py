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

# Function to fetch submissions from Canvas
def get_submissions(course_id, assignment_id):
    url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error fetching submissions: " + response.text)
        return []

# Function to download submission file
def download_submission_file(url):
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.get(url, headers=headers)
    return response.content if response.status_code == 200 else None

# Function to generate feedback using OpenAI
def generate_feedback(proposed_answer):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Provide feedback on this answer: {proposed_answer}"}
        ]
    )
    return response['choices'][0]['message']['content'] if response['choices'] else "No feedback available."

# Function to calculate grade based on submission text
def calculate_grade(submission_text):
    # Placeholder for a grading logic, e.g., keyword scoring, length of response, etc.
    if len(submission_text) < 100:
        return 5.0  # Low score for short submissions
    elif len(submission_text) < 300:
        return 7.5  # Medium score for moderate length submissions
    else:
        return 10.0  # Full score for long submissions

# Function to submit feedback to Canvas
def submit_feedback(course_id, assignment_id, user_id, feedback, grade):
    url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    data = {
        'submission[comment][text_comment]': feedback,
        'submission[grade]': grade
    }
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return True, "Feedback submitted successfully!"
    else:
        return False, "Error submitting feedback: " + response.text

# Streamlit styling and UI
st.set_page_config(page_title="Kepler College Grading System", page_icon="📚", layout="wide")
st.markdown("""
<style>
    .header { text-align: center; color: #4B0082; font-size: 30px; font-weight: bold; }
    .content { border: 2px solid #4B0082; padding: 20px; border-radius: 10px; background-color: #F3F4F6; }
</style>
""", unsafe_allow_html=True)

# Streamlit UI
st.image("header.png", use_column_width=True)
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

# Input fields for course ID and assignment ID
st.sidebar.header("Configuration")
course_id = st.sidebar.number_input("Enter Course ID:", min_value=1, step=1, value=2906)
assignment_id = st.sidebar.number_input("Enter Assignment ID:", min_value=1, step=1, value=47134)

# Proposed answer input
proposed_answer = st.text_area("Proposed Answer for Evaluation:", height=100)

# Initialize session state for feedback if not already done
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []

# Button to fetch submissions and provide feedback
if st.button("Download and Grade Submissions"):
    with st.spinner("Fetching submissions..."):
        submissions = get_submissions(course_id, assignment_id)
    if submissions:
        for submission in submissions:
            user_id = submission['user_id']
            submission_id = submission['id']
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
                
                if submission_text:
                    st.markdown(f"**Submission by {user_name} (User ID: {user_id}, Submission ID: {submission_id})**")
                    st.text(submission_text)

                    # Automatically generate feedback and grade
                    feedback = generate_feedback(submission_text)
                    grade = calculate_grade(submission_text)

                    # Display generated feedback and grade
                    st.markdown(f"**Generated Feedback:** {feedback}")
                    st.markdown(f"**Generated Grade:** {grade:.1f}")

                    # Save feedback data
                    feedback_entry = {
                        "Student Name": user_name,
                        "Feedback": feedback,
                        "User ID": user_id,
                        "Submission ID": submission_id,
                        "Grade": grade
                    }
                    st.session_state.feedback_data.append(feedback_entry)

# Submit feedback and grades
if st.button("Submit Feedback to Canvas"):
    if not st.session_state.feedback_data:
        st.warning("No feedback available to submit.")
    else:
        with st.spinner("Submitting feedback..."):
            for entry in st.session_state.feedback_data:
                success, message = submit_feedback(course_id, assignment_id, entry["User ID"], entry["Feedback"], entry["Grade"])
                if success:
                    st.success(message)
                else:
                    st.error(message)

# Display feedback data
if st.session_state.feedback_data:
    st.subheader("Feedback Data")
    for feedback_entry in st.session_state.feedback_data:
        st.markdown(f"**{feedback_entry['Student Name']} (User ID: {feedback_entry['User ID']}, Submission ID: {feedback_entry['Submission ID']})**")
        st.markdown(f"Feedback: {feedback_entry['Feedback']}")
        st.markdown(f"Grade: {feedback_entry['Grade']:.1f}")
