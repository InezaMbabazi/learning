import streamlit as st
import openai
import os
import tempfile

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

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
        height: 500px; /* Height for PDF content */
        overflow-y: auto;
        background-color: #f9f9f9;
        margin-bottom: 20px; /* Space between PDF and chatbot */
    }
    </style>
    """, unsafe_allow_html=True)

# Upload PDF file
st.subheader("Upload PDF File")
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    # Save the uploaded PDF temporarily using tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_pdf_path = temp_file.name

    # Display the saved PDF in an iframe
    pdf_display = f'<iframe src="file://{temp_pdf_path}" width="100%" height="500"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

    # Placeholder content for chatbot (you can extract text from PDF if needed)
    lesson_content = "Lesson content from the PDF."

    # Chatbot interaction section
    st.subheader("Chatbot Interaction")
    student_input = st.text_input("Ask your question about the lesson:")

    if student_input:
        response = get_chatbot_response(student_input, lesson_content)
        st.markdown('<div class="chatbox">{}</div>'.format(response), unsafe_allow_html=True)
else:
    st.write("Please upload a PDF file.")
