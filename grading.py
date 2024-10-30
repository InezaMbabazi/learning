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

def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to retrieve submissions.")
        return []

def download_submission_file(file_url):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(file_url, headers=headers)
    return response.content if response.status_code == 200 else None

def display_excel_content(file_content):
    df = pd.read_excel(io.BytesIO(file_content))
    st.dataframe(df)

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
    return response.status_code in [200, 201]

def get_grading(student_submission, proposed_answer):
    grading_prompt = f"Evaluate the student's submission in relation to the proposed answer:\n\n"
    grading_prompt += f"**Proposed Answer**: {proposed_answer}\n\n"
    grading_prompt += f"**Student Submission**: {student_submission}\n\n"
    grading_prompt += "Provide constructive feedback, including a grade from 0 to 10."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    feedback = response['choices'][0]['message']['content']

    # Extract the grade from the feedback
    # Here we assume that the model returns something like "Grade: 8/10"
    try:
        calculated_grade = int(feedback.split("Grade:")[1].split("/")[0].strip())
    except (IndexError, ValueError):
        calculated_grade = 0  # Default to 0 if parsing fails

    # Ensure the grade is within 0-10 range
    calculated_grade = min(max(calculated_grade, 0), 10)

    # Align feedback with calculated grade
    if calculated_grade >= 7:
        feedback = f"Great job! Your submission is well done. Here are some minor suggestions: {feedback}"
    elif calculated_grade >= 4:
        feedback = f"Your submission is decent, but there are areas to improve: {feedback}"
    else:
        feedback = f"There are significant areas for improvement in your submission: {feedback}"

    return feedback, calculated_grade

# Streamlit UI
st.image("header.png", use_column_width=True)
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

course_id = st.number_input("Enter Course ID:", min_value=1, step=1, value=2906)
assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1, value=47134)

proposed_answer = st.text_area("Enter the proposed answer for evaluation:", "")

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

                    feedback, calculated_grade = get_grading(submission_text, proposed_answer)

                    # Update feedback to address the student directly
                    feedback_message = f"Dear {user_name},\n\n{feedback}\n\nPlease revise accordingly."
                    
                    feedback_key = f"{user_id}_{assignment_id}"

                    # Store feedback and grade in session state
                    st.session_state.feedback_data[feedback_key] = {
                        "Student Name": user_name,
                        "User ID": user_id,
                        "Feedback": feedback_message,
                        "Grade": calculated_grade
                    }

                    # Display feedback and grade directly under the submission
                    st.markdown(f'<div class="feedback-title">Feedback:</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="feedback">{feedback_message}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="feedback-title">Grade:</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="feedback">{calculated_grade}</div>', unsafe_allow_html=True)

# Submit feedback
if st.button("Submit Feedback to Canvas"):
    if not st.session_state.feedback_data:
        st.warning("No feedback available to submit.")
    else:
        for key, entry in st.session_state.feedback_data.items():
            # Retrieve the edited feedback and grade from the session state
            success = submit_feedback(course_id, assignment_id, entry['User ID'], entry['Feedback'], entry['Grade'])
            if success:
                st.success(f"Successfully submitted feedback for {entry['Student Name']} (User ID: {entry['User ID']}).")
            else:
                st.error(f"Failed to submit feedback for {entry['Student Name']} (User ID: {entry['User ID']}).")

# Display previous feedback
st.subheader("Previous Feedback:")
if 'feedback_data' in st.session_state and st.session_state.feedback_data:
    for key, feedback in st.session_state.feedback_data.items():
        st.markdown(f"**{feedback['Student Name']} (User ID: {feedback['User ID']}):**")
        st.markdown(f"**Grade:** {feedback['Grade']}")
        st.markdown(f"**Feedback:** {feedback['Feedback']}")
else:
    st.info("No feedback has been generated yet.")
