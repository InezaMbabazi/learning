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

# Function to fetch submissions from Canvas with pagination handling
def get_submissions(course_id, assignment_id):
    submissions = []
    page = 1

    while True:
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions?page={page}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            submissions.extend(data)  # Add submissions from this page to the list
            
            # Check if there's a next page
            if 'next' in response.links:
                page += 1
            else:
                break  # No more pages, exit the loop
        else:
            st.error(f"Failed to retrieve submissions. Status Code: {response.status_code}")
            break

    return submissions

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
    return response.status_code, response.text

# Function to generate AI-based feedback
def generate_feedback(submission_text, proposed_answer):
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
course_id = st.number_input("Enter Course ID:", min_value=1, step=1, key="course_id")
assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1, key="assignment_id")
proposed_answer = st.text_area("Enter the proposed answer for evaluation:", key="proposed_answer")

# Initialize session state
if "feedback_data" not in st.session_state:
    st.session_state["feedback_data"] = {}

# Button to Download and Grade Submissions
if st.button("📥 Download and Grade Submissions"):
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
                feedback, grade = generate_feedback(submission_text, proposed_answer)

                # Store feedback and grade in session state
                st.session_state["feedback_data"][user_id] = {
                    "user_name": user_name,
                    "submission_text": submission_text,
                    "feedback": feedback,
                    "grade": grade
                }

# Display stored feedback for each student
if st.session_state["feedback_data"]:
    for user_id, data in st.session_state["feedback_data"].items():
        st.subheader(f"Submission by {data['user_name']} (User ID: {user_id})")
        st.text_area("User Submission:", data['submission_text'], height=200, key=f"submission_{user_id}")
        
        editable_feedback = st.text_area(
            f"Edit Feedback for {data['user_name']}:", 
            data['feedback'], 
            key=f"feedback_{user_id}"
        )

        editable_grade = st.radio(
            f"Select Grade for {data['user_name']}:",
            [("✅ Pass", 1), ("❌ Revise and Resubmit", 0)],
            index=data['grade'],
            key=f"grade_{user_id}",
            format_func=lambda x: x[0]
        )

        # Update session state with user modifications
        st.session_state["feedback_data"][user_id]["feedback"] = editable_feedback
        st.session_state["feedback_data"][user_id]["grade"] = editable_grade[1]

# Submit all feedback with a single button
if st.button("🚀 Submit All Feedback"):
    for user_id, user_data in st.session_state["feedback_data"].items():
        status_code, response_text = submit_feedback(
            course_id, assignment_id, user_id, user_data["feedback"], user_data["grade"]
        )

        if status_code in [200, 201]:
            st.success(f"✅ Feedback submitted for {user_id}")
        else:
            st.error(f"❌ Failed to submit feedback for {user_id}. Response: {response_text}")

