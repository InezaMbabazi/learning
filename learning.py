import streamlit as st
import openai
import PyPDF2

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate questions based on lesson content
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
        if len(lines) < 6:  # Check if the response is in the correct format
            st.error(f"Unexpected question format: {lines}")
            continue  # Skip invalid questions
        
        question_text = lines[0]
        options = lines[1:5]
        correct_answer_line = next((line for line in lines if "Correct Answer:" in line), None)
        if not correct_answer_line:
            st.error(f"No correct answer found in: {lines}")
            continue  # Skip if no correct answer
        
        correct_answer = correct_answer_line.split(":")[-1].strip()
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

st.markdown("""<div style="background-color: #f0f0f5; padding: 20px; border-radius: 10px;">
<h3 style="color: #2E86C1;">Welcome to Kepler College's AI-Powered Lesson Assistant</h3>
<p>Upload your lesson content in <strong>PDF format</strong>, or type the lesson content manually. Submit your content and questions at the end.</p>
</div>""", unsafe_allow_html=True)

# Option 1: Upload PDF file
st.subheader("Option 1: Upload PDF File")
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

# Option 2: Manual text input
st.subheader("Option 2: Paste Specific Lesson Content Here")
manual_content = st.text_area("Paste lesson content here:")

# Processing inputs
lesson_content = None
if uploaded_file is not None:
    lesson_content = load_pdf_content(uploaded_file)
elif manual_content:
    lesson_content = manual_content

# Submit button
if st.button("Submit"):
    if not lesson_content:
        st.error("Please upload a PDF file or enter the lesson content manually.")
    else:
        # Display Lesson Content
        st.subheader("Lesson Content")
        st.write(lesson_content)
        
        # Generate Questions
        st.subheader("Generated Multiple-Choice Questions")
        mc_questions = generate_mc_questions(lesson_content)
        for i, question in enumerate(mc_questions, 1):
            st.write(f"**Question {i}:** {question['question']}")
            for option in question['options']:
                st.write(option)
            st.write(f"**Correct Answer:** {question['correct']}")
            st.write("---")
        
        # Chatbot Interaction
        st.subheader("Ask a Question About the Lesson Content")
        user_question = st.text_input("Your question about the lesson content:")
        
        if user_question:
            answer = chat_with_content(user_question, lesson_content)
            st.write("**Answer:**")
            st.write(answer)
