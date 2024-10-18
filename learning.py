import streamlit as st
import openai
import PyPDF2
import docx

# Function to load content from a PDF file
def load_pdf_content(file_path):
    content = ''
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            content += page.extract_text()
    return content

# Function to get response from OpenAI based on student input
def get_chatbot_response(student_input, lesson_content):
    context = f"Lesson Content: {lesson_content}\n\nStudent Query: {student_input}"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": context}
        ]
    )
    
    return response['choices'][0]['message']['content']

# Streamlit UI
st.title("Chatbot for Lesson Assistance")

# Upload PDF file and load its content
file_path = 'note2.pdf'  # Ensure this file is in your GitHub repo and deployed

lesson_content = load_pdf_content(file_path)
st.write("PDF content has been loaded.")

# Student input for asking a question
student_input = st.text_input("Ask your question about the lesson:")

if student_input:
    response = get_chatbot_response(student_input, lesson_content)
    st.write("Chatbot Response:", response)
