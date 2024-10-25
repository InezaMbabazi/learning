import streamlit as st
import requests

# Canvas API token and base URL
API_TOKEN = 'YOUR_API_TOKEN_HERE'  # Replace with your actual Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

# Function to get submissions for an assignment with logging for debugging
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    submissions_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    
    response = requests.get(submissions_url, headers=headers)
    
    if response.status_code == 200:
        submissions = response.json()
        if submissions:
            st.write(f"Found {len(submissions)} submissions.")
            return submissions
        else:
            st.warning("No submissions found for this assignment.")
            return []
    else:
        st.error(f"Failed to retrieve submissions. Status Code: {response.status_code}")
        st.write(response.json())  # Log the response to understand any errors
        return []

# Streamlit UI for debugging and confirmation
st.title("Canvas Assignment Submissions Checker")

# Course and Assignment ID
course_id = 2850  # Replace with your course ID
assignment_id = 45964  # Replace with your assignment ID

# Check for submissions
if st.button("Check Submissions"):
    submissions = get_submissions(course_id, assignment_id)
    
    # Display basic submission data if available
    if submissions:
        for submission in submissions:
            st.write(submission)  # Log each submission's data to understand the structure and content available
