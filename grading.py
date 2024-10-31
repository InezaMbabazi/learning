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
    return response.json() if response.status_code == 200 else []

def download_submission_file(file_url):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(file_url, headers=headers)
    return response.content if response.status_code == 200 else None

def submit_feedback(course_id, assignment_id, user_id, feedback, grade):
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    payload = {"comment": {"text_comment": feedback}, "submission": {"posted_grade": grade}}
    url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code in [200, 201]

def get_grading(student_submission, proposed_answer):
    grading_prompt = f"Evaluate the following student submission against the proposed answer and provide specific feedback:\n\n"
    grading_prompt += f"**Proposed Answer**: {proposed_answer}\n\n"
    grading_prompt += f"**Student Submission**: {student_submission}\n\n"
    grading_prompt += "Respond with clear, direct feedback that can be shared with the student."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    feedback = response['choices'][0]['message']['content']
    
    # Calculate alignment score
    grade = 1 if proposed_answer.lower() in student_submission.lower() else 0
    return feedback, grade

# Streamlit UI
st.image("header.png", use_column_width=True)
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

course_id = st.number_input("Enter Course ID:", min_value=1, step=1, value=2906)
assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1, value=47134)

proposed_answer = st.text_area("Enter the proposed answer for evaluation:", "")

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
                
                if submission_text:
                    feedback, grade = get_grading(submission_text, proposed_answer)
                    feedback_message = f"Dear {user_name},\n\n{feedback}\n\nPlease review this feedback to improve."

                    st.markdown(f"### Feedback for {user_name} (User ID: {user_id})")
                    st.markdown(f"**Feedback:** {feedback_message}")
                    st.markdown(f"**Grade:** {'1 (Aligned)' if grade == 1 else '0 (Not Aligned)'}")

                    # Submit feedback
                    if submit_feedback(course_id, assignment_id, user_id, feedback_message, grade):
                        st.success(f"Feedback submitted successfully for {user_name}.")
                    else:
                        st.error(f"Failed to submit feedback for {user_name}.")
