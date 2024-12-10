import streamlit as st
import pandas as pd
import os
import openai
import fitz  # PyMuPDF
from io import StringIO

# Initialize OpenAI API
openai.api_key = st.secrets["openai"]["api_key"]

# Directory to save student records
RECORDS_DIR = "learning"
if not os.path.exists(RECORDS_DIR):
    os.makedirs(RECORDS_DIR)

# Load students from the CSV file
def load_students():
    student_file_path = os.path.join(RECORDS_DIR, 'students.csv')
    if os.path.exists(student_file_path):
        return pd.read_csv(student_file_path)
    else:
        return pd.DataFrame(columns=["student_id", "First Name", "Last Name", "Email"])

# Function to generate multiple-choice questions based on lesson content
def generate_mc_questions(lesson_content):
    prompt = f"""
    Based on the following lesson content, generate 3 multiple-choice questions. 
    For each question, provide:
    1. The question text.
    2. Four options (A, B, C, D).
    3. Mark the correct answer with the format: "Correct Answer: <Option Letter>". 
    
    Lesson Content: {lesson_content}
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    questions_raw = response['choices'][0]['message']['content'].strip().split("\n\n")
    
    parsed_questions = []
    for question_raw in questions_raw:
        lines = question_raw.strip().split("\n")
        question_text = lines[0].strip()
        options = [line.strip() for line in lines[1:5]]
        correct_answer = [line.split(":")[-1].strip() for line in lines if "Correct Answer:" in line][0]
        parsed_questions.append({
            "question": question_text,
            "options": options,
            "correct": correct_answer
        })
    
    return parsed_questions

# Function to provide feedback and suggest additional content
def generate_feedback(lesson_content, question, user_answer, correct_answer):
    feedback_prompt = f"""
    Lesson Content: {lesson_content}
    Question: {question}
    User's Answer: {user_answer}
    Correct Answer: {correct_answer}
    Provide feedback and, if the answer is incorrect, recommend specific content to review.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": feedback_prompt}]
        )
        feedback = response['choices'][0]['message']['content'].strip()
    except Exception as e:
        feedback = f"An error occurred while generating feedback: {e}"
    return feedback

# Function to save student progress
def save_student_progress(student_id, data):
    file_path = os.path.join(RECORDS_DIR, f"{student_id}_progress.csv")
    df = pd.DataFrame(data)
    if os.path.exists(file_path):
        df_existing = pd.read_csv(file_path)
        df_combined = pd.concat([df_existing, df], ignore_index=True)
        df_combined.to_csv(file_path, index=False)
    else:
        df.to_csv(file_path, index=False)

# Streamlit UI
st.title("AI-Powered Student Assessment System")

# Load students
students_df = load_students()

# Get student_id from the user
student_id = st.text_input("Enter your student ID:")
if not student_id:
    st.warning("Please enter your student ID to continue.")
    st.stop()

# Check if student exists
if student_id not in students_df['student_id'].values:
    st.warning("Student not found. Please register below.")
    first_name = st.text_input("First Name:")
    last_name = st.text_input("Last Name:")
    email = st.text_input("Email:")
    if st.button("Register"):
        if first_name and last_name and email:
            new_student = pd.DataFrame([{"student_id": student_id, "First Name": first_name, "Last Name": last_name, "Email": email}])
            students_df = pd.concat([students_df, new_student], ignore_index=True)
            students_df.to_csv(os.path.join(RECORDS_DIR, 'students.csv'), index=False)
            st.success("Registration successful. Please proceed.")
        else:
            st.error("All fields are required.")
    st.stop()

# Upload or enter lesson content
uploaded_file = st.file_uploader("Upload Lesson Content (PDF)", type="pdf")
manual_content = st.text_area("Or paste lesson content here:")
lesson_content = extract_text_from_pdf(uploaded_file) if uploaded_file else manual_content

if lesson_content:
    if "questions" not in st.session_state:
        st.session_state["questions"] = []
        st.session_state["user_progress"] = []

    if not st.session_state["questions"]:
        st.session_state["questions"] = generate_mc_questions(lesson_content)

    for idx, question in enumerate(st.session_state["questions"]):
        st.write(f"**Question {idx + 1}:** {question['question']}")
        for option in question["options"]:
            st.write(option)
        user_answer = st.radio(f"Your answer for Question {idx + 1}:", ["A", "B", "C", "D"], key=f"q{idx}")
        if st.button(f"Submit Answer for Question {idx + 1}", key=f"submit_{idx}"):
            correct_answer = question["correct"]
            feedback = generate_feedback(lesson_content, question["question"], user_answer, correct_answer)
            st.session_state["user_progress"].append({
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "feedback": feedback
            })
            if user_answer != correct_answer:
                st.write("Incorrect. Review the following content:")
                st.write(feedback)
            else:
                st.write("Correct!")
    st.write("Continue practicing until you master the material.")
