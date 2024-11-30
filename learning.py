import streamlit as st
import openai
import PyPDF2
import os
import pandas as pd

# Initialize OpenAI API
openai.api_key = st.secrets["openai"]["api_key"]

# Directory for saving student records
RECORDS_DIR = "student_records"
if not os.path.exists(RECORDS_DIR):
    os.makedirs(RECORDS_DIR)


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
        
        # Check if question structure is valid (should have at least 5 lines)
        if len(lines) < 5:
            st.error(f"Unexpected question format: {lines}")
            continue
        
        # Parse the question text and options
        question_text = lines[0].strip()
        options = [line.strip() for line in lines[1:5]]
        
        # Find the correct answer (line starting with "Correct Answer:")
        correct_answer = None
        for line in lines[5:]:
            if "Correct Answer:" in line:
                correct_answer = line.split(":")[-1].strip().split(" ")[0]
                break
        
        if not correct_answer:
            st.error(f"Correct answer not found in: {lines}")
            continue
        
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

# Function to load PDF content
def load_pdf_content(file):
    reader = PyPDF2.PdfReader(file)
    content = ''
    for page in reader.pages:
        text = page.extract_text()
        if text:
            content += text + "\n"
    return content.strip()

# Function to handle chatbot responses
def chat_with_content(user_question, lesson_content):
    prompt = f"""
    The following is lesson content:\n{lesson_content}
    
    User's question: {user_question}
    
    Please provide a detailed, clear answer based on the lesson content.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response['choices'][0]['message']['content'].strip()
    return answer

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
        if student_id in overall_df['Student ID'].values:
            overall_df.loc[overall_df['Student ID'] == student_id, 'Total Score'] += total_score
            overall_df.loc[overall_df['Student ID'] == student_id, 'Total Questions'] += total_questions
        else:
            new_entry = pd.DataFrame({
                'Student ID': [student_id],
                'Total Score': [total_score],
                'Total Questions': [total_questions]
            })
            overall_df = pd.concat([overall_df, new_entry], ignore_index=True)
        overall_df.to_csv(overall_file_path, index=False)
    else:
        new_data = pd.DataFrame({
            'Student ID': [student_id],
            'Total Score': [total_score],
            'Total Questions': [total_questions]
        })
        new_data.to_csv(overall_file_path, index=False)

# Streamlit UI
st.image("header.png", use_column_width=True)
st.title("Kepler College AI-Powered Lesson Assistant")

student_id = st.text_input("Enter your Student ID:", "")
if not student_id:
    st.warning("Please enter your Student ID to proceed.")
    st.stop()

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
manual_content = st.text_area("Paste lesson content here:")
lesson_content = load_pdf_content(uploaded_file) if uploaded_file else manual_content

if lesson_content:
    st.subheader("Chat with the Content")
    user_question = st.text_input("Ask a question about the lesson content:")
    if user_question:
        st.write(chat_with_content(user_question, lesson_content))

    if st.button("Generate Test Questions"):
        st.session_state["questions"] = generate_mc_questions(lesson_content)

    mastery_score = 0.8  # Define mastery score (80% correct)
    is_mastered = False

    while not is_mastered:
        if "questions" in st.session_state:
            user_answers = []
            progress_data = []
            for idx, question in enumerate(st.session_state["questions"]):
                st.write(f"**Question {idx + 1}:** {question['question']}")
                for option in question["options"]:
                    st.write(option)
                user_answer = st.radio(f"Your answer for Question {idx + 1}:", ["A", "B", "C", "D"], key=f"q{idx + 1}")
                user_answers.append(user_answer)

            if st.button("Submit Answers"):
                score = 0
                for idx, question in enumerate(st.session_state["questions"]):
                    feedback = generate_feedback(lesson_content, question["question"], user_answers[idx], question["correct"])
                    progress_data.append({
                        "Student ID": student_id,
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
                        st.write(f"Feedback: {feedback}")

                save_student_progress(student_id, progress_data)
                update_overall_performance(student_id, score, len(st.session_state["questions"]))
                st.write(f"**Your Score:** {score}/{len(st.session_state['questions'])}")
                
                # Check if mastery is achieved
                if score / len(st.session_state["questions"]) >= mastery_score:
                    st.success("Congratulations! You have mastered the content.")
                    is_mastered = True
                else:
                    st.warning("You did not meet the mastery threshold. Please review the content and retake the test.")
                    if st.button("Retake Test"):
                        st.session_state["questions"] = generate_mc_questions(lesson_content)
                        continue
