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

# Function to load PDF content
def load_pdf_content(file):
    reader = PyPDF2.PdfReader(file)
    content = ''
    for page in reader.pages:
        content += page.extract_text() + "\n"  # Adding newline for better formatting
    return content

# Streamlit UI
st.title("Chatbot for Lesson Assistance")

# Set up layout with two equal columns
col1, col2 = st.columns(2)

# Upload PDF file and load its content
with col1:
    st.subheader("Lesson PDF")
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if uploaded_file is not None:
        # Load and store the lesson content for chatbot use
        lesson_content = load_pdf_content(uploaded_file)
        
        # Check if content was successfully loaded
        if lesson_content:
            pdf_bytes = uploaded_file.read()
            pdf_base64 = base64.b64encode(pdf_bytes).decode()
            pdf_display = f'<embed src="data:application/pdf;base64,{pdf_base64}" width="100%" height="500" type="application/pdf">'
            st.components.v1.html(pdf_display, height=500)
        else:
            st.write("Unable to read PDF content.")
    else:
        st.write("Please upload a PDF file.")

# Chatbot interaction in the second column
with col2:
    st.subheader("Ask the Chatbot")
    student_input = st.text_input("Ask your question about the lesson:")

    if student_input and 'lesson_content' in locals():
        response = get_chatbot_response(student_input, lesson_content)
        st.markdown('<div style="border: 2px solid #2196F3; padding: 10px; height: 500px; overflow-y: scroll; background-color: #f1f1f1;">{}</div>'.format(response), unsafe_allow_html=True)
