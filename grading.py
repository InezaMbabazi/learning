import streamlit as st
import requests
import pandas as pd
import os

# Canvas API token and base URL
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'  # Replace with your actual Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

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
def download_submission_file(file_url, filename):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(file_url, headers=headers)
    
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    else:
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
    
    response = requests.put(grade_url, headers=headers, json=data)
    return response.status_code == 200

# Streamlit UI
st.title("Canvas Assignment Submissions Downloader and Grader")

# Course and Assignment ID
course_id = 2850  # Replace with your course ID
assignment_id = 45964  # Replace with your assignment ID

# Fetch and display submissions
if st.button("Download All Submissions"):
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
                    st.write(f"Downloaded {filename}")
                else:
                    st.write(f"Failed to download file for user {user_id}")
        
        st.success("All submissions downloaded successfully.")
    else:
        st.warning("No submissions found for this assignment.")

# Grading and Feedback Section
st.header("Grade and Provide Feedback")

# Loop through each submission and allow grading
for submission in submissions:
    user_id = submission['user_id']
    st.subheader(f"Submission for User {user_id}")
    
    grade = st.text_input(f"Grade for User {user_id}", "")
    feedback = st.text_area(f"Feedback for User {user_id}", "")

    if st.button(f"Submit Grade and Feedback for User {user_id}"):
        if submit_grade_feedback(course_id, assignment_id, user_id, grade, feedback):
            st.success(f"Grade and feedback submitted for User {user_id}")
        else:
            st.error(f"Failed to submit grade and feedback for User {user_id}")
