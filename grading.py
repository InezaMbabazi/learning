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

# Function to display Excel content in Streamlit
def display_excel_content(file_content):
    df = pd.read_excel(io.BytesIO(file_content))
    st.dataframe(df)

# Function to generate grading and feedback using OpenAI
def generate_grading_feedback(submission_text, proposed_answer):
    if openai.api_key is None:
        st.error("OpenAI API key is missing. Please configure it to proceed.")
        return None, None

    prompt = (
        f"Evaluate the student's submission and compare it with the proposed answer provided. "
        f"Provide a grade out of 100 based on content accuracy and completeness, "
        f"and give specific feedback on areas of improvement and strengths.\n\n"
        f"Student's Submission:\n{submission_text}\n\n"
        f"Proposed Answer:\n{proposed_answer}\n\n"
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    feedback_content = response['choices'][0]['message']['content'].strip()
    
    # Parse grade and feedback from response
    grade, feedback = None, None
    if "Grade:" in feedback_content:
        lines = feedback_content.split("\n")
        for line in lines:
            if line.lower().startswith("grade:"):
                grade = line.split(": ")[1].strip()
                feedback = "\n".join(lines[1:]).strip()
                break
    else:
        feedback = feedback_content  # If no specific grade line is found

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
st.title("Kepler College Grading System with OpenAI Integration")

# Option to select Canvas or Local upload in the sidebar
source = st.sidebar.radio("Choose file source:", ("Canvas", "Upload from Local"))

if source == "Upload from Local":
    uploaded_file = st.file_uploader("Upload student submission file")
    if uploaded_file:
        file_content = uploaded_file.read()
        filename = uploaded_file.name
        
        if filename.endswith(".txt"):
            submission_text = file_content.decode('utf-8')
            st.text_area("Text Submission", submission_text, height=200)
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(file_content))
            submission_text = "\n".join([para.text for para in doc.paragraphs])
            st.text_area("Word Document Submission", submission_text, height=200)
        
        # Process grading if submission is text-based
        if submission_text:
            proposed_answer = st.text_area("Enter Proposed Answer for Evaluation:", height=100)
            if proposed_answer:
                grade, feedback = generate_grading_feedback(submission_text, proposed_answer)
                st.write("**Grade:**", grade if grade else "Not Assigned")
                st.write("**Feedback:**", feedback if feedback else "No feedback generated.")
else:
    # Download from Canvas
    course_id = 2850  # Replace with your course ID
    assignment_id = 45964  # Replace with your assignment ID
    submissions = get_submissions(course_id, assignment_id)
    if submissions:
        proposed_answer = st.text_area("Enter Proposed Answer for Evaluation:", height=100)
        feedback_data = []

        if proposed_answer:
            for submission in submissions:
                user_id = submission['user_id']
                user_name = submission['user']['name'] if 'user' in submission else f"User {user_id}"
                attachments = submission.get('attachments', [])
                
                for attachment in attachments:
                    file_content = download_submission_file(attachment['url'])
                    filename = attachment['filename']
                    submission_text = ""

                    if filename.endswith(".txt") and file_content:
                        submission_text = file_content.decode('utf-8')
                    elif filename.endswith(".docx") and file_content:
                        doc = Document(io.BytesIO(file_content))
                        submission_text = "\n".join([para.text for para in doc.paragraphs])
                    
                    if submission_text:
                        grade, feedback = generate_grading_feedback(submission_text, proposed_answer)
                        st.write(f"**{user_name}** - Grade: {grade if grade else 'Not Assigned'}, Feedback: {feedback if feedback else 'No feedback generated.'}")
                        feedback_data.append((user_id, grade, feedback))

            # Submit all feedback to Canvas
            if st.button("Submit All Feedback to Canvas"):
                for user_id, grade, feedback in feedback_data:
                    submit_feedback_to_canvas(course_id, assignment_id, user_id, grade, feedback)
                    st.success(f"Feedback submitted for User {user_id}")
