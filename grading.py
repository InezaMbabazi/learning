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
    .btn { background-color: #4B0082; color: white; padding: 10px; border-radius: 5px; cursor: pointer; }
    .btn:hover { background-color: #5E2B91; }
</style>
""", unsafe_allow_html=True)

# Function to get submissions for an assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    submissions_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    response = requests.get(submissions_url, headers=headers)
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
    st.dataframe(df)  # Display as a structured table in columns

# Function to generate grading and feedback using OpenAI
def generate_grading_feedback(submission_text, proposed_answer):
    if openai.api_key is None:
        st.error("OpenAI API key is missing. Please configure it to proceed.")
        return None, None

    prompt = (
        f"Evaluate the following student's submission against the proposed answer. "
        f"Assess alignment and rate it from 0 to 100. If there is no alignment, respond that there is no alignment and don't give a grade.\n\n"
        f"Submission: {submission_text}\n"
        f"Proposed Answer: {proposed_answer}\n\n"
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    feedback_content = response['choices'][0]['message']['content'].strip()
    
    if "no alignment" in feedback_content.lower():
        grade = None  # No grade if no alignment
        feedback = "No alignment with the proposed answer."
    else:
        lines = feedback_content.split("\n")
        grade = lines[0].split(": ")[1].strip() if "Grade:" in lines[0] else "Not Assigned"
        feedback = "\n".join(lines[1:]).strip()
    
    return grade, feedback

# Function to submit feedback to Canvas
def submit_feedback_to_canvas(course_id, assignment_id, user_id, grade, feedback):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    submission_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    payload = {
        "submission": {"posted_grade": grade} if grade else {},
        "comment": {"text_comment": feedback}
    }
    response = requests.put(submission_url, headers=headers, json=payload)
    return response.status_code == 200

# Streamlit UI
st.image("header.png", use_column_width=True)  # Display header image
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

# Option to select Canvas or local upload
input_type = st.radio("Choose Submission Source:", ["Canvas", "Local Upload"])

if input_type == "Canvas":
    # Set Course and Assignment IDs
    course_id = 2850  # Replace with your course ID
    assignment_id = 45964  # Replace with your assignment ID

    # Proposed Answer Input
    proposed_answer = st.text_area("Proposed Answer for Evaluation:", height=100)
    if not proposed_answer:
        st.warning("Please enter the proposed answer before downloading submissions.")

    # Download submissions only if proposed answer is provided
    if st.button("Download and Grade Submissions") and proposed_answer:
        submissions = get_submissions(course_id, assignment_id)
        if submissions:
            feedback_data = []

            for submission in submissions:
                user_id = submission['user_id']
                user_name = submission['user']['name'] if 'user' in submission else f"User {user_id}"
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
                        continue  # Skip text display for Excel files
                    
                    if submission_text:
                        st.markdown(f'<div class="submission-title">Submission by {user_name}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="submission-text">{submission_text}</div>', unsafe_allow_html=True)

                        grade, feedback = generate_grading_feedback(submission_text, proposed_answer)
                        grade_input = st.text_input(f"Grade for {user_name}", value=grade or "Not Assigned", key=f"grade_{user_id}")
                        feedback_input = st.text_area(f"Feedback for {user_name}", value=feedback, height=100, key=f"feedback_{user_id}")
                        
                        feedback_data.append({
                            "Student Name": user_name,
                            "Grade": grade_input,
                            "Feedback": feedback_input,
                            "User ID": user_id
                        })

            if st.button("Submit Feedback to Canvas"):
                for entry in feedback_data:
                    user_id = entry["User ID"]
                    grade = entry["Grade"]
                    feedback = entry["Feedback"]
                    
                    if submit_feedback_to_canvas(course_id, assignment_id, user_id, grade, feedback):
                        st.success(f"Feedback submitted for {entry['Student Name']}")
                    else:
                        st.error(f"Failed to submit feedback for {entry['Student Name']}")

else:
    st.write("Upload submissions from local storage.")
    uploaded_file = st.file_uploader("Choose a file", type=["txt", "docx", "xlsx"])

    if uploaded_file:
        if uploaded_file.name.endswith(".txt"):
            submission_text = uploaded_file.read().decode("utf-8")
            st.write(submission_text)
        elif uploaded_file.name.endswith(".docx"):
            doc = Document(uploaded_file)
            submission_text = "\n".join([para.text for para in doc.paragraphs])
            st.write(submission_text)
        elif uploaded_file.name.endswith(".xlsx"):
            display_excel_content(uploaded_file)
