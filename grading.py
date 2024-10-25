import streamlit as st
import requests
import os
from docx import Document
import openai

# Canvas API token and base URL
API_TOKEN = 'your_canvas_api_token'  # Replace with your actual Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

# OpenAI API Key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get submissions for an assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    submissions_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    
    try:
        response = requests.get(submissions_url, headers=headers)
        response.raise_for_status()  # Raise error for unsuccessful status
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to retrieve submissions: {e}")
        return []

# Function to download a submission file
def download_submission_file(file_url, filename):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.get(file_url, headers=headers)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    except requests.RequestException:
        return False

# Function to grade and provide feedback using OpenAI API
def grade_with_openai(submission_text, proposed_answer):
    prompt = f"Grade the following submission based on the provided answer:\n\nSubmission:\n{submission_text}\n\nProposed Answer:\n{proposed_answer}\n\nProvide a grade out of 100 and feedback on how closely it matches the proposed answer."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        feedback = response.choices[0].message['content']
        return feedback
    except Exception as e:
        st.error(f"Error generating feedback: {e}")
        return "Feedback could not be generated."

# Streamlit UI
st.title("Canvas Assignment Submissions with Automated Grading and Feedback")

# Course and Assignment ID
course_id = 2850  # Replace with your course ID
assignment_id = 45964  # Replace with your assignment ID

# Fetch submissions
submissions = []

if st.button("Fetch Submissions"):
    submissions = get_submissions(course_id, assignment_id)
    if submissions:
        st.success("Submissions retrieved successfully.")
    else:
        st.warning("No submissions found for this assignment or failed to retrieve submissions.")

# Input for the correct answer
st.header("Provide the Correct Answer")
proposed_answer = st.text_area("Enter the ideal answer for automatic grading:", "")

# Grading and Feedback Section
st.header("Grade, Provide Feedback, and Preview Submission")

if submissions and proposed_answer:
    for submission in submissions:
        user_id = submission['user_id']
        st.subheader(f"Submission for User {user_id}")
        
        # Find downloaded files
        download_folder = "submissions"
        os.makedirs(download_folder, exist_ok=True)
        
        user_files = [f for f in os.listdir(download_folder) if f.startswith(str(user_id))]

        for user_file in user_files:
            file_path = os.path.join(download_folder, user_file)
            if user_file.endswith(".docx"):
                # Read and display .docx content
                doc = Document(file_path)
                submission_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                st.text(submission_text)

                # Use OpenAI to grade and give feedback
                feedback = grade_with_openai(submission_text, proposed_answer)
                
                # Parse grade and feedback from OpenAI response
                grade = feedback.split("\n")[0].replace("Grade:", "").strip()
                detailed_feedback = "\n".join(feedback.split("\n")[1:])

                st.write(f"Generated Grade: {grade}")
                st.write("Feedback:")
                st.write(detailed_feedback)
else:
    st.info("Please fetch submissions and enter the proposed answer before grading.")
