import streamlit as st
import requests
import os
import io
from docx import Document
import openai
import pandas as pd

# Canvas API token and base URL
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'
BASE_URL = 'https://kepler.instructure.com/api/v1'

# OpenAI API Key
openai.api_key = st.secrets["openai"]["api_key"]

st.set_page_config(page_title="Kepler College Grading System", page_icon="📚", layout="wide")

# Custom CSS for styling
st.markdown(
    """
    <style>
    .main {
        background-color: #f7f9fc;
        color: #333;
    }
    h1 {
        color: #2a9d8f;
        text-align: center;
    }
    .stButton>button {
        background-color: #e76f51;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #2a9d8f;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions", headers=headers)
    return response.json() if response.status_code == 200 else []

def download_submission_file(file_url):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(file_url, headers=headers)
    return response.content if response.status_code == 200 else None

def display_excel_content(file_content):
    df = pd.read_excel(io.BytesIO(file_content))
    st.dataframe(df)

def submit_feedback(course_id, assignment_id, user_id, feedback, grade):
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    payload = {"comment": {"text_comment": feedback}, "submission": {"posted_grade": grade}}
    url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code in [200, 201]

def get_grading(student_submission, proposed_answer):
    grading_prompt = f"Evaluate the student's submission:\n\n**Proposed Answer**: {proposed_answer}\n\n**Student Submission**: {student_submission}"
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": grading_prompt}])
    feedback = response['choices'][0]['message']['content']
    return feedback

def calculate_grade(submission_text, proposed_answer):
    base_grade = 5
    keywords = ["important", "necessary", "critical"]

    if len(submission_text) > 500:
        base_grade += 2
    elif len(submission_text) < 200:
        base_grade -= 1

    for keyword in keywords:
        if keyword in submission_text.lower():
            base_grade += 1

    return min(max(base_grade, 0), 10)

# Streamlit UI
st.markdown('<h1>Kepler College Grading System</h1>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    course_id = st.number_input("Enter Course ID:", min_value=1, step=1, value=2906)
    assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1, value=47134)
with col2:
    proposed_answer = st.text_area("Enter the proposed answer for evaluation:", "", height=200)

if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = {}

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
                if attachment['filename'].endswith(".txt") and file_content:
                    submission_text = file_content.decode('utf-8')

            if submission_text:
                feedback = get_grading(submission_text, proposed_answer)
                calculated_grade = calculate_grade(submission_text, proposed_answer)

                feedback_key = f"{user_id}_{assignment_id}"
                if feedback_key not in st.session_state.feedback_data:
                    st.session_state.feedback_data[feedback_key] = {
                        "Student Name": user_name,
                        "User ID": user_id,
                        "Feedback": feedback,
                        "Grade": calculated_grade
                    }

# Submit feedback
if st.button("Submit Feedback to Canvas"):
    for key, entry in st.session_state.feedback_data.items():
        success = submit_feedback(course_id, assignment_id, entry['User ID'], entry['Feedback'], entry['Grade'])
        if success:
            st.success(f"Successfully submitted feedback for {entry['Student Name']} (User ID: {entry['User ID']}).")
        else:
            st.error(f"Failed to submit feedback for {entry['Student Name']} (User ID: {entry['User ID']}).")

# Display previous feedback with editable text areas
st.subheader("Previous Feedback:")
for key, feedback in st.session_state.feedback_data.items():
    st.write(f"Student: {feedback['Student Name']} (User ID: {feedback['User ID']})")
    
    # Editable text area for feedback
    feedback['Feedback'] = st.text_area(
        f"Edit Feedback for {feedback['Student Name']} (User ID: {feedback['User ID']})",
        value=feedback['Feedback'],
        key=f"{key}_feedback"
    )
    feedback['Grade'] = st.number_input(
        f"Grade for {feedback['Student Name']} (User ID: {feedback['User ID']})",
        min_value=0, max_value=10, value=feedback['Grade'],
        key=f"{key}_grade"
    )
    st.markdown("---")
