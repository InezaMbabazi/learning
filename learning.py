import streamlit as st
import pandas as pd
import openai
import PyPDF2
import os

# Initialize OpenAI API
openai.api_key = st.secrets["openai"]["api_key"]

# CSV file paths
STUDENT_DATA_FILE = "student_progress.csv"
CHAT_HISTORY_FILE = "chat_history.csv"

# Ensure CSV files exist
if not os.path.exists(STUDENT_DATA_FILE):
    pd.DataFrame(columns=["student_id", "content_id", "question_id", "question", "answer", "correct_answer", "feedback", "score"]).to_csv(STUDENT_DATA_FILE, index=False)

if not os.path.exists(CHAT_HISTORY_FILE):
    pd.DataFrame(columns=["student_id", "content_id", "user_question", "ai_response"]).to_csv(CHAT_HISTORY_FILE, index=False)

# Function to save student progress
def save_student_progress(student_id, content_id, question_id, question, answer, correct_answer, feedback, score):
    new_data = {
        "student_id": student_id,
        "content_id": content_id,
        "question_id": question_id,
        "question": question,
        "answer": answer,
        "correct_answer": correct_answer,
        "feedback": feedback,
        "score": score,
    }
    df = pd.read_csv(STUDENT_DATA_FILE)
    df = df.append(new_data, ignore_index=True)
    df.to_csv(STUDENT_DATA_FILE, index=False)

# Function to load student progress
def load_student_progress(student_id, content_id):
    df = pd.read_csv(STUDENT_DATA_FILE)
    return df[(df["student_id"] == student_id) & (df["content_id"] == content_id)]

# Function to save chat history
def save_chat_history(student_id, content_id, user_question, ai_response):
    new_data = {
        "student_id": student_id,
        "content_id": content_id,
        "user_question": user_question,
        "ai_response": ai_response,
    }
    df = pd.read_csv(CHAT_HISTORY_FILE)
    df = df.append(new_data, ignore_index=True)
    df.to_csv(CHAT_HISTORY_FILE, index=False)

# Function to load chat history
def load_chat_history(student_id, content_id):
    df = pd.read_csv(CHAT_HISTORY_FILE)
    return df[(df["student_id"] == student_id) & (df["content_id"] == content_id)]

# Function to chat with content
def chat_with_content(user_question, lesson_content):
    prompt = f"""
    Lesson Content: {lesson_content}
    
    User's question: {user_question}
    
    Provide a clear answer based on the lesson content.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content'].strip()

# Streamlit UI
st.title("AI-Powered Lesson Assistant with Memory (CSV Storage)")
st.subheader("Welcome back! Let's continue your learning journey.")

# Student login
student_id = st.text_input("Enter your Student ID (e.g., email):")
content_id = st.text_input("Enter Content ID (e.g., Lesson Name):")

if student_id and content_id:
    st.write(f"Welcome, **{student_id}**! Your progress will be saved under **{content_id}**.")
    
    # Load lesson content
    st.subheader("Upload Lesson Content")
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    manual_content = st.text_area("Or paste the lesson content here:")
    
    lesson_content = None
    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        lesson_content = "".join(page.extract_text() for page in reader.pages)
    elif manual_content:
        lesson_content = manual_content
    
    if lesson_content:
        st.subheader("Chat with the Lesson")
        user_question = st.text_input("Ask a question about the content:")
        if user_question:
            ai_response = chat_with_content(user_question, lesson_content)
            st.write("**AI Response:**")
            st.write(ai_response)
            save_chat_history(student_id, content_id, user_question, ai_response)
        
        # Display chat history
        if st.button("Show Previous Questions"):
            chat_history = load_chat_history(student_id, content_id)
            if not chat_history.empty:
                st.write("**Chat History:**")
                for _, row in chat_history.iterrows():
                    st.write(f"**Q:** {row['user_question']}")
                    st.write(f"**A:** {row['ai_response']}")
            else:
                st.write("No chat history found.")
    
        # Generate test questions
        if st.button("Generate Test Questions"):
            # Call the question generation function (define your MC question logic here)
            st.write("Feature coming soon: Test yourself!")
    
    # Load progress
    st.subheader("Your Progress")
    student_progress = load_student_progress(student_id, content_id)
    if not student_progress.empty:
        for _, record in student_progress.iterrows():
            st.write(f"Question: {record['question']}")
            st.write(f"Your Answer: {record['answer']} | Correct Answer: {record['correct_answer']}")
            st.write(f"Feedback: {record['feedback']}")
            st.write(f"Score: {record['score']}")
    else:
        st.write("No progress recorded yet.")
