import streamlit as st
import openai
import PyPDF2
import random

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get response from OpenAI based on the lesson content for generating questions
def generate_questions_from_content(lesson_content):
    prompt = f"Generate 3 questions based on the following lesson content:\n{lesson_content}\n\nPlease ensure the questions are relevant and test the student's understanding."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extracting the generated questions
    generated_questions = response['choices'][0]['message']['content'].strip().split("\n")
    return generated_questions

# Function to load PDF content
def load_pdf_content(file):
    reader = PyPDF2.PdfReader(file)
    content = ''
    for page in reader.pages:
        text = page.extract_text()
        if text:  # Only append if text is not None
            content += text + "\n"  # Adding newline for better formatting
    return content.strip()  # Return stripped content

# Function to grade the test (based on simplified logic)
def grade_test(answers, correct_answers):
    score = 0
    for answer, correct in zip(answers, correct_answers):
        if answer.strip().lower() == correct.strip().lower():
            score += 1
    return score

# Streamlit UI
st.title("Chatbot for Lesson Assistance with AI-Generated Questions")

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
        padding: 10px;
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
    # Load and store the lesson content for chatbot use
    lesson_content = load_pdf_content(uploaded_file)
    
    # Check if content was successfully loaded
    if lesson_content:
        # Display the PDF content in a selectable area
        st.markdown('<div class="pdf-area"><pre>{}</pre></div>'.format(lesson_content), unsafe_allow_html=True)
        
        # Generate test questions using OpenAI based on the PDF content
        if st.button("Generate Questions"):
            generated_questions = generate_questions_from_content(lesson_content)
            st.subheader("Test Questions")
            answers = []
            for i, question in enumerate(generated_questions):
                st.write(f"Question {i+1}: {question}")
                answer = st.text_input(f"Your answer to question {i+1}:")
                answers.append(answer)
            
            # Check if answers are provided and grade the test
            if len(answers) == len(generated_questions):
                # Simplified grading: we assume the answer is the first word of the question (just for demo purposes)
                correct_answers = [q.split(' ')[0] for q in generated_questions] 
                score = grade_test(answers, correct_answers)
                
                # Provide feedback based on score
                st.write(f"Your score: {score}/{len(generated_questions)}")
                if score == len(generated_questions):
                    st.write("Excellent! You understood the content well.")
                elif score >= len(generated_questions) // 2:
                    st.write("Good job, but you may want to review some parts.")
                else:
                    st.write("You should review the lesson and try again.")
    else:
        st.write("Unable to extract text from PDF.")
else:
    st.write("Please upload a PDF file.")

# Chatbot interaction section
st.subheader("Chatbot Interaction")
student_input = st.text_input("Ask your question about the lesson:")

if student_input and 'lesson_content' in locals():
    response = get_chatbot_response(student_input, lesson_content)
    st.markdown('<div class="chatbox">{}</div>'.format(response), unsafe_allow_html=True)
