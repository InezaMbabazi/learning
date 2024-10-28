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
st.markdown("""
<style>
    .header { text-align: center; color: #4B0082; font-size: 30px; font-weight: bold; }
    .content { border: 2px solid #4B0082; padding: 20px; border-radius: 10px; background-color: #F3F4F6; }
    .submission-title { font-size: 24px; color: #4B0082; }
    .submission-text { font-size: 20px; border: 2px solid #4B0082; padding: 10px; background-color: #E6E6FA; border-radius: 10px; color: #333; font-weight: bold; }
    .feedback-title { color: #FF4500; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Function to get submissions for an assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions", headers=headers)
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

# Function to display Excel content
def display_excel_content(file_content):
    df = pd.read_excel(io.BytesIO(file_content))
    st.dataframe(df)

# Function to submit feedback to Canvas
def submit_feedback(course_id, assignment_id, user_id, feedback, grade):
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "comment": {
            "text_comment": feedback
        },
        "submission": {
            "posted_grade": grade  # Include the grade in the payload
        }
    }

    # Construct the URL using the provided IDs
    url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    
    response = requests.put(url, headers=headers, json=payload)  # Changed to PUT for grading

    print(f"Submitting feedback for user ID {user_id}...")
    print(f"Request Payload: {payload}")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    if response.status_code in [200, 201]:
        return True, f"Successfully submitted feedback for user ID {user_id}."
    else:
        print(response.text)
        return False, f"Failed to submit feedback for user ID {user_id}. Status code: {response.status_code} Response: {response.text}"

# Function to generate automated feedback using OpenAI
def generate_feedback(proposed_answer):
    prompt = f"Generate feedback based on the following proposed answer:\n{proposed_answer}\nFeedback:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        feedback = response.choices[0].message['content'].strip()
        return feedback
    except Exception as e:
        st.error(f"Error generating feedback: {str(e)}")
        return "Error generating feedback."

# Function to calculate grade automatically
def calculate_grade(submission_text):
    # Example grading logic based on the length and keyword presence
    keywords = ["important", "necessary", "critical"]  # Define keywords
    base_grade = 5  # Starting point for grade out of 10
    
    # Length criteria
    if len(submission_text) > 500:  # Arbitrary length threshold
        base_grade += 2
    elif len(submission_text) < 200:
        base_grade -= 1

    # Keyword presence
    for keyword in keywords:
        if keyword in submission_text.lower():
            base_grade += 1

    # Ensure grade is within the range of 0 to 10
    return min(max(base_grade, 0), 10)

# Streamlit UI
st.image("header.png", use_column_width=True)
st.markdown('<h1 class="header">Kepler College Grading System</h1>', unsafe_allow_html=True)

# Input fields for course ID and assignment ID
course_id = st.number_input("Enter Course ID:", min_value=1, step=1, value=2906)
assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1, value=47134)

proposed_answer = st.text_area("Proposed Answer for Evaluation:", height=100)

# Initialize session state for feedback if not already done
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []

if st.button("Download and Grade Submissions") and proposed_answer:
    submissions = get_submissions(course_id, assignment_id)
    if submissions:
        for submission in submissions:
            user_id = submission['user_id']  # Fetch user ID
            submission_id = submission['id']  # Fetch submission ID
            user_name = submission.get('user', {}).get('name', f"User {user_id}")
            attachments = submission.get('attachments', [])
            submission_text = ""

            # Fetch existing feedback
            existing_feedback = submission.get('comment', {}).get('text_comment', "")

            for attachment in attachments:
                file_content = download_submission_file(attachment['url'])
                filename = attachment['filename']

                if filename.endswith(".txt") and file_content:
                    submission_text = file_content.decode('utf-8')
                elif filename.endswith(".docx") and file_content:
                    doc = Document(io.BytesIO(file_content))
                    submission_text = "\n".join([para.text for para in doc.paragraphs])
                elif filename.endswith(".xlsx") and file_content:
                    st.markdown(f'<div class="submission-title">Excel Submission from {user_name}</div>', unsafe_allow_html=True)
                    display_excel_content(file_content)
                    continue

                if submission_text:
                    st.markdown(f'<div class="submission-title">Submission by {user_name} (User ID: {user_id}, Submission ID: {submission_id})</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="submission-text">{submission_text}</div>', unsafe_allow_html=True)

                    # Display the existing feedback
                    st.markdown(f"**Feedback for {user_name}:** {existing_feedback}")

                    # Generate automated feedback based on the proposed answer
                    generated_feedback = generate_feedback(proposed_answer)

                    # Automatically calculate grade
                    auto_grade = calculate_grade(submission_text)

                    # Input for grade (scale out of 10)
                    grade_input = st.number_input(
                        f"Grade for {user_name} (0-10)", 
                        value=float(auto_grade),  # Ensure the default grade is a float
                        min_value=0.0, 
                        max_value=10.0, 
                        step=0.1, 
                        key=f"grade_{user_id}"
                    )

                    # Create unique keys for each user
                    feedback_input = st.text_area(f"Feedback for {user_name}", value=generated_feedback, height=100, key=f"feedback_{user_id}")

                    # Update session state to maintain user feedback
                    feedback_entry = {
                        "Student Name": user_name,
                        "Feedback": feedback_input,
                        "User ID": user_id,
                        "Submission ID": submission_id,
                        "Grade": grade_input  # Store the grade in the feedback entry
                    }
                    # Update the feedback data in session state
                    for i, entry in enumerate(st.session_state.feedback_data):
                        if entry["User ID"] == user_id:
                            st.session_state.feedback_data[i] = feedback_entry
                            break
                    else:
                        st.session_state.feedback_data.append(feedback_entry)

# Button to submit feedback and grades
if st.button("Submit Feedback to Canvas"):
    if not st.session_state.feedback_data:
        st.warning("No feedback available to submit.")
    else:
        for entry in st.session_state.feedback_data:
            success, message = submit_feedback(course_id, assignment_id, entry["User ID"], entry["Feedback"], entry["Grade"])
            st.success(message) if success else st.error(message)

# Display the session state feedback data
if st.session_state.feedback_data:
    st.subheader("Feedback Data")
    for feedback_entry in st.session_state.feedback_data:
        st.markdown(f"**{feedback_entry['Student Name']} (User ID: {feedback_entry['User ID']}, Submission ID: {feedback_entry['Submission ID']})**")
        st.markdown(f"Feedback: {feedback_entry['Feedback']}")
        st.markdown(f"Grade: {feedback_entry['Grade']}")
