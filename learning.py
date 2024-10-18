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

# Apply custom CSS to style the borders and layout
st.markdown("""
    <style>
    .scrollable-content {
        height: 300px;
        border: 2px solid #4CAF50;
        padding: 10px;
        overflow-y: scroll;
        background-color: #f9f9f9;
    }
    .chatbox {
        height: 300px;
        border: 2px solid #2196F3;
        padding: 10px;
        background-color: #f1f1f1;
    }
    </style>
    """, unsafe_allow_html=True)

# Set up layout with two equal columns
col1, col2 = st.columns([1, 1])

# Load the PDF file and its content
file_path = 'note2.pdf'  # Ensure this file is in your GitHub repo and deployed
lesson_content = load_pdf_content(file_path)

# Display PDF content in the first column (Scrollable and Styled)
with col1:
    st.subheader("Lesson Content")
    st.markdown('<div class="scrollable-content">{}</div>'.format(lesson_content.replace("\n", "<br>")), unsafe_allow_html=True)

# Chatbot interaction in the second column (Same Size and Styled)
with col2:
    st.subheader("Ask the Chatbot")
    student_input = st.text_input("Ask your question about the lesson:")

    if student_input:
        response = get_chatbot_response(student_input, lesson_content)
        st.markdown('<div class="chatbox">{}</div>'.format(response), unsafe_allow_html=True)
