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
        grading_prompt += "Provide detailed feedback and suggestions for improvement."
    elif content_type == "Programming (Code)":
        grading_prompt += f"**Proposed Code**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Code Submission**: {student_submission}\n\n"
        grading_prompt += "Check logic, efficiency, correctness, and provide feedback and suggestions for improvement."
    else:
        grading_prompt += f"**Proposed Answer**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Submission**: {student_submission}\n\n"
        grading_prompt += "Provide detailed feedback and suggestions for improvement."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    
    feedback = response['choices'][0]['message']['content']
    return feedback

# Function to calculate grade based on feedback content
def calculate_grade(feedback):
    # Initialize grade to 0
    grade = 0
    # Define grading keywords
    keywords_positive = ["excellent", "good", "well done", "strong", "impressive"]
    keywords_negative = ["poor", "needs improvement", "weak", "inadequate", "lacks"]

    # Check for positive feedback keywords
    for keyword in keywords_positive:
        if keyword in feedback.lower():
            grade += 2  # Increase grade for positive feedback

    # Check for negative feedback keywords
    for keyword in keywords_negative:
        if keyword in feedback.lower():
            grade -= 1  # Decrease grade for negative feedback

    # Ensure grade is within 0 to 10
    return min(max(grade, 0), 10)

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
                    feedback = get_grading(submission_text, proposed_answer, "Text")

                    # Calculate grade based on feedback content
                    calculated_grade = calculate_grade(feedback)

                    # Input for feedback with the full feedback text
                    feedback_input = st.text_area(f"Feedback for {user_name}", value=feedback, height=100, key=f"feedback_{user_id}")

                    # Update session state
                    feedback_entry = {
                        "Student Name": user_name,
                        "Feedback": feedback_input,
                        "User ID": user_id,
                        "Grade": calculated_grade  # Store the calculated grade
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

# Display all feedbacks given with user's name and their obtained grade
if st.session_state.feedback_data:
    st.markdown("<h2>Feedback Summary</h2>", unsafe_allow_html=True)
    for entry in st.session_state.feedback_data:
        st.markdown(f'<div class="feedback"><strong>{entry["Student Name"]}</strong> (User ID: {entry["User ID"]})<br>Feedback: {entry["Feedback"]}<br><strong>Grade for User:</strong> {entry["Grade"]}</div>', unsafe_allow_html=True)
