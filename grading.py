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

# Function definitions (as before)...

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

if st.button("Download and Grade Submissions") and proposed_answer:
    with st.spinner("Fetching submissions..."):
        submissions = get_submissions(course_id, assignment_id)
    if submissions:
        for submission in submissions:
            user_id = submission['user_id']  # Fetch user ID
            submission_id = submission['id']  # Fetch submission ID
            user_name = submission.get('user', {}).get('name', f"User {user_id}")
            attachments = submission.get('attachments', [])
            submission_text = ""

            # Fetch existing feedback
            existing_feedback = submission.get('comment', {}).get('text_comment', "")

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

                    # Display the existing feedback
                    st.markdown(f"**Feedback for {user_name}:** {existing_feedback}")

                    # Generate automated feedback based on the proposed answer
                    generated_feedback = generate_feedback(proposed_answer)

                    # Automatically calculate grade
                    auto_grade = calculate_grade(submission_text)

                    # Input for grade (scale out of 10)
                    grade_input = st.number_input(
                        f"Grade for {user_name} (0-10)", 
                        value=float(auto_grade),  # Ensure the default grade is a float
                        min_value=0.0, 
                        max_value=10.0, 
                        step=0.1, 
                        key=f"grade_{user_id}"
                    )

                    # Create unique keys for each user
                    feedback_input = st.text_area(f"Feedback for {user_name}", value=generated_feedback, height=100, key=f"feedback_{user_id}")

                    # Update session state to maintain user feedback
                    feedback_entry = {
                        "Student Name": user_name,
                        "Feedback": feedback_input,
                        "User ID": user_id,
                        "Submission ID": submission_id,
                        "Grade": grade_input  # Store the grade in the feedback entry
                    }
                    # Update the feedback data in session state
                    for i, entry in enumerate(st.session_state.feedback_data):
                        if entry["User ID"] == user_id:
                            st.session_state.feedback_data[i] = feedback_entry
                            break
                    else:
                        st.session_state.feedback_data.append(feedback_entry)

# Button to submit feedback and grades
if st.button("Submit Feedback to Canvas"):
    if not st.session_state.feedback_data:
        st.warning("No feedback available to submit.")
    else:
        with st.spinner("Submitting feedback..."):
            for entry in st.session_state.feedback_data:
                success, message = submit_feedback(course_id, assignment_id, entry["User ID"], entry["Feedback"], entry["Grade"])
                st.success(message) if success else st.error(message)

# Display the session state feedback data
if st.session_state.feedback_data:
    st.subheader("Feedback Data")
    for feedback_entry in st.session_state.feedback_data:
        st.markdown(f"**{feedback_entry['Student Name']} (User ID: {feedback_entry['User ID']}, Submission ID: {feedback_entry['Submission ID']})**")
        st.markdown(f"Feedback: {feedback_entry['Feedback']}")
        st.markdown(f"Grade: {feedback_entry['Grade']}")
