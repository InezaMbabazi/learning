import streamlit as st
import openai
import PyPDF2
import random

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
        text = page.extract_text()
        if text:  # Only append if text is not None
            content += text + "\n"  # Adding newline for better formatting
    return content.strip()  # Return stripped content

# Function to generate test questions from the content
def generate_test_questions(content):
    # Split the content into sentences
    sentences = content.split('. ')
    
    # Randomly select 3 sentences as questions
    questions = random.sample(sentences, min(3, len(sentences))) if len(sentences) >= 3 else sentences
    
    return questions

# Function to grade the test
def grade_test(answers, correct_answers):
    score = 0
    for answer, correct in zip(answers, correct_answers):
        if answer.strip().lower() == correct.strip().lower():
            score += 1
    return score

# Streamlit UI
st.title("Chatbot for Lesson Assistance with Test Feature")

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
        
        # Generate test questions
        test_questions = generate_test_questions(lesson_content)
        
        # Testing button
        if st.button("Start Test"):
            st.subheader("Test")
            answers = []
            for i, question in enumerate(test_questions):
                st.write(f"Question {i+1}: {question}")
                answer = st.text_input(f"Your answer to question {i+1}:")
                answers.append(answer)

            # Check if answers are provided and grade the test
            if len(answers) == len(test_questions):
                correct_answers = [q.split(' ')[0] for q in test_questions]  # Simplified grading
                score = grade_test(answers, correct_answers)
                
                # Provide feedback based on score
                st.write(f"Your score: {score}/{len(test_questions)}")
                if score == len(test_questions):
                    st.write("Excellent! You understood the content well.")
                elif score >= len(test_questions) // 2:
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
