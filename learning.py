import streamlit as st
import openai
import PyPDF2

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

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

# Set up layout with two columns
col1, col2 = st.columns([2, 1])  # Adjust the ratio as needed (2:1 gives more space to the lesson content)

# Load the PDF file and its content
file_path = 'note2.pdf'  # Ensure this file is in your GitHub repo and deployed
lesson_content = load_pdf_content(file_path)

# Display PDF content in the first column
with col1:
    st.subheader("Lesson Content")
    st.write(lesson_content)  # You can add more formatting or allow scrolling if needed

# Chatbot interaction in the second column
with col2:
    st.subheader("Ask the Chatbot")
    student_input = st.text_input("Ask your question about the lesson:")

    if student_input:
        response = get_chatbot_response(student_input, lesson_content)
        st.write("Chatbot Response:", response)
