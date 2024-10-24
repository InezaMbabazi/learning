import streamlit as st
import openai
import requests
import pandas as pd

# Canvas API credentials
API_TOKEN = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'
BASE_URL = 'https://kepler.instructure.com/api/v1'

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get all available courses from Canvas
def get_all_courses():
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    course_url = f"{BASE_URL}/courses"
    response = requests.get(course_url, headers=headers)
    
    if response.status_code == 200:
        courses = response.json()
        return courses
    else:
        st.error("Failed to fetch courses from Canvas.")
        return []

# Function to get course by code and its assignments
def get_course_by_code(course_code):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    # Get all courses
    courses = get_all_courses()
    course = next((c for c in courses if str(course_code) in c['course_code']), None)
    
    if course:
        course_id = course['id']
        course_name = course['name']
        
        # Fetch assignments for this course
        assignments_url = f"{BASE_URL}/courses/{course_id}/assignments"
        assignments_response = requests.get(assignments_url, headers=headers)
        
        if assignments_response.status_code == 200:
            assignments = assignments_response.json()
            return course_name, assignments
        else:
            st.error("Failed to retrieve assignments.")
            return None, []
    else:
        st.error("Course code not found.")
        return None, []

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

# Fixed course code
course_code = '2850'

# Fetch course details
course_name, assignments = get_course_by_code(course_code)

if course_name and assignments:
    st.subheader(f"Course: {course_name}")
    
    # Display assignments for selection
    assignment_names = [assignment['name'] for assignment in assignments]
    selected_assignment = st.selectbox("Select Assignment to Grade:", assignment_names)
    
    # Input for the proposed answer
    proposed_answer = st.text_area("Proposed Answer:", placeholder="Type the answer you expect from the student here...")

    # Dropdown for selecting content type
    content_type = st.selectbox("Select Content Type", options=["Text", "Math (LaTeX)", "Programming (Code)"])
    
    # Submit to grade selected assignment
    if selected_assignment and proposed_answer:
        # Mock student submissions (replace with actual data retrieval logic from Canvas or a database)
        student_submissions = [
            {"name": "Student A", "submission": "Sample submission A", "turnitin": 12},
            {"name": "Student B", "submission": "Sample submission B", "turnitin": 28},
            {"name": "Student C", "submission": "Sample submission C", "turnitin": 5},
        ]
        
        # Create a DataFrame to capture results
        results = []

        for student in student_submissions:
            student_submission = student['submission']
            turnitin_score = student['turnitin']
            
            # Get grading feedback
            feedback = get_grading(student_submission.strip(), proposed_answer, content_type)

            # Extract grade (you can add logic here to extract it automatically from feedback)
            grade = "8/10"  # Replace with actual extraction logic if needed
            
            # Clean feedback to remove grades (if necessary)
            feedback_cleaned = feedback.replace(grade, "").strip()

            # Append to results
            results.append({
                "Student Name": student['name'],
                "Submission": student_submission,
                "Grade": grade,
                "Feedback": feedback_cleaned,
                "Turnitin Score (%)": turnitin_score
            })
        
        # Convert results to a DataFrame for display
        df_results = pd.DataFrame(results)
        st.dataframe(df_results)
else:
    st.write("Course code 2850 not found.")
