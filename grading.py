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

# Function to fetch submissions from Canvas
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to retrieve submissions. Status Code: {response.status_code}")
        return []

# Function to download submission file
def download_submission_file(file_url):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(file_url, headers=headers)
    
    return response.content if response.status_code == 200 else None

# Function to submit feedback and grade in Canvas
def submit_feedback(course_id, assignment_id, user_id, feedback, grade):
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "comment": {"text_comment": feedback},
        "submission": {"posted_grade": grade}  # Ensure grade remains numeric (0 or 1)
    }

    url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    response = requests.put(url, headers=headers, json=payload)
    
    # Debugging: Show API response
    st.write(f"**Debugging Info:** Submitting feedback for User ID {user_id}")
    st.write(f"Status Code: {response.status_code}")
    st.write(f"Response: {response.text}")

    return response.status_code in [200, 201]

# Function to generate AI-based feedback
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
st.title("📚 Kepler College Grading System")

# Input Fields for Course & Assignment
course_id = st.number_input("Enter Course ID:", min_value=1, step=1)
assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1)
proposed_answer = st.text_area("Enter the proposed answer for evaluation:")

# Button to Download and Grade Submissions
if st.button("📥 Download and Grade Submissions"):
    submissions = get_submissions(course_id, assignment_id)
    if submissions:
        all_feedback = []
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
                st.write(f"Suggested Grade: {'✅ Pass' if grade == 1 else '❌ Revise and Resubmit'}")
                
                # Editable Feedback & Grade
                editable_feedback = st.text_area(f"Edit Feedback for {user_name}:", feedback, key=f"feedback_{user_id}")
                editable_grade = st.radio(
                    f"Select Grade for {user_name}:", 
                    [("✅ Pass", 1), ("❌ Revise and Resubmit", 0)], 
                    index=grade, key=f"grade_{user_id}", 
                    format_func=lambda x: x[0]
                )

                # Store feedback for bulk submission
                all_feedback.append((user_id, editable_feedback, editable_grade[1]))

        # Submit all feedback with a single button
        if st.button("🚀 Submit All Feedback"):
            for user_id, feedback, grade in all_feedback:
                success = submit_feedback(course_id, assignment_id, user_id, feedback, grade)
                if success:
                    st.success(f"✅ Feedback submitted for {user_id}")
                else:
                    st.error(f"❌ Failed to submit feedback for {user_id}")

