import streamlit as st
import openai
import PyPDF2

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate questions based on lesson content
def generate_questions_from_content(lesson_content):
    prompt = f"Generate 3 questions based on the following lesson content:\n{lesson_content}\n\nEnsure the questions test understanding comprehensively."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    generated_questions = response['choices'][0]['message']['content'].strip().split("\n")
    return generated_questions

# Function to assess user answers
def assess_user_answers(questions, user_answers, lesson_content):
    prompt = f"""
    The following are the lesson content, questions, and user answers:
    Lesson Content: {lesson_content}
    Questions: {questions}
    User Answers: {user_answers}
    
    Provide an assessment of the user's answers, identify weaknesses, and suggest areas for improvement.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    assessment = response['choices'][0]['message']['content'].strip()
    return assessment

# Function to fetch targeted content based on weaknesses
def fetch_targeted_content(weaknesses, lesson_content):
    prompt = f"""
    Based on the user's weaknesses: {weaknesses}, generate a focused summary or explanation to help them improve. Use the following lesson content for reference:
    {lesson_content}
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    targeted_content = response['choices'][0]['message']['content'].strip()
    return targeted_content

# Function to load PDF content
def load_pdf_content(file):
    reader = PyPDF2.PdfReader(file)
    content = ''
    for page in reader.pages:
        text = page.extract_text()
        if text:
            content += text + "\n"
    return content.strip()

# Streamlit UI
st.image("header.png", use_column_width=True)
st.title("Kepler College AI-Powered Adaptive Learning Assistant")

st.markdown("""
    <div style="background-color: #f0f0f5; padding: 20px; border-radius: 10px;">
        <h3 style="color: #2E86C1;">Welcome to Kepler College's AI-Powered Adaptive Learning Assistant</h3>
        <p>Upload your lesson content in <strong>PDF format</strong>, or type it manually. Assess your understanding, address weaknesses, and improve iteratively.</p>
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

# Adaptive assessment process
if lesson_content:
    st.subheader("Adaptive Learning Mode")
    
    if st.button("Start Assessment"):
        generated_questions = generate_questions_from_content(lesson_content)
        st.subheader("Generated Questions")
        user_answers = []
        for i, question in enumerate(generated_questions, 1):
            user_answer = st.text_input(f"Question {i}: {question}", key=f"q{i}")
            user_answers.append(user_answer)
        
        if st.button("Submit Answers"):
            assessment = assess_user_answers(generated_questions, user_answers, lesson_content)
            st.subheader("Assessment and Feedback")
            st.write(assessment)
            
            # Extract weaknesses from the assessment
            weaknesses = "Identify weaknesses based on the feedback provided."
            targeted_content = fetch_targeted_content(weaknesses, lesson_content)
            
            st.subheader("Targeted Content for Improvement")
            st.write(targeted_content)
            
            st.write("Reassess after reviewing the content to track improvement.")
else:
    st.write("Please upload a PDF file or enter the lesson content manually.")
