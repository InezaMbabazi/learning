import streamlit as st
import openai
import PyPDF2

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate multiple-choice questions based on lesson content
def generate_mc_questions(lesson_content):
    prompt = f"""
    Based on the following lesson content, generate 3 multiple-choice questions. 
    For each question, provide:
    1. The question text.
    2. Four options (A, B, C, D).
    3. Mark the correct answer with the format: "Correct Answer: <Option Letter>".
    
    Lesson Content: {lesson_content}
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    questions_raw = response['choices'][0]['message']['content'].strip().split("\n\n")
    
    parsed_questions = []
    for question_raw in questions_raw:
        lines = question_raw.strip().split("\n")
        if len(lines) < 6:
            st.error(f"Unexpected question format: {lines}")
            continue
        
        question_text = lines[0]
        options = lines[1:5]
        correct_answer_line = next((line for line in lines if "Correct Answer:" in line), None)
        if not correct_answer_line:
            st.error(f"No correct answer found in: {lines}")
            continue
        
        correct_answer = correct_answer_line.split(":")[-1].strip()
        parsed_questions.append({
            "question": question_text,
            "options": options,
            "correct": correct_answer
        })
    return parsed_questions

# Function to generate personalized feedback
def generate_feedback(lesson_content, question, user_answer, correct_answer):
    feedback_prompt = f"""
    Lesson Content: {lesson_content}
    
    Question: {question}
    User's Answer: {user_answer}
    Correct Answer: {correct_answer}
    
    Provide feedback for the user based on their answer. If the user's answer is incorrect, suggest specific parts of the lesson content they should review to better understand the topic.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": feedback_prompt}]
    )
    feedback = response['choices'][0]['message']['content'].strip()
    return feedback

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

# Generate test questions and display them
if lesson_content:
    if st.button("Generate Test Questions"):
        mc_questions = generate_mc_questions(lesson_content)
        if mc_questions:
            st.session_state["questions"] = mc_questions
        else:
            st.write("No valid questions were generated. Please revise the content.")

# Display questions and capture user answers
if "questions" in st.session_state:
    st.subheader("Test Yourself!")
    user_answers = []
    for idx, question in enumerate(st.session_state["questions"]):
        st.write(f"**Question {idx + 1}:** {question['question']}")
        for option in question["options"]:
            st.write(option)
        user_answer = st.radio(
            f"Select your answer for Question {idx + 1}:", 
            options=["A", "B", "C", "D"], 
            key=f"q{idx + 1}"
        )
        user_answers.append(user_answer)
    
    # Submit button for all questions
    if st.button("Submit Answers"):
        score = 0
        st.subheader("Results and Feedback:")
        for idx, (question, user_answer) in enumerate(zip(st.session_state["questions"], user_answers)):
            correct_answer = question["correct"]
            st.write(f"**Question {idx + 1}:** {question['question']}")
            
            if user_answer == correct_answer:
                score += 1
                st.write(f"✅ Correct! The correct answer is {correct_answer}.")
            else:
                st.write(f"❌ Incorrect. The correct answer is {correct_answer}.")
            
            # Provide feedback and suggested learning
            feedback = generate_feedback(lesson_content, question["question"], user_answer, correct_answer)
            st.write(f"**Feedback:** {feedback}")
        
        st.write(f"**Your Score: {score}/{len(st.session_state['questions'])}**")
else:
    st.write("Please upload a lesson or enter content to generate questions.")
