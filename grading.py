import streamlit as st
import openai
import requests
import re  # For regex pattern matching

# Canvas API credentials
API_TOKEN = '1941~FXJZ2tYC2DTWQr923eFTaXy473rK73A4KrYkT3uVy7WeYV9fyJQ4khH4MAGEH3Tf'
BASE_URL = 'https://kepler.instructure.com/api/v1'

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get course details from Canvas using course code
def get_course_name_and_assignments(course_code):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    # Get courses by their code or ID
    course_url = f"{BASE_URL}/courses"
    response = requests.get(course_url, headers=headers)
    
    if response.status_code == 200:
        courses = response.json()
        course = next((c for c in courses if course_code in c['name'] or course_code in c['course_code']), None)
        
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
    else:
        st.error("Failed to fetch courses from Canvas.")
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

# Helper function to extract grade from feedback (if needed)
def extract_grade(feedback):
    # Regex to find a grade in the format "X/10"
    match = re.search(r'(\d+)/10', feedback)
    return int(match.group(1)) if match else "N/A"

# Helper function to clean feedback
def clean_feedback(feedback):
    # Remove any grades from the feedback text
    return re.sub(r'\d+/10', '', feedback).strip()

# Streamlit UI
st.image("header.png", use_column_width=True)
st.title("Kepler College AI-Powered Grading Assistant")

# Input for course code
course_code = st.text_input("Enter Course Code:")

# Fetch course details
if course_code:
    course_name, assignments = get_course_name_and_assignments(course_code)
    
    if course_name and assignments:
        st.subheader(f"Course: {course_name}")
        
        # Display assignments for selection
        assignment_names = [assignment['name'] for assignment in assignments]
        selected_assignments = st.multiselect("Select Assignments to Grade:", assignment_names)
        
        # Input for the proposed answer
        proposed_answer = st.text_area("Proposed Answer:", placeholder="Type the answer you expect from the student here...")

        # Dropdown for selecting content type
        content_type = st.selectbox("Select Content Type", options=["Text", "Math (LaTeX)", "Programming (Code)"])

        # Submit to grade selected assignments
        if selected_assignments and proposed_answer:
            for selected_assignment in selected_assignments:
                # Mocking student submission (replace with actual data retrieval logic)
                student_submission = "Sample student answer for " + selected_assignment  # Replace with actual student data
                
                # Get grading feedback
                feedback = get_grading(student_submission.strip(), proposed_answer, content_type)
                
                # Extract the grade from feedback
                grade = extract_grade(feedback)

                # Clean feedback to remove any mention of grades
                feedback_cleaned = clean_feedback(feedback)

                # Display results
                st.write(f"**Assignment:** {selected_assignment}")
                st.write(f"**Grade:** {grade}/10")
                st.write(f"**Feedback:** {feedback_cleaned}")
else:
    st.write("Please enter a course code to continue.")
