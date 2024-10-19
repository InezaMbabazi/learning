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
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the generated questions
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

# Function to get grading from OpenAI based on student responses
def get_grading(student_answers, generated_questions, lesson_content):
    grading_prompt = f"Based on the following lesson content: {lesson_content}\n"
    grading_prompt += "Here are the student's answers and the questions:\n"

    for i, (question, answer) in enumerate(zip(generated_questions, student_answers), 1):
        grading_prompt += f"Question {i}: {question}\nStudent's Answer: {answer}\n"

    grading_prompt += "\nPlease provide feedback for each answer, grade each answer out of 10, and suggest improvements if necessary."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": grading_prompt}
        ]
    )
    
    feedback = response['choices'][0]['message']['content']
    return feedback

# Streamlit UI
st.image("header.png", use_column_width=True)  # Add your header image file here
st.title("Kepler College AI-Powered Lesson Assistant")

# Instructions with better formatting
st.markdown("""
    <div style="background-color: #f0f0f5; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: #2E86C1;">Welcome to Kepler College's AI-Powered Lesson Assistant</h3>
        <p>To use this AI assistant, follow these simple steps:</p>
        <ul style="list-style-type: square;">
            <li>Upload your lesson content in <strong>PDF format</strong>.</li>
            <li>Generate questions to assess your understanding of the material.</li>
            <li>Interact with the chatbot to receive AI-driven answers and explanations about your content.</li>
        </ul>
        <p>Get ready to enhance your learning experience with AI!</p>
    </div>
    """, unsafe_allow_html=True)

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

# Session state to track if questions have been generated
if 'generated_questions' not in st.session_state:
    st.session_state.generated_questions = []

if uploaded_file is not None:
    # Load and store the lesson content for chatbot use
    lesson_content = load_pdf_content(uploaded_file)
    
    # Check if content was successfully loaded
    if lesson_content:
        # Display the PDF content in a selectable area
        st.markdown('<div class="pdf-area"><pre>{}</pre></div>'.format(lesson_content), unsafe_allow_html=True)
        
        # Generate test questions using OpenAI based on the PDF content
        if st.button("Generate Questions"):
            st.session_state.generated_questions = generate_questions_from_content(lesson_content)
        
        # Display the generated questions and student input
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
                
                # Display feedback after submission
                if submit and all(student_answers):
                    feedback = get_grading(student_answers, st.session_state.generated_questions, lesson_content)
                    st.subheader("Feedback on Your Answers:")
                    st.markdown(f"<div class='chatbox'>{feedback}</div>", unsafe_allow_html=True)
                elif submit:
                    st.warning("Please answer all questions before submitting.")
    else:
        st.write("Unable to extract text from PDF.")
else:
    st.write("Please upload a PDF file.")

# Chatbot interaction section
st.subheader("Chatbot Interaction")
student_input = st.text_input("Ask your question about the lesson:")

if student_input and 'lesson_content' in locals():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Lesson Content: {lesson_content}\n\nStudent Query: {student_input}"}
        ]
    )
    st.markdown('<div class="chatbox">{}</div>'.format(response['choices'][0]['message']['content']), unsafe_allow_html=True)
``
