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
            "posted_grade": grade
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
    grading_prompt = f"Evaluate the student's submission in relation to the proposed answer:\n\n"
    
    if content_type == "Math (LaTeX)":
        grading_prompt += f"**Proposed Answer (LaTeX)**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Submission (LaTeX)**: {student_submission}\n\n"
        grading_prompt += "Provide feedback on correctness, grade out of 10, and suggest improvements regarding how closely it aligns with the proposed answer."
    elif content_type == "Programming (Code)":
        grading_prompt += f"**Proposed Code**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Code Submission**: {student_submission}\n\n"
        grading_prompt += "Check logic, efficiency, correctness, and grade out of 10, focusing on how well the submission follows the proposed code."
    else:
        grading_prompt += f"**Proposed Answer**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Submission**: {student_submission}\n\n"
        grading_prompt += "Provide detailed feedback, grade out of 10, and suggest improvements while clearly referencing the proposed answer."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    
    feedback = response['choices'][0]['message']['content']
    return feedback

# Function to calculate grade automatically
def calculate_grade(submission_text):
    keywords = ["important", "necessary", "critical"]
    base_grade = 5
    if len(submission_text) > 500:
        base_grade += 2
    elif len(submission_text) < 200:
        base_grade -= 1
    for keyword in keywords:
        if keyword in submission_text.lower():
            base_grade += 1
    return min(max(base_grade, 0), 10)

# Streamlit UI
st.image("header.png", use_column_width=True)
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

course_id = st.number_input("Enter Course ID:", min_value=1, step=1, value=2906)
assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1, value=47134)

# Proposed answer input
proposed_answer = st.text_area("Enter the proposed answer for evaluation:", "")

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

                    # Generate feedback specific to the student's submission, using the proposed answer
                    feedback_and_grade = get_grading(submission_text, proposed_answer, "Text")

                    # Attempt to extract a grade from the feedback; set to 0 if extraction fails
                    try:
                        # Convert the last word to float if it's a grade
                        extracted_grade = float(feedback_and_grade.split()[-1])
                    except ValueError:
                        # Default to 0 if the last word isn't a valid grade
                        extracted_grade = 0.0

                    # Input for grade with the extracted grade or 0.0 as the default
                    grade_input = st.number_input(
                        f"Grade for {user_name} (0-10)", 
                        value=extracted_grade, 
                        min_value=0.0, 
                        max_value=10.0, 
                        step=0.1, 
                        key=f"grade_{user_id}"
                    )

                    # Input for feedback with the full feedback_and_grade text as default
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
            success, message = submit_feedback(course_id, assignment_id, entry['User ID'], entry['Feedback'], entry['Grade'])
            st.success(message if success else f"Error: {message}")

# Display previous feedback
st.subheader("Previous Feedback:")
for feedback in st.session_state.feedback_data:
    st.write(f"Student: {feedback['Student Name']}, Grade: {feedback['Grade']}, Feedback: {feedback['Feedback']}")
