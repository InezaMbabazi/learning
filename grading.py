import streamlit as st
import requests
import os
from docx import Document

# Canvas API token and base URL
API_TOKEN = 'YOUR_ACTUAL_CANVAS_API_TOKEN'  # Replace with your Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

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

# Function to submit grade and feedback
def submit_grade_feedback(course_id, assignment_id, user_id, grade, feedback):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    grade_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    
    data = {
        "submission": {
            "posted_grade": grade,
            "comment": {
                "text_comment": feedback
            }
        }
    }
    
    try:
        response = requests.put(grade_url, headers=headers, json=data)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred while submitting grade: {http_err}")
    except Exception as err:
        st.error(f"An error occurred while submitting grade: {err}")
    return False

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
            
            for attachment in attachments:
                file_url = attachment['url']
                filename = os.path.join(download_folder, f"{user_id}_{attachment['filename']}")
                
                if download_submission_file(file_url, filename):
                    st.success(f"Downloaded {filename}")
                else:
                    st.error(f"Failed to download file for user {user_id}")
        
        st.success("All submissions downloaded successfully.")
    else:
        st.warning("No submissions found for this assignment.")

# Grading and Feedback Section
st.header("Grade, Provide Feedback, and Preview Submission")

# Check if submissions were retrieved before displaying grading options
if 'submissions' in locals() and submissions:
    for submission in submissions:
        user_id = submission['user_id']
        st.subheader(f"Submission for User {user_id}")

        # Find downloaded files
        download_folder = "submissions"
        user_files = [f for f in os.listdir(download_folder) if f.startswith(str(user_id))]

        # Display each file
        for user_file in user_files:
            file_path = os.path.join(download_folder, user_file)
            if user_file.endswith(".txt"):
                with open(file_path, "r") as f:
                    st.text(f.read())
            elif user_file.endswith(".pdf"):
                st.write("PDF file:", user_file)
                st.download_button("Download PDF", open(file_path, "rb"), file_name=user_file)
            elif user_file.endswith((".jpg", ".jpeg", ".png")):
                st.image(file_path)
            elif user_file.endswith(".docx"):
                # Read and display .docx content
                doc = Document(file_path)
                doc_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                st.text(doc_text)
            else:
                st.write(f"File type not supported for preview: {user_file}")

        # Grade and feedback inputs
        grade = st.text_input(f"Grade for User {user_id}", "")
        feedback = st.text_area(f"Feedback for User {user_id}", "", height=100)

        if st.button(f"Submit Grade and Feedback for User {user_id}", key=f'submit_{user_id}'):
            if submit_grade_feedback(course_id, assignment_id, user_id, grade, feedback):
                st.success(f"Grade and feedback submitted for User {user_id}")
            else:
                st.error(f"Failed to submit grade and feedback for User {user_id}")
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
    color: #2980b9; /* Blue color for subheadings */
}
.stButton {
    background-color: #27ae60; /* Green color for buttons */
    color: white;
}
.stButton:hover {
    background-color: #2ecc71; /* Lighter green on hover */
}
</style>
""", unsafe_allow_html=True)
