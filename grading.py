import streamlit as st
import openai
import PyPDF2
import pandas as pd

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate questions based on lesson content
def generate_questions_from_content(lesson_content):
    prompt = f"Generate 3 questions based on the following lesson content:\n{lesson_content}\n\nMake sure the questions test the student's understanding."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
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
        messages=[{"role": "user", "content": grading_prompt}]
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
            <li>Upload your lesson content in <strong>PDF format</strong>, or type the lesson content manually.</li>
            <li>Generate questions to assess your understanding of the material.</li>
            <li>Upload students' work for grading and feedback.</li>
        </ul>
        <p>Get ready to enhance your learning experience with AI!</p>
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
    if lesson_content:
        st.markdown('<div class="pdf-area"><pre>{}</pre></div>'.format(lesson_content), unsafe_allow_html=True)
elif manual_content:
    lesson_content = manual_content

# Generate questions if content is available
if lesson_content:
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
                
                # Save feedback to a DataFrame
                grading_results = []
                for i, (question, answer) in enumerate(zip(st.session_state.generated_questions, student_answers)):
                    grade = feedback.split("\n")[i].split(":")[1].strip()  # Extract the grade
                    grading_results.append({"Question": question, "Student Answer": answer, "Feedback": feedback.split("\n")[i], "Grade": grade})

                # Create DataFrame and display it
                grading_df = pd.DataFrame(grading_results)
                st.write("Grading Results:")
                st.dataframe(grading_df)  # Display the results in a table
                
            elif submit:
                st.warning("Please answer all questions before submitting.")
else:
    st.write("Please upload a PDF file or enter the lesson content manually.")

# Upload student work for grading
st.subheader("Upload Student Work for Grading")
student_work_file = st.file_uploader("Upload a PDF of student work", type="pdf")

if student_work_file is not None:
    student_work_content = load_pdf_content(student_work_file)
    st.write("Uploaded Student Work:")
    st.markdown('<div class="pdf-area"><pre>{}</pre></div>'.format(student_work_content), unsafe_allow_html=True)

    # Button to grade the student work
    if st.button("Grade Student Work"):
        # Placeholder for grading logic, this can be enhanced to integrate grading logic
        student_answers = student_work_content.split("\n")  # Simulate extracting answers
        feedback = get_grading(student_answers, st.session_state.generated_questions, lesson_content)
        st.subheader("Feedback on Student Work:")
        st.markdown(f"<div class='chatbox'>{feedback}</div>", unsafe_allow_html=True)
        
        # Save feedback to a DataFrame
        grading_results = []
        for i, (question, answer) in enumerate(zip(st.session_state.generated_questions, student_answers)):
            grade = feedback.split("\n")[i].split(":")[1].strip()  # Extract the grade
            grading_results.append({"Question": question, "Student Answer": answer, "Feedback": feedback.split("\n")[i], "Grade": grade})

        # Create DataFrame and display it
        grading_df = pd.DataFrame(grading_results)
        st.write("Grading Results:")
        st.dataframe(grading_df)  # Display the results in a table

# Chatbot interaction section
st.subheader("Chatbot Interaction")
student_input = st.text_input("Ask your question about the lesson:")

if student_input and lesson_content:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Lesson Content: {lesson_content}\n\nStudent Query: {student_input}"}]
    )
    st.markdown('<div class="chatbox">{}</div>'.format(response['choices'][0]['message']['content']), unsafe_allow_html=True)
