import streamlit as st
import openai
import PyPDF2

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to load content from a PDF file
def load_pdf_content(file):
    content = ''
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
    .chatbox {
        height: 500px;  /* Same size as the PDF content */
        border: 2px solid #2196F3;
        padding: 10px;
        background-color: #f1f1f1;
        overflow-y: scroll;  /* Allow scrolling */
    }
    .pdfbox {
        height: 500px;  /* Same size as the chatbot frame */
        border: 2px solid #FF5733;
        padding: 10px;
        overflow-y: scroll;  /* Allow scrolling */
    }
    </style>
    """, unsafe_allow_html=True)

# Set up layout with two equal columns
col1, col2 = st.columns([1, 1])

# File uploader for the PDF file in the first column
with col1:
    st.subheader("Upload Lesson PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:
        # Load and display the PDF content
        lesson_content = load_pdf_content(uploaded_file)
        st.markdown('<div class="pdfbox">', unsafe_allow_html=True)
        st.write(lesson_content)  # Display PDF text content
        st.markdown('</div>', unsafe_allow_html=True)

# Chatbot interaction in the second column
with col2:
    st.subheader("Ask the Chatbot")
    student_input = st.text_input("Ask your question about the lesson:")

    if student_input and uploaded_file:
        response = get_chatbot_response(student_input, lesson_content)
        st.markdown('<div class="chatbox">{}</div>'.format(response), unsafe_allow_html=True)
