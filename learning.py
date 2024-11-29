import streamlit as st
import openai
import PyPDF2

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate multiple-choice questions
def generate_mc_questions(lesson_content):
    prompt = f"""
    Based on the following lesson content, generate 3 multiple-choice questions. 
    For each question, provide 4 options (A, B, C, D) with one correct answer clearly marked:
    
    Lesson Content: {lesson_content}
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    questions = response['choices'][0]['message']['content'].strip().split("\n\n")
    
    # Parse questions into a structured format
    parsed_questions = []
    for question in questions:
        lines = question.split("\n")
        question_text = lines[0]
        options = lines[1:5]
        correct_answer = lines[5].split(":")[-1].strip()  # Extract the correct answer
        parsed_questions.append({
            "question": question_text,
            "options": options,
            "correct": correct_answer
        })
    return parsed_questions

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
    st.subheader("Multiple-Choice Assessment Mode")
    
    if st.button("Generate Questions"):
        mc_questions = generate_mc_questions(lesson_content)
        user_answers = []
        correct_count = 0
        
        for i, q in enumerate(mc_questions, 1):
            st.write(f"**Question {i}:** {q['question']}")
            answer = st.radio(f"Choose your answer for Question {i}:", q['options'], key=f"q{i}")
            user_answers.append(answer)
            
            # Compare user answer with correct answer
            if st.button(f"Submit Answer for Question {i}", key=f"submit{i}"):
                if answer.startswith(q['correct']):
                    st.success("Correct!")
                    correct_count += 1
                else:
                    st.error(f"Wrong! The correct answer is: {q['correct']}")
        
        # Display final score
        if st.button("Finish Assessment"):
            st.write(f"**You got {correct_count}/{len(mc_questions)} questions correct!**")
else:
    st.write("Please upload a PDF file or enter the lesson content manually.")
