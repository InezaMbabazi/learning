import streamlit as st
import requests
import os
from docx import Document
import openai

# Canvas API token and base URL
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'  # Replace with your Canvas API token
BASE_URL = 'https://kepler.instructure.com/api/v1'

# OpenAI API Key
openai.api_key = st.secrets["openai"]["api_key"]

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

# Proposed answers input
proposed_answer = st.text_area("Enter Proposed Answer:", height=100)

# Check if submissions were retrieved before displaying grading options
if 'submissions' in locals() and submissions:
    submission_texts = []  # To store all submission texts
    user_ids = []          # To store user IDs

    for submission in submissions:
        user_id = submission['user_id']
        user_ids.append(user_id)
        st.subheader(f"Submission for User {user_id}")

        # Find downloaded files
        download_folder = "submissions"
        user_files = [f for f in os.listdir(download_folder) if f.startswith(str(user_id))]

        # Display each file in a bordered section
        for user_file in user_files:
            file_path = os.path.join(download_folder, user_file)
            with st.container():  # Create a bordered container
                st.markdown(f"<div style='border: 2px solid #2980b9; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
                if user_file.endswith(".txt"):
                    with open(file_path, "r") as f:
                        submission_text = f.read()
                        submission_texts.append(submission_text)  # Collect submission text
                        st.text(submission_text)
                elif user_file.endswith(".pdf"):
                    st.write("PDF file:", user_file)
                    st.download_button("Download PDF", open(file_path, "rb"), file_name=user_file)
                elif user_file.endswith((".jpg", ".jpeg", ".png")):
                    st.image(file_path)
                elif user_file.endswith(".docx"):
                    # Read and display .docx content
                    doc = Document(file_path)
                    doc_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    submission_texts.append(doc_text)  # Collect submission text
                    st.text(doc_text)
                else:
                    st.write(f"File type not supported for preview: {user_file}")
                st.markdown("</div>", unsafe_allow_html=True)  # Close the bordered container

    # Generate grade and feedback for all submissions when the button is clicked
    if st.button("Generate Grades and Feedback for All Submissions", key='generate_all'):
        all_feedbacks = []
        for submission_text in submission_texts:
            feedback_output = generate_grading_feedback(submission_text, proposed_answer)
            if feedback_output:
                all_feedbacks.append(feedback_output)
        
        # Store the feedback results
        if all_feedbacks:
            st.session_state.feedbacks = {user_id: feedback.split('\n', 1) for user_id, feedback in zip(user_ids, all_feedbacks)}
            st.success("Grades and feedback generated successfully.")

# Submit grades and feedback
if 'feedbacks' in st.session_state:
    st.header("Submit Grades and Feedback")
    
    for user_id, (grade, feedback) in st.session_state.feedbacks.items():
        st.subheader(f"Feedback for User {user_id}")
        st.text(f"Generated Grade: {grade.strip()}")
        feedback_area = st.text_area(f"Generated Feedback for User {user_id}", feedback.strip(), height=100)

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
