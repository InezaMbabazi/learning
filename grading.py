import streamlit as st 
import requests
import os
import pandas as pd
from docx import Document
import openai

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

# Function to download a submission file
def download_submission_file(file_url, filename):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.get(file_url, headers=headers)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred while downloading: {http_err}")
    except Exception as err:
        st.error(f"An error occurred while downloading: {err}")
    return False

# Function to generate grading and feedback using OpenAI
def generate_grading_feedback(submission_text, proposed_answer):
    if openai.api_key is None:
        st.error("OpenAI API key is not configured. Cannot generate feedback.")
        return None
    prompt = (
        f"Evaluate the following student's submission against the proposed answer. "
        f"Assess how well the submission aligns with the proposed answer and rate it on a scale of 0 to 100.\n\n"
        f"Submission: {submission_text}\n"
        f"Proposed Answer: {proposed_answer}\n\n"
        f"Provide a detailed assessment."
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
st.title("Canvas Assignment Grading Tool")

# Set Course and Assignment IDs
course_id = 2850  # Replace with your course ID
assignment_id = 45964  # Replace with your assignment ID

# Download and display submissions
if st.button("Download All Submissions"):
    submissions = get_submissions(course_id, assignment_id)
    if submissions:
        table_data = []
        for submission in submissions:
            user_id = submission['user_id']
            user_name = submission['user']['name'] if 'user' in submission else f"User {user_id}"
            attachments = submission.get('attachments', [])
            
            submission_text = ""
            for attachment in attachments:
                file_url = attachment['url']
                filename = f"submissions/{user_id}_{attachment['filename']}"
                
                if download_submission_file(file_url, filename):
                    st.success(f"Downloaded {filename}")
                    
                    # Load the file content
                    if filename.endswith(".txt"):
                        with open(filename, "r") as f:
                            submission_text = f.read()
                    elif filename.endswith(".docx"):
                        doc = Document(filename)
                        submission_text = "\n".join([para.text for para in doc.paragraphs])
                
                # Collect data for displaying in a table
                table_data.append({
                    "Student Name": user_name,
                    "Submission": submission_text,
                    "Grade": "",
                    "Feedback": ""
                })
        
        st.success("All submissions downloaded successfully.")
        submissions_df = pd.DataFrame(table_data)
        
        # Proposed answers input
        proposed_answer = st.text_area("Enter Proposed Answer:", height=100)
        
        # Editable table for grades and feedback
        st.header("Provide Grades and Feedback")
        
        # Iterate over each row to add editable inputs
        for idx, row in submissions_df.iterrows():
            st.subheader(f"Student: {row['Student Name']}")
            st.text_area("Submission:", row['Submission'], height=150, disabled=True)
            grade = st.number_input(f"Grade for {row['Student Name']}", value=0, min_value=0, max_value=100)
            feedback = st.text_area(f"Feedback for {row['Student Name']}", height=100)
            
            if st.button(f"Submit Feedback and Grade for {row['Student Name']}"):
                # Add code here to send feedback and grade to Canvas
                st.success(f"Grade and feedback submitted for {row['Student Name']}")
        
        # Option to view as a full table for final review
        st.dataframe(submissions_df)

st.markdown(""" 
<style>
body { background-color: #f0f4f7; }
h1 { color: #2c3e50; }
.stButton { background-color: #3498db; color: white; }
.stButton:hover { background-color: #2980b9; }
</style>
""", unsafe_allow_html=True)
