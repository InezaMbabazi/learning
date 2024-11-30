import streamlit as st
import pandas as pd
import os
import openai
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
        st.error("Student records not found.")
        return pd.DataFrame()

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
        
        # Parse the question text and options
        question_text = lines[0].strip()
        options = [line.strip() for line in lines[1:5]]
        
        # Find the correct answer (line starting with "Correct Answer:")
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

# Function to generate personalized feedback
def generate_feedback(lesson_content, question, user_answer, correct_answer):
    feedback_prompt = f"""
    Lesson Content: {lesson_content}
    
    Question: {question}
    User's Answer: {user_answer}
    Correct Answer: {correct_answer}
    
    Provide feedback for the user based on their answer. If the user's answer is incorrect, suggest specific parts of the lesson content they should review to better understand the topic.
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

# Function to update overall performance
def update_overall_performance(student_id, total_score, total_questions):
    overall_file_path = os.path.join(RECORDS_DIR, "overall_performance.csv")
    if os.path.exists(overall_file_path):
        overall_df = pd.read_csv(overall_file_path)
        if student_id in overall_df['student_id'].values:
            overall_df.loc[overall_df['student_id'] == student_id, 'Total Score'] += total_score
            overall_df.loc[overall_df['student_id'] == student_id, 'Total Questions'] += total_questions
        else:
            new_entry = pd.DataFrame({
                'student_id': [student_id],
                'Total Score': [total_score],
                'Total Questions': [total_questions]
            })
            overall_df = pd.concat([overall_df, new_entry], ignore_index=True)
        overall_df.to_csv(overall_file_path, index=False)
    else:
        new_data = pd.DataFrame({
            'student_id': [student_id],
            'Total Score': [total_score],
            'Total Questions': [total_questions]
        })
        new_data.to_csv(overall_file_path, index=False)

# Streamlit UI
st.title("Kepler College AI-Powered Lesson Assistant")

# Load students from the CSV file
students_df = load_students()

# Normalize column names to avoid any case or extra whitespace issues
students_df.columns = students_df.columns.str.strip().str.lower()

# Ensure student_id is treated as a string
students_df['student_id'] = students_df['student_id'].astype(str)

# Get student_id from the user
student_id = st.text_input("Enter your student_id:")

if not student_id:
    st.warning("Please enter your student_id to proceed.")
    st.stop()

# Verify the student_id exists in the directory
if student_id not in students_df['student_id'].values:
    st.error("Invalid student_id. Please check and enter a valid ID.")
    st.stop()

# Upload or enter lesson content
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
manual_content = st.text_area("Paste lesson content here:")

lesson_content = ""
if uploaded_file is not None:
    lesson_content = uploaded_file.read().decode("utf-8")
elif manual_content:
    lesson_content = manual_content

if lesson_content:
    # Ask the user a question
    user_question = st.text_input("Ask a question about the lesson content:")
    
    if user_question:
        prompt = f"Lesson content: {lesson_content}\n\nUser's question: {user_question}\n\nProvide a clear answer."
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        st.write(response.choices[0].text.strip())

    # Generate and display multiple-choice questions
    if st.button("Generate Test Questions"):
        st.session_state["questions"] = generate_mc_questions(lesson_content)

    # Answer questions
    if "questions" in st.session_state:
        user_answers = []
        for idx, question in enumerate(st.session_state["questions"]):
            st.write(f"**Question {idx + 1}:** {question['question']}")
            for option in question["options"]:
                st.write(option)
            
            # Capture user answers
            user_answer = st.radio(f"Your answer for Question {idx + 1}:", ["A", "B", "C", "D"], key=f"q{idx + 1}")
            user_answers.append(user_answer)

        if st.button("Submit Answers"):
            score = 0
            progress_data = []
            for idx, question in enumerate(st.session_state["questions"]):
                feedback = generate_feedback(lesson_content, question["question"], user_answers[idx], question["correct"])
                progress_data.append({
                    "student_id": student_id,
                    "Question": question["question"],
                    "User Answer": user_answers[idx],
                    "Correct Answer": question["correct"],
                    "Feedback": feedback
                })
                if user_answers[idx] == question["correct"]:
                    st.success(f"Question {idx + 1}: Correct!")
                    score += 1
                else:
                    st.error(f"Question {idx + 1}: Incorrect. Correct Answer: {question['correct']}")

            # Save progress
            save_student_progress(student_id, progress_data)

            # Update overall performance
            update_overall_performance(student_id, score, len(st.session_state["questions"]))

            mastery_score = score / len(st.session_state["questions"])
            if mastery_score >= 0.8:
                st.success("You have mastered this lesson!")
            else:
                st.warning("You need more practice. Try again.")
else:
    st.warning("Please upload or enter lesson content.")
