import streamlit as st
import openai
import PyPDF2

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate questions based on lesson content
def generate_questions_from_content(lesson_content):
    prompt = f"Generate 3 detailed questions based on the following lesson content:\n{lesson_content}\n\nPlease ensure the questions are relevant and test the student's understanding."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the generated questions
    generated_questions = response['choices'][0]['message']['content'].strip().split("\n")
    return generated_questions

# Function to load PDF content
def load_pdf_content(file):
    reader = PyPDF2.PdfReader(file)
    content = ''
    for page in reader.pages:
        text = page.extract_text()
        if text:  # Only append if text is not None
            content += text + "\n"  # Adding newline for better formatting
    return content.strip()  # Return stripped content

# Function to get grading from OpenAI based on student responses
def get_grading(student_answers, generated_questions, lesson_content):
    grading_prompt = f"Lesson Content: {lesson_content}\n\nHere are the student's answers and the questions:\n"
    for i, (question, answer) in enumerate(zip(generated_questions, student_answers), 1):
        grading_prompt += f"Question {i}: {question}\nStudent's Answer: {answer}\n"

    grading_prompt += "\nPlease grade the student's answers and provide feedback for each."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": grading_prompt}
        ]
    )
    
    feedback = response['choices'][0]['message']['content']
    return feedback

# Streamlit UI
st.title("Chatbot for Lesson Assistance with AI-Generated Questions")

# Apply custom CSS to style the layout
st.markdown("""
    <style>
    .chatbox {
        border: 2px solid #2196F3;
        padding: 10px;
        height: 200px; /* Height for chatbot response */
        overflow-y: scroll;
        background-color: #f1f1f1;
    }
    .pdf-area {
        border: 2px solid #2196F3;
        padding: 10px;
        height: 300px; /* Fixed height for PDF content */
        overflow-y: auto;
        background-color: #f9f9f9;
        margin-bottom: 20px; /* Space between PDF and chatbot */
    }
    </style>
    """, unsafe_allow
