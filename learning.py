import streamlit as st 
import openai
import PyPDF2
import base64

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
        height: 300px; /* Fixed height for PDF content */
        overflow-y: auto;
        background-color: #f9f9f9;
        margin-bottom: 20px; /* Space between PDF and chatbot */
    }
    </style>
    """, unsafe_allow_html=True)

# Upload PDF file and load its content
st.subheader("Upload PDF File")
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    # Read the PDF content
    pdf_bytes = uploaded_file.read()
    
    # Display the PDF in its original format
    pdf_base64 = base64.b64encode(pdf_bytes).decode()
    pdf_display = f'<embed src="data:application/pdf;base64,{pdf_base64}" width="100%" height="300" type="application/pdf">'
    st.components.v1.html(pdf_display, height=300)

    # Extract text for chatbot use
    lesson_content = ''
    reader = PyPDF2.PdfReader(uploaded_file)
    for page in reader.pages:
        text = page.extract_text()
        if text:  # Only append if text is not None
            lesson_content += text + "\n"  # Adding newline for better formatting
    lesson_content = lesson_content.strip()  # Return stripped content

    # Display the extracted text content in a selectable area
    st.markdown('<div class="pdf-area"><pre>{}</pre></div>'.format(lesson_content), unsafe_allow_html=True)

    # Chatbot interaction section
    st.subheader("Chatbot Interaction")
    student_input = st.text_input("Ask your question about the lesson:")

    if student_input:
        response = get_chatbot_response(student_input, lesson_content)
        st.markdown('<div class="chatbox">{}</div>'.format(response), unsafe_allow_html=True)
else:
    st.write("Please upload a PDF file.")
