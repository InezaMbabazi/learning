import streamlit as st
import openai

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

# Apply custom CSS to style the borders and layout
st.markdown("""
    <style>
    .chatbox {
        height: 500px;  /* Same size as the PDF content */
        border: 2px solid #2196F3;
        padding: 10px;
        background-color: #f1f1f1;
    }
    .pdfbox {
        height: 500px;  /* Same size as the chatbot frame */
        border: 2px solid #FF5733;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Set up layout with two equal columns
col1, col2 = st.columns([1, 1])

# Display the PDF file in the first column using an iframe
with col1:
    st.subheader("Lesson PDF")
    # Link to the raw PDF file on GitHub
    pdf_url = 'https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/main/note2.pdf'
    pdf_display = f'<iframe src="{pdf_url}" width="100%" height="500"></iframe>'
    st.markdown(f'<div class="pdfbox">{pdf_display}</div>', unsafe_allow_html=True)

# Chatbot interaction in the second column
with col2:
    st.subheader("Ask the Chatbot")
    student_input = st.text_input("Ask your question about the lesson:")

    if student_input:
        response = get_chatbot_response(student_input, "Lesson content from PDF")
        st.markdown('<div class="chatbox">{}</div>'.format(response), unsafe_allow_html=True)
