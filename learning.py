import streamlit as st
import openai
import PyPDF2

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate questions based on lesson content
def generate_questions_from_content(lesson_content):
    prompt = f"Generate 3 questions based on the following lesson content:\n{lesson_content}\n\nMake sure the questions test the student's understanding."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    generated_questions = response['choices'][0]['message']['content'].strip().split("\n")
    return generated_questions

# Function to load PDF content
def load_pdf_content(file):
    reader = PyPDF2.PdfReader(file)
    content = ''
    for page in reader.pages:
        text = page.extract_text()
        if text:
            content += text + "\n"
    return content.strip()

# Function to handle chatbot responses
def chat_with_content(question, lesson_content):
    prompt = f"The following is lesson content:\n{lesson_content}\n\nUser's question: {question}\nAnswer the question based on the content provided."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response['choices'][0]['message']['content'].strip()
    return answer

# Streamlit UI
st.image("header.png", use_column_width=True)
st.title("Kepler College AI-Powered Lesson Assistant")

st.markdown("""
    <div style="background-color: #f0f0f5; padding: 20px; border-radius: 10px;">
        <h3 style="color: #2E86C1;">Welcome to Kepler College's AI-Powered Lesson Assistant</h3>
        <p>Upload your lesson content in <strong>PDF format</strong>, or type the lesson content manually.</p>
    </div>
    """, unsafe_allow_html=True)

# Option 1: Upload PDF file
st.subheader("Option 1: Upload PDF File")
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

# Option 2: Manual text input
st.subheader("Option 2: Paste Specific Lesson Content Here")
manual_content = st.text_area("Paste lesson content here:")

# Load content from PDF or manual input
lesson_content = None
if uploaded_file is not None:
    lesson_content = load_pdf_content(uploaded_file)
    st.subheader("PDF Content")
    st.write(lesson_content)
elif manual_content:
    lesson_content = manual_content

# Chatbot interaction
st.subheader("Ask a Question About the Lesson Content")
if lesson_content:
    user_question = st.text_input("Your question about the lesson content:")
    
    if user_question:
        answer = chat_with_content(user_question, lesson_content)
        st.write("**Answer:**")
        st.write(answer)
else:
    st.write("Please upload a PDF file or enter the lesson content manually.")

# Generate test questions if content is available
if lesson_content:
    if st.button("Generate Test Questions"):
        generated_questions = generate_questions_from_content(lesson_content)
        st.subheader("Generated Test Questions")
        for i, question in enumerate(generated_questions, 1):
            st.write(f"Question {i}: {question}")
