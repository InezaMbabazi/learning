import streamlit as st
import openai
import requests
import pandas as pd

# Canvas API credentials
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'
BASE_URL = 'https://kepler.instructure.com/api/v1'

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get submissions for the assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    # Get submissions for the given assignment
    submissions_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    
    response = requests.get(submissions_url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to retrieve submissions.")
        return []

# Function to provide grading feedback using OpenAI
def get_grading(student_submission, proposed_answer, content_type):
    grading_prompt = f"Evaluate the student's submission based on the proposed answer:\n\n"
    if content_type == "Math (LaTeX)":
        grading_prompt += f"**Proposed Answer (LaTeX)**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Submission (LaTeX)**: {student_submission}\n\n"
        grading_prompt += "Provide feedback on correctness, grade out of 10, and suggest improvements."
    elif content_type == "Programming (Code)":
        grading_prompt += f"**Proposed Code**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Code Submission**: {student_submission}\n\n"
        grading_prompt += "Check logic, efficiency, correctness, and grade out of 10."
    else:
        grading_prompt += f"**Proposed Answer**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Submission**: {student_submission}\n\n"
        grading_prompt += "Provide detailed feedback and grade out of 10. Suggest improvements."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    
    feedback = response['choices'][0]['message']['content']
    return feedback

# Streamlit UI
st.title("Canvas Assignment Grading Automation")

# Course and Assignment ID
course_id = 2624  # Replace with your course ID
assignment_id = 41195  # Replace with your assignment ID

# Proposed Answer Input
proposed_answer = st.text_area("Proposed Answer:", placeholder="Enter the correct answer here...")

# Select content type
content_type = st.selectbox("Content Type:", options=["Text", "Math (LaTeX)", "Programming (Code)"])

# Submit button
if st.button("Grade Submissions"):
    if proposed_answer:
        # Fetch submissions from Canvas
        submissions = get_submissions(course_id, assignment_id)
        
        # If submissions exist, process them
        if submissions:
            # DataFrame to store results
            results = []

            for submission in submissions:
                # Get student name and submission content
                student_name = submission.get('user', {}).get('name', 'Unknown')
                student_submission = submission.get('body', 'No Submission')
                turnitin_score = submission.get('turnitin_score', 'N/A')

                # Grade the submission if available
                if student_submission != 'No Submission':
                    feedback = get_grading(str(student_submission).strip(), proposed_answer, content_type)
                    grade = "8/10"  # You can extract actual grade based on feedback logic
                    feedback_cleaned = feedback.replace(grade, "").strip()

                    # Append the result to the list
                    results.append({
                        "Student Name": student_name,
                        "Submission": student_submission,
                        "Grade": grade,
                        "Feedback": feedback_cleaned,
                        "Turnitin Score (%)": turnitin_score
                    })

            # Display results in a table
            df_results = pd.DataFrame(results)
            st.dataframe(df_results)
        else:
            st.write("No submissions found.")
    else:
        st.error("Please provide the proposed answer.")
