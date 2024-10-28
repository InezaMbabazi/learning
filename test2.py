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

# Streamlit styling
st.set_page_config(page_title="Kepler College Grading System", page_icon="📚", layout="wide")
st.markdown("""
<style>
    .header { text-align: center; color: #4B0082; font-size: 30px; font-weight: bold; }
    .content { border: 2px solid #4B0082; padding: 20px; border-radius: 10px; background-color: #F3F4F6; }
    .submission-title { font-size: 24px; color: #4B0082; }
    .submission-text { font-size: 20px; border: 2px solid #4B0082; padding: 10px; background-color: #E6E6FA; border-radius: 10px; color: #333; font-weight: bold; }
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

# Function to submit grade to Canvas
def submit_grade(course_id, assignment_id, user_id, grade):
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "submission": {
            "posted_grade": grade
        }
    }

    # Construct the URL using the provided IDs
    url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        return True, f"Successfully submitted grade for user ID {user_id}."
    else:
        return False, f"Failed to submit grade for user ID {user_id}. Status code: {response.status_code} Response: {response.text}"

# Function to calculate grade (modify this logic as needed)
def calculate_grade(submission_text):
    # Simple grading logic: count words as an example
    word_count = len(submission_text.split())
    grade = min(max(word_count // 10, 0), 100)  # Scale to 0-100 for example
    return grade

# Streamlit UI
st.image("header.png", use_column_width=True)
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

course_id = 2906  # Replace with your course ID
assignment_id = 47134  # Replace with your assignment ID

proposed_answer = st.text_area("Proposed Answer for Evaluation:", height=100)

# Initialize session state for grades if not already done
if 'grade_data' not in st.session_state:
    st.session_state.grade_data = []

if st.button("Download and Grade Submissions") and proposed_answer:
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
                elif filename.endswith(".xlsx") and file_content:
                    st.markdown(f'<div class="submission-title">Excel Submission from {user_name}</div>', unsafe_allow_html=True)
                    display_excel_content(file_content)
                    continue

                if submission_text:
                    st.markdown(f'<div class="submission-title">Submission by {user_name} (User ID: {user_id}, Submission ID: {submission_id})</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="submission-text">{submission_text}</div>', unsafe_allow_html=True)

                    # Calculate grade based on the submission
                    grade = calculate_grade(submission_text)
                    st.markdown(f"**Calculated Grade for {user_name}:** {grade}")

                    # Prepare to submit the grade
                    grade_entry = {
                        "Student Name": user_name,
                        "Grade": grade,
                        "User ID": user_id,
                        "Submission ID": submission_id
                    }
                    st.session_state.grade_data.append(grade_entry)

# Button to submit grades
if st.button("Submit Grades to Canvas"):
    if not st.session_state.grade_data:
        st.warning("No grade data to submit.")
    else:
        submission_results = []
        for entry in st.session_state.grade_data:
            success, message = submit_grade(course_id, assignment_id, entry["User ID"], entry["Grade"])
            submission_results.append((entry["Student Name"], success, message))

        for student_name, success, message in submission_results:
            if success:
                st.success(f"{message} - {student_name}")
            else:
                st.error(f"{message} - {student_name}")
