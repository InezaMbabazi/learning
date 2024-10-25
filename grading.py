import streamlit as st
import requests
import os
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
    
    prompt = f"Grade the following submission based on the proposed answer:\n\n" \
             f"Submission: {submission_text}\n" \
             f"Proposed Answer: {proposed_answer}\n" \
             f"Provide a grade (out of 100) and detailed feedback on the submission's strengths and weaknesses."
    
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
    
    if submissions:
        download_folder = "submissions"
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        for submission in submissions:
            user_id = submission['user_id']
            attachments = submission.get('attachments', [])
            
            submission_text = ""
            for attachment in attachments:
                file_url = attachment['url']
                filename = os.path.join(download_folder, f"{user_id}_{attachment['filename']}")
                
                if download_submission_file(file_url, filename):
                    st.success(f"Downloaded {filename}")
                    
                    # Display the content of the downloaded file
                    if filename.endswith(".txt"):
                        with open(filename, "r") as f:
                            submission_text = f.read()
                            st.write(f"Submission Content from User {user_id}:\n{submission_text}")  # Display submission content
                    elif filename.endswith(".docx"):
                        doc = Document(filename)
                        doc_text = "\n".join([para.text for para in doc.paragraphs])
                        st.write(f"Submission Content from User {user_id}:\n{doc_text}")  # Display docx content
                else:
                    st.error(f"Failed to download file for user {user_id}")
        
        st.success("All submissions downloaded successfully.")
    else:
        st.warning("No submissions found for this assignment.")

# Grading and Feedback Section
st.header("Grade and Provide Feedback on Submission")

# Proposed answers input
proposed_answer = st.text_area("Enter Proposed Answer:", height=100)

# Check if submissions were retrieved before displaying grading options
if 'submissions' in locals() and submissions:
    # Automatically generate grades and feedback for all submissions
    if proposed_answer:
        for submission in submissions:
            user_id = submission['user_id']
            attachments = submission.get('attachments', [])
            
            submission_text = ""
            for attachment in attachments:
                file_url = attachment['url']
                filename = os.path.join(download_folder, f"{user_id}_{attachment['filename']}")
                
                # Read the submission text based on the file type
                if filename.endswith(".txt"):
                    with open(filename, "r") as f:
                        submission_text = f.read()
                elif filename.endswith(".docx"):
                    doc = Document(filename)
                    submission_text = "\n".join([para.text for para in doc.paragraphs])

                # Display the submission text
                st.write(f"Evaluating Submission from User {user_id}:\n{submission_text}")  # Display submission text
                        
                # Generate feedback
                feedback_output = generate_grading_feedback(submission_text, proposed_answer)
                if feedback_output:
                    try:
                        # Split into grade and feedback
                        grade, feedback = feedback_output.split('\n', 1)  
                        st.markdown(f"<p style='color: green;'>Generated Grade: {grade.strip()}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color: blue;'>Generated Feedback for User {user_id}: {feedback.strip()}</p>", unsafe_allow_html=True)
                    except ValueError:
                        st.error(f"Failed to parse feedback for User {user_id}: {feedback_output}")
else:
    st.warning("Please download submissions before grading.")

# Add some color for better user experience
st.markdown("""
<style>
body {
    background-color: #f0f4f7; /* Light background color */
}
h1 {
    color: #2c3e50; /* Darker text for headings */
}
h2 {
    color: #34495e; /* Darker text for subheadings */
}
.stButton {
    background-color: #3498db; /* Button color */
    color: white; /* Button text color */
}
.stButton:hover {
    background-color: #2980b9; /* Button hover color */
}
</style>
""", unsafe_allow_html=True)
