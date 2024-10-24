import streamlit as st
import openai
import requests
import pandas as pd

# Canvas API credentials
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'
BASE_URL = 'https://kepler.instructure.com/api/v1'

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get a specific assignment by its ID
def get_assignment_details(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    # Fetch assignment details by its ID
    assignment_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}"
    response = requests.get(assignment_url, headers=headers)
    
    if response.status_code == 200:
        assignment = response.json()
        return assignment
    else:
        st.error("Failed to fetch assignment details.")
        return None

# Function to get all submissions for a specific assignment
def get_submissions(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    submissions_url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
    response = requests.get(submissions_url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to retrieve submissions.")
        return []

# Function to get grading from OpenAI based on student submissions and proposed answers
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
st.image("header.png", use_column_width=True)
st.title("Kepler College AI-Powered Grading Assistant")

# Course and Assignment ID for the specific assignment
course_id = 2850
assignment_id = 46672

# Fetch specific assignment details
assignment = get_assignment_details(course_id, assignment_id)

if assignment:
    st.subheader(f"Assignment: {assignment['name']}")
    
    # Input for the proposed answer
    proposed_answer = st.text_area("Proposed Answer:", placeholder="Type the answer you expect from the student here...")

    # Dropdown for selecting content type
    content_type = st.selectbox("Select Content Type", options=["Text", "Math (LaTeX)", "Programming (Code)"])
    
    # Submit to grade assignment
    if proposed_answer:
        # Fetch submissions for this assignment
        submissions = get_submissions(course_id, assignment_id)
        
        if submissions:
            # Create a DataFrame to capture results
            results = []

            for submission in submissions:
                # Safely access 'user' and 'body' keys
                student_name = submission.get('user', {}).get('name', 'Unknown')
                student_submission = submission.get('body', 'No Submission')
                turnitin_score = submission.get('turnitin_score', 'N/A')
                
                # Get grading feedback if there is a submission
                if student_submission != 'No Submission':
                    feedback = get_grading(student_submission.strip(), proposed_answer, content_type)

                    # Extract grade (you can add logic here to extract it automatically from feedback)
                    grade = "8/10"  # Replace with actual extraction logic if needed

                    # Clean feedback to remove grades (if necessary)
                    feedback_cleaned = feedback.replace(grade, "").strip()

                    # Append to results
                    results.append({
                        "Student Name": student_name,
                        "Submission": student_submission,
                        "Grade": grade,
                        "Feedback": feedback_cleaned,
                        "Turnitin Score (%)": turnitin_score
                    })

            # Convert results to a DataFrame for display
            df_results = pd.DataFrame(results)
            st.dataframe(df_results)
else:
    st.write("Unable to retrieve assignment details.")
