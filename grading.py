import streamlit as st
import requests
import os
from docx import Document
import openai
import pandas as pd

# Canvas API token and base URL
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'  # Replace with your Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

# OpenAI API Key from Streamlit secrets
try:
    openai.api_key = st.secrets["openai"]["api_key"]
except KeyError:
    st.error("OpenAI API key is missing. Please check your configuration.")
    openai.api_key = None

# Function to get submissions for an assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    submissions_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    
    try:
        response = requests.get(submissions_url, headers=headers)
        response.raise_for_status()  # Raise an error for HTTP errors
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.error(f"An error occurred: {err}")
    return []

# Function to generate grading and feedback using OpenAI
def generate_grading_feedback(submission_text, proposed_answer):
    if openai.api_key is None:
        st.error("OpenAI API key is not configured. Cannot generate feedback.")
        return None

    prompt = (
        f"Evaluate the following student's submission against the proposed answer. "
        f"Assess how well the submission aligns with the proposed answer and rate it on a scale of 0 to 100. "
        f"If the submission does not directly respond to the proposed answer, give zero and provide detailed feedback.\n\n"
        f"Submission: {submission_text}\n"
        f"Proposed Answer: {proposed_answer}\n\n"
        f"Provide a detailed assessment of the alignment, including strengths, weaknesses, and areas for improvement."
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        st.error(f"Error in OpenAI API call: {e}")
        return None

# Streamlit UI
st.title("Canvas Assignment Submissions Downloader, Grader, and Preview")

# Set Course and Assignment IDs
course_id = 2850  # Replace with your course ID
assignment_id = 45964  # Replace with your assignment ID

# Download submissions when the button is pressed
if st.button("Download All Submissions", key='download_button'):
    submissions = get_submissions(course_id, assignment_id)
    table_data = []

    for submission in submissions:
        user_id = submission['user_id']
        user_name = submission['user']['name'] if 'user' in submission else f"User {user_id}"
        submission_text = submission.get('body', "No submission text available")

        table_data.append({"Student Name": user_name, "Submission": submission_text, "Grade": "", "Feedback": ""})
    
    st.success("All submissions downloaded successfully.")
    
    # Display submissions in a table and make fields editable
    for index, data in enumerate(table_data):
        st.subheader(f"Student: {data['Student Name']}")
        st.text_area("Submission", data['Submission'], height=200, disabled=True)
        
        # Editable grade and feedback inputs
        grade = st.text_input(f"Grade for {data['Student Name']}", key=f"grade_{index}")
        feedback = st.text_area(f"Feedback for {data['Student Name']}", key=f"feedback_{index}", height=100)
        
        # Button to submit the grade and feedback to Canvas
        if st.button(f"Submit Grade & Feedback for {data['Student Name']}", key=f"submit_{index}"):
            headers = {"Authorization": f"Bearer {API_TOKEN}"}
            update_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
            payload = {"submission": {"posted_grade": grade, "text_comment": feedback}}
            
            response = requests.put(update_url, headers=headers, json=payload)
            if response.status_code == 200:
                st.success(f"Grade and feedback for {data['Student Name']} submitted successfully!")
            else:
                st.error(f"Failed to submit grade and feedback for {data['Student Name']}.")

# Note: Add style for better UI if needed
