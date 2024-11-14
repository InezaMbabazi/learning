import streamlit as st
import requests
import io
from docx import Document
import openai
import pandas as pd

# Canvas API token and base URL
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'
BASE_URL = 'https://kepler.instructure.com/api/v1'

# OpenAI API Key
openai.api_key = st.secrets["openai"]["api_key"]

# Turnitin API token and base URL
TURNITIN_API_TOKEN = 'f015c795c0214bb990d611439697784c'
TURNITIN_BASE_URL = 'https://api.turnitin.com/api/v1'

st.set_page_config(page_title="Kepler College Grading System", page_icon="📚", layout="wide")

def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to retrieve submissions.")
        return []

def download_submission_file(file_url):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(file_url, headers=headers)
    return response.content if response.status_code == 200 else None

def display_excel_content(file_content):
    df = pd.read_excel(io.BytesIO(file_content))
    st.dataframe(df)

def submit_feedback(course_id, assignment_id, user_id, feedback, grade):
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "comment": {
            "text_comment": feedback
        },
        "submission": {
            "posted_grade": grade
        }
    }
    url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code in [200, 201]

def check_plagiarism(submission_text):
    headers = {"Authorization": f"Bearer {TURNITIN_API_TOKEN}", "Content-Type": "application/json"}
    payload = {"text": submission_text}
    response = requests.post(f"{TURNITIN_BASE_URL}/check", headers=headers, json=payload)
    if response.status_code == 200:
        plagiarism_score = response.json().get("plagiarism_score", "N/A")
        st.markdown(f"<span style='color:red;'>Plagiarism Score: {plagiarism_score}%</span>", unsafe_allow_html=True)
        return plagiarism_score
    else:
        st.warning("Failed to retrieve plagiarism score.")
        return "N/A"


def get_grading(submission_text, proposed_answer):
    if not proposed_answer.strip():
        return "No proposed answer provided. Unable to give feedback.", 0

    correlation_prompt = (
        f"Compare the following user submission to the proposed answer and rate the alignment as a percentage (0-100)."
        f"\n\n**Proposed Answer**:\n{proposed_answer}\n\n**User Submission**:\n{submission_text}\n\n"
        "Provide only the correlation percentage as an integer."
    )

    try:
        correlation_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": correlation_prompt}]
        )
        correlation_percentage = float(correlation_response['choices'][0]['message']['content'].strip())

    except ValueError:
        correlation_percentage = 0  # Fallback if parsing fails
        st.warning("Could not parse correlation percentage. Defaulting to 0.")

    feedback_message, alignment_grade = generate_feedback(correlation_percentage, submission_text, proposed_answer)

    return feedback_message, alignment_grade

def generate_feedback(correlation_percentage, submission_text, proposed_answer):
    # Feedback generation logic (same as in your original code)
    # ...
    return feedback_message, alignment_grade

# Streamlit UI
st.image("header.png", use_column_width=True)
st.title("Kepler College Grading System")

course_id = st.number_input("Enter Course ID:", min_value=1, step=1)
assignment_id = st.number_input("Enter Assignment ID:", min_value=1, step=1)

proposed_answer = st.text_area("Enter the proposed answer for evaluation:")

if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = {}

if st.button("Download and Grade Submissions"):
    submissions = get_submissions(course_id, assignment_id)
    if submissions:
        for submission in submissions:
            user_id = submission['user_id']
            user_name = submission.get('user', {}).get('name', f"User {user_id}")
            attachments = submission.get('attachments', [])
            submission_text = ""

            for attachment in attachments:
                file_content = download_submission_file(attachment['url'])
                filename = attachment['filename']
                
                if filename.endswith(".txt") and file_content:
                    submission_text = file_content.decode('utf-8')
                elif filename.endswith(".docx") and file_content:
                    doc = Document(io.BytesIO(file_content))
                    submission_text = "\n".join([para.text for para in doc.paragraphs])
                elif filename.endswith(".xlsx") and file_content:
                    st.write(f"Excel Submission from {user_name}")
                    display_excel_content(file_content)
                    continue

                if submission_text:
                    st.subheader(f"Submission by {user_name} (User ID: {user_id})")
                    st.text_area("User Submission:", submission_text, height=200)

                    # Perform plagiarism check
                    plagiarism_score = check_plagiarism(submission_text)
                    st.write(f"Plagiarism Score: {plagiarism_score}%")

                    feedback, alignment_grade = get_grading(submission_text, proposed_answer)
                    feedback_key = f"{user_id}_{assignment_id}"

                    st.session_state.feedback_data[feedback_key] = {
                        "Student Name": user_name,
                        "User ID": user_id,
                        "Feedback": feedback,
                        "Grade": alignment_grade,
                        "Plagiarism Score": plagiarism_score
                    }

                    editable_feedback = st.text_area(f"Edit Feedback for {user_name}:", feedback, key=f"feedback_{user_id}")
                    editable_grade = st.number_input(f"Edit Grade for {user_name}:", min_value=0, max_value=1, value=alignment_grade, key=f"grade_{user_id}")

                    st.write("Feedback:")
                    st.write(editable_feedback)
                    st.write("Grade:")
                    st.write(editable_grade)

if st.button("Submit Feedback to Canvas"):
    if not st.session_state.feedback_data:
        st.warning("No feedback available to submit.")
    else:
        for key, entry in st.session_state.feedback_data.items():
            success = submit_feedback(course_id, assignment_id, entry['User ID'], entry['Feedback'], entry['Grade'])
            if success:
                st.success(f"Successfully submitted feedback for {entry['Student Name']} (User ID: {entry['User ID']}).")
            else:
                st.error(f"Failed to submit feedback for {entry['Student Name']} (User ID: {entry['User ID']}).")
