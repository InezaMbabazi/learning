import streamlit as st
import requests
import io
from docx import Document
import openai
import pandas as pd

# Canvas API token and base URL
API_TOKEN = '1941~GP768CAHzwHRJFZvYr2nzCcMu8ta9mFuWGMenDw9N7h6Ef73y97z2uwGkerP3nWm'
BASE_URL = 'https://kepler.instructure.com/api/v1'

# OpenAI API Key
openai.api_key = st.secrets["openai"]["api_key"]

st.set_page_config(page_title="Kepler College Grading System", page_icon="📚", layout="wide")

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

def generate_feedback(submission_text, proposed_answer):
    """
    Generate feedback based on the similarity of the submission to the proposed answer.
    """
    if not proposed_answer.strip():
        return "No proposed answer provided. Unable to give feedback.", 0

    comparison_prompt = (
        f"Compare the following user submission to the proposed answer. If there are similarities, "
        f"highlight areas to improve and correct. If there are no similarities, provide feedback asking the student "
        f"to revise their response completely.\n\n**Proposed Answer**:\n{proposed_answer}\n\n"
        f"**User Submission**:\n{submission_text}\n\nProvide clear, actionable feedback."
    )

    try:
        feedback_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": comparison_prompt}]
        )
        feedback_message = feedback_response['choices'][0]['message']['content']
        grade = 1 if "improve" in feedback_message.lower() or "correct" in feedback_message.lower() else 0
    except Exception as e:
        feedback_message = "An error occurred while generating feedback. Please try again."
        grade = 0

    return feedback_message, grade

# Streamlit UI
st.title("Kepler College Grading System")

course_id = st.number_input("Enter Course ID:", min_value=1, step=1)
assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1)
proposed_answer = st.text_area("Enter the proposed answer for evaluation:")

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
                if attachment['filename'].endswith(".docx") and file_content:
                    doc = Document(io.BytesIO(file_content))
                    submission_text = "\n".join([para.text for para in doc.paragraphs])

            if submission_text:
                st.subheader(f"Submission by {user_name} (User ID: {user_id})")
                st.text_area("User Submission:", submission_text, height=200)

                feedback, grade = generate_feedback(submission_text, proposed_answer)
                st.text_area(f"Generated Feedback for {user_name}:", feedback, height=200)
                st.write(f"Suggested Grade: {'Pass' if grade == 1 else 'Revise and Resubmit'}")
                
                # Optional: Allow editing feedback
                editable_feedback = st.text_area(f"Edit Feedback for {user_name}:", feedback, key=f"feedback_{user_id}")
                editable_grade = st.selectbox(f"Edit Grade for {user_name}:", ["Pass", "Revise and Resubmit"], index=grade, key=f"grade_{user_id}")

                if st.button(f"Submit Feedback for {user_name}", key=f"submit_{user_id}"):
                    success = submit_feedback(course_id, assignment_id, user_id, editable_feedback, grade)
                    if success:
                        st.success(f"Feedback submitted successfully for {user_name}.")
                    else:
                        st.error(f"Failed to submit feedback for {user_name}.")
