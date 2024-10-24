import streamlit as st
import openai
import PyPDF2
import base64  # Import base64 for encoding the PDF

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

# Display the PDF content using iframe
def display_pdf(file):
    with open(file.name, "wb") as f:
        f.write(file.getbuffer())
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64.b64encode(file.getvalue()).decode()}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

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

# Session state to track if questions have been generated
if 'generated_questions' not in st.session_state:
    st.session_state.generated_questions = []

# Load content from PDF or manual input
lesson_content = None
if uploaded_file is not None:
    lesson_content = load_pdf_content(uploaded_file)
    st.subheader("PDF Content")
    display_pdf(uploaded_file)  # Display PDF in an iframe
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
        with st.form(key='question_form'):
            for i, question in enumerate(st.session_state.generated_questions):
                st.write(f"Question {i+1}: {question}")
                answer = st.text_input(f"Your answer to question {i+1}", key=f"answer_{i}")
                student_answers.append(answer)
            
            # Submit button for form
            submit = st.form_submit_button("Submit Answers")
            
            if submit and all(student_answers):
                feedback = get_grading(student_answers, st.session_state.generated_questions, lesson_content)
                st.subheader("Feedback on Your Answers:")
                st.markdown(f"<div class='chatbox'>{feedback}</div>", unsafe_allow_html=True)
            elif submit:
                st.warning("Please answer all questions before submitting.")
else:
    st.write("Please upload a PDF file or enter the lesson content manually.")
