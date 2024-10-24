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

# Function to grade student answers and provide feedback using OpenAI
def get_grading(student_answers, generated_questions, lesson_content):
    feedback = []
    
    for i, (question, answer) in enumerate(zip(generated_questions, student_answers)):
        prompt = f"Question: {question}\nStudent's Answer: {answer}\nLesson Content: {lesson_content}\nProvide feedback on the student's answer."
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        
        feedback_message = response['choices'][0]['message']['content'].strip()
        feedback.append(f"Question {i + 1} Feedback: {feedback_message}")
    
    return "\n".join(feedback)

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
manual_content = st.text_area("Paste lesson content here:", height=150)

# Session state to track if questions have been generated
if 'generated_questions' not in st.session_state:
    st.session_state.generated_questions = []

# Load content from PDF or manual input
lesson_content = None
if uploaded_file is not None:
    lesson_content = load_pdf_content(uploaded_file)
    st.subheader("PDF Content")
    
    # Display PDF content in a scrollable text area
    st.text_area("PDF Content", value=lesson_content, height=300, disabled=True)  # Set height as needed

elif manual_content:
    lesson_content = manual_content

# Generate questions if content is available
if lesson_content:
    if st.button("Generate Questions"):
        st.session_state.generated_questions = generate_questions_from_content(lesson_content)
    
    if st.session_state.generated_questions:
        st.subheader("Test Questions")

        # Student answers section
        student_answers = []
        feedbacks = []
        with st.form(key='question_form'):
            for i, question in enumerate(st.session_state.generated_questions):
                # Create a color block for each question
                question_color = f"#{i * 30 % 255:02x}{(255 - i * 30 % 255):02x}c0"
                st.markdown(f'<div style="background-color: {question_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">', unsafe_allow_html=True)
                st.write(f"**Question {i + 1}:** {question}")
                answer = st.text_input(f"Your answer to question {i + 1}", key=f"answer_{i}")
                student_answers.append(answer)
                st.markdown('</div>', unsafe_allow_html=True)  # End color block
            
            # Submit button for form
            submit = st.form_submit_button("Submit Answers")
            
            if submit and all(student_answers):
                # Provide feedback using OpenAI
                feedback = get_grading(student_answers, st.session_state.generated_questions, lesson_content)
                feedbacks = feedback.split("\n")
                
                st.subheader("Feedback on Your Answers:")
                
                for feedback in feedbacks:
                    st.markdown(f'<div style="background-color: #e0f7fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;">{feedback}</div>', unsafe_allow_html=True)
            elif submit:
                st.warning("Please answer all questions before submitting.")
else:
    st.write("Please upload a PDF file or enter the lesson content manually.")
