import streamlit as st
import requests
import os
import io
from docx import Document
import openai
import pandas as pd
from textblob import TextBlob  # Import TextBlob for sentiment analysis

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

def get_grading(submission_text, proposed_answer):
    grading_prompt = f"Evaluate the submission in relation to the proposed answer and provide constructive feedback.\n\n"
    grading_prompt += f"**Proposed Answer**: {proposed_answer}\n\n"
    grading_prompt += f"**Submission**: {submission_text}\n\n"
    grading_prompt += "Provide feedback in a direct manner, addressing the user as 'you' and specifying what should be improved."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    feedback = response['choices'][0]['message']['content']
    return feedback

def calculate_grade(submission_text, proposed_answer):
    base_grade = 5  # Start with a base grade
    
    # Check for conceptual alignment with critical and ethical thinking
    if "critical thinking" in submission_text.lower() and "ethical thinking" in submission_text.lower():
        base_grade += 2
    
    # Check for real-life examples
    if "example" in submission_text.lower() or any(keyword in submission_text.lower() for keyword in ["class", "workplace", "alcoholism"]):
        base_grade += 1

    # Check for structured, step-by-step explanation
    steps = ["observe", "wonder", "gather", "analyze", "synthesize", "reflect", "decide"]
    if all(step in submission_text.lower() for step in steps):
        base_grade += 1

    # Adjust for length to discourage overly brief responses
    if len(submission_text) < 100:
        base_grade -= 2
    elif len(submission_text) > 500:
        base_grade += 1  # Reward for depth if length exceeds 500

    # Check overall relevance to proposed answer
    if proposed_answer.lower() in submission_text.lower():
        base_grade += 1
    else:
        base_grade -= 1

    # Ensure the grade is within 0-10 range
    return min(max(base_grade, 0), 10)

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

                    feedback = get_grading(submission_text, proposed_answer)

                    # Address the user directly in the feedback
                    feedback_message = f"You need to work on the following:\n\n{feedback}"
                    
                    calculated_grade = calculate_grade(submission_text, proposed_answer)

                    feedback_key = f"{user_id}_{assignment_id}"

                    if feedback_key not in st.session_state.feedback_data:
                        st.session_state.feedback_data[feedback_key] = {
                            "Name": user_name,
                            "User ID": user_id,
                            "Feedback": feedback_message,
                            "Grade": calculated_grade
                        }

# Submit feedback
if st.button("Submit Feedback to Canvas"):
    if not st.session_state.feedback_data:
        st.warning("No feedback available to submit.")
    else:
        for key, entry in st.session_state.feedback_data.items():
            success = submit_feedback(course_id, assignment_id, entry['User ID'], entry['Feedback'], entry['Grade'])
            if success:
                st.success(f"Successfully submitted feedback for {entry['Name']} (User ID: {entry['User ID']}).")
            else:
                st.error(f"Failed to submit feedback for {entry['Name']} (User ID: {entry['User ID']}).")

# Display previous feedback with editable fields
st.subheader("Previous Feedback:")
if 'feedback_data' in st.session_state and st.session_state.feedback_data:
    for key, feedback in st.session_state.feedback_data.items():
        st.write(f"Name: {feedback['Name']} (User ID: {feedback['User ID']})")

        # Editable feedback text area
        editable_feedback = st.text_area(
            f"Edit Feedback for {feedback['Name']} (User ID: {feedback['User ID']})",
            value=feedback['Feedback'],
            key=f"editable_feedback_{feedback['User ID']}_{assignment_id}"
        )

        # Editable grade input
        editable_grade = st.number_input(
            f"Edit Grade for {feedback['Name']} (User ID: {feedback['User ID']})",
            value=float(feedback['Grade']),
            min_value=0.0,
            max_value=10.0,
            step=0.1,
            key=f"editable_grade_{feedback['User ID']}_{assignment_id}"
        )

        # Update feedback data in session state
        if st.button(f"Update Feedback and Grade for {feedback['Name']}"):
            st.session_state.feedback_data[key]['Feedback'] = editable_feedback
            st.session_state.feedback_data[key]['Grade'] = editable_grade
            st.success(f"Updated feedback and grade for {feedback['Name']}.")

# Clear session state button
if st.button("Clear All Feedback Data"):
    st.session_state.feedback_data.clear()
    st.success("All feedback data cleared.")
