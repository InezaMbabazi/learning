import streamlit as st
import pandas as pd
import os
import openai
import fitz  # PyMuPDF

# Initialize OpenAI API
openai.api_key = st.secrets["openai"]["api_key"]

# Directory to save student progress
RECORDS_DIR = "learning"
if not os.path.exists(RECORDS_DIR):
    os.makedirs(RECORDS_DIR)

# Function to generate questions related to the entire content
def generate_questions(lesson_content):
    prompt = f"""
    Based on the following lesson content, generate 5 multiple-choice questions.
    For each question, include:
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
        correct_answer = None
        for line in lines[5:]:
            if "Correct Answer:" in line:
                correct_answer = line.split(":")[-1].strip().split(" ")[0]
                break
        parsed_questions.append({
            "question": question_text,
            "options": options,
            "correct": correct_answer
        })
    
    return parsed_questions

# Function to extract a relevant excerpt from the lesson content
def extract_relevant_content(lesson_content, question):
    prompt = f"""
    Lesson Content: {lesson_content}
    Question: {question}
    
    Extract the most relevant part of the lesson content that helps to answer this question.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content'].strip()

# Function to extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Streamlit UI
st.title("Interactive Learning Assistant")

# Get student_id from the user
student_id = st.text_input("Enter your student_id:")

if not student_id:
    st.warning("Please enter your student_id to proceed.")
    st.stop()

# Upload or enter lesson content
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
manual_content = st.text_area("Paste lesson content here:")

lesson_content = ""
if uploaded_file is not None:
    lesson_content = extract_text_from_pdf(uploaded_file)
elif manual_content:
    lesson_content = manual_content

if lesson_content:
    # Generate and display questions
    if st.button("Generate Questions"):
        st.session_state["questions"] = generate_questions(lesson_content)

    # Answer questions
    if "questions" in st.session_state:
        user_answers = []
        for idx, question in enumerate(st.session_state["questions"]):
            st.write(f"**Question {idx + 1}:** {question['question']}")
            for option in question["options"]:
                st.write(option)
            
            user_answer = st.radio(f"Your answer for Question {idx + 1}:", ["A", "B", "C", "D"], key=f"q{idx + 1}")
            user_answers.append(user_answer)

        if st.button("Submit Answers"):
            score = 0
            feedback = []
            for idx, question in enumerate(st.session_state["questions"]):
                correct_answer = question["correct"]
                if user_answers[idx] == correct_answer:
                    score += 1
                    feedback.append(f"Question {idx + 1}: Correct!")
                else:
                    relevant_content = extract_relevant_content(lesson_content, question['question'])
                    feedback.append(f"""
                    Question {idx + 1}: Incorrect.
                    Review this part of the content to understand better: 
                    {relevant_content}
                    """)

            st.success(f"Your score: {score}/{len(st.session_state['questions'])}")
            for fb in feedback:
                st.write(fb)
