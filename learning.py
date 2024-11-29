import streamlit as st
import openai
import pandas as pd
import os

# Initialize OpenAI API
openai.api_key = st.secrets["openai"]["api_key"]

# Define file paths
STUDENT_DATA_FILE = "student_data.csv"
CHAT_HISTORY_FILE = "chat_history.csv"
TEST_RESULTS_FILE = "test_results.csv"

# Initialize CSV files with headers if they don't exist
def initialize_csv(file_path, columns):
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file_path, index=False)

initialize_csv(STUDENT_DATA_FILE, ["student_id", "content_id", "status"])
initialize_csv(CHAT_HISTORY_FILE, ["student_id", "content_id", "user_question", "ai_response"])
initialize_csv(TEST_RESULTS_FILE, ["student_id", "content_id", "question", "student_answer", "correct_answer", "is_correct"])

# Function to generate multiple-choice questions
def generate_mc_questions(lesson_content):
    prompt = f"""
    Generate 3 multiple-choice questions from the following lesson content:
    {lesson_content}

    Format:
    Question: [Question text]
    a) Option 1
    b) Option 2
    c) Option 3
    d) Option 4
    Correct: [Correct option]
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    questions = response['choices'][0]['message']['content'].strip().split("\n\n")
    mc_questions = []
    for q in questions:
        lines = q.split("\n")
        question = lines[0].split("Question:")[-1].strip()
        options = [line.strip() for line in lines[1:5]]
        correct_answer = lines[5].split(":")[-1].strip()
        mc_questions.append({"question": question, "options": options, "correct": correct_answer})
    return mc_questions

# Function to save chat history
def save_chat_history(student_id, content_id, user_question, ai_response):
    new_data = {"student_id": student_id, "content_id": content_id, "user_question": user_question, "ai_response": ai_response}
    df = pd.read_csv(CHAT_HISTORY_FILE)
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(CHAT_HISTORY_FILE, index=False)

# Function to save test results
def save_test_results(student_id, content_id, question, student_answer, correct_answer):
    is_correct = student_answer == correct_answer
    new_data = {
        "student_id": student_id,
        "content_id": content_id,
        "question": question,
        "student_answer": student_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct
    }
    df = pd.read_csv(TEST_RESULTS_FILE)
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(TEST_RESULTS_FILE, index=False)

# Function to provide feedback and recommend learning content
def generate_feedback(lesson_content, incorrect_questions):
    prompt = f"""
    Based on the following lesson content:
    {lesson_content}

    Provide detailed explanations for the following questions the student answered incorrectly:
    {incorrect_questions}
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content'].strip()

# Streamlit UI
st.title("AI-Powered Learning Assistant")

# Student information
student_id = st.text_input("Enter your student ID:")
content_id = st.text_input("Enter the content ID (topic):")

# Upload or input lesson content
st.subheader("Upload Lesson Content")
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
manual_content = st.text_area("Or paste the lesson content here:")

# Load lesson content
lesson_content = None
if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    lesson_content = content
    st.write(content)
elif manual_content:
    lesson_content = manual_content

if lesson_content and student_id and content_id:
    # Chatbot interaction
    st.subheader("Chat with the Lesson Content")
    user_question = st.text_input("Ask a question about the content:")
    if st.button("Submit Question"):
        if user_question:
            prompt = f"The following is lesson content:\n{lesson_content}\n\nUser's question: {user_question}\nAnswer the question based on the content provided."
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            ai_response = response['choices'][0]['message']['content'].strip()
            st.write("**Answer:**", ai_response)
            save_chat_history(student_id, content_id, user_question, ai_response)

    # Generate and display test questions
    st.subheader("Test Your Knowledge")
    if st.button("Generate Test Questions"):
        questions = generate_mc_questions(lesson_content)
        incorrect_questions = []
        for idx, q in enumerate(questions):
            st.write(f"**Question {idx + 1}:** {q['question']}")
            for opt in q['options']:
                st.write(opt)
            student_answer = st.radio(f"Your answer for Question {idx + 1}:", ["a", "b", "c", "d"], key=f"q{idx}")
            if st.button(f"Submit Answer for Question {idx + 1}", key=f"submit_q{idx}"):
                save_test_results(student_id, content_id, q['question'], student_answer, q['correct'])
                if student_answer != q['correct']:
                    incorrect_questions.append(q['question'])

        # Provide feedback
        if incorrect_questions:
            st.subheader("Feedback and Suggested Content")
            feedback = generate_feedback(lesson_content, incorrect_questions)
            st.write(feedback)
else:
    st.write("Please fill in all required fields to proceed.")
