import streamlit as st
import openai
import fitz  # PyMuPDF

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to extract content from a PDF file and return it as HTML
def load_pdf_content(file):
    doc = fitz.open(file)
    content = ''
    for page in doc:
        content += page.get_text("html")  # Extract text as HTML
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

# Upload PDF file
uploaded_file = st.file_uploader("Upload your PDF file", type=["pdf"])

# Check if a PDF file has been uploaded
if uploaded_file:
    # Load the content of the PDF
    lesson_content = load_pdf_content(uploaded_file)

    # Display the PDF content
    st.subheader("Lesson PDF")
    st.markdown(lesson_content, unsafe_allow_html=True)  # Display as HTML

    # Chatbot interaction
    st.subheader("Ask the Chatbot")
    student_input = st.text_input("Ask your question about the lesson:")

    if student_input:
        response = get_chatbot_response(student_input, lesson_content)
        st.markdown('<div class="chatbox">{}</div>'.format(response), unsafe_allow_html=True)

# Apply custom CSS for chatbox styling
st.markdown("""
    <style>
    .chatbox {
        height: 200px;  /* Adjust height as needed */
        border: 2px solid #2196F3;
        padding: 10px;
        background-color: #f1f1f1;
    }
    </style>
    """, unsafe_allow_html=True)
