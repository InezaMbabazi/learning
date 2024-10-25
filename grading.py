import streamlit as st
import requests
import os
import openai

# Canvas API token and base URL
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'  # Replace with your Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

# Load OpenAI API Key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get assignment details
def get_assignment_details(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    assignment_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}"
    
    try:
        response = requests.get(assignment_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.error(f"An error occurred: {err}")
    return None

# Function to get submissions for an assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    submissions_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    
    try:
        response = requests.get(submissions_url, headers=headers)
        response.raise_for_status()
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

# Function to generate grading and feedback using OpenAI
def generate_grading_feedback(submission_text, proposed_answer):
    prompt = f"Grade the following submission based on the proposed answer:\n\n" \
             f"Submission: {submission_text}\n" \
             f"Proposed Answer: {proposed_answer}\n" \
             f"Provide a grade (out of 100) and feedback."
    
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

# Display Assignment Details
assignment_details = get_assignment_details(course_id, assignment_id)
if assignment_details:
    st.header(f"Assignment Title: {assignment_details['name']}")
    st.subheader("Description:")
    st.write(assignment_details['description'])

# Proposed answers input
proposed_answer = st.text_area("Enter Proposed Answer:", height=100)

# Initialize feedback storage in session state if not already present
if 'feedbacks' not in st.session_state:
    st.session_state.feedbacks = {}

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

        # Automatically generate grades and feedback for all submissions
        if proposed_answer:
            for submission in submissions:
                user_id = submission['user_id']
                attachments = submission.get('attachments', [])
                
                for attachment in attachments:
                    file_url = attachment['url']
                    filename = os.path.join(download_folder, f"{user_id}_{attachment['filename']}")
                    
                    if filename.endswith(".txt"):
                        with open(filename, "r") as f:
                            submission_text = f.read()
                            st.write(f"Evaluating Submission from User {user_id}:\n{submission_text})  # Debugging line
                            
                            # Generate feedback
                            feedback_output = generate_grading_feedback(submission_text, proposed_answer)
                            if feedback_output:
                                # Debugging: Check if output is not None
                                st.write(f"Feedback Output for User {user_id}: {feedback_output}")  # Debugging line
                                try:
                                    grade, feedback = feedback_output.split('\n', 1)  # Split into grade and feedback
                                    st.session_state.feedbacks[user_id] = (grade.strip(), feedback.strip())
                                except ValueError:
                                    st.error(f"Failed to parse feedback for User {user_id}: {feedback_output}")
        
        # Display generated feedback
        if st.session_state.feedbacks:
            st.header("Generated Grades and Feedback")
            for user_id, (grade, feedback) in st.session_state.feedbacks.items():
                st.subheader(f"Feedback for User {user_id}")
                st.text(f"Generated Grade: {grade.strip()}")
                st.text(f"Generated Feedback: {feedback.strip()}")

# Submit grades and feedback
if st.session_state.feedbacks:
    st.header("Submit Grades and Feedback")
    
    for user_id, (grade, feedback) in st.session_state.feedbacks.items():
        feedback_area = st.text_area(f"Feedback for User {user_id}", feedback.strip(), height=100)

        # Separate button to submit grade and feedback
        if st.button(f"Submit Grade and Feedback for User {user_id}", key=f'submit_{user_id}'):
            if submit_grade_feedback(course_id, assignment_id, user_id, grade.strip(), feedback_area.strip()):
                st.success(f"Grade and feedback submitted for User {user_id}")
            else:
                st.error(f"Failed to submit grade and feedback for User {user_id}")

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
