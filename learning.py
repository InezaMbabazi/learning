import streamlit as st 
import openai
import PyPDF2

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate questions based on lesson content
def generate_questions_from_content(lesson_content):
    prompt = f"Generate 3 detailed questions based on the following lesson content:\n{lesson_content}\n\nPlease ensure the questions are relevant and test the student's understanding."
    
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
    grading_prompt = f"Lesson Content: {lesson_content}\n\nHere are the student's answers and the questions:\n"
    for i, (question, answer) in enumerate(zip(generated_questions, student_answers), 1):
        grading_prompt += f"Question {i}: {question}\nStudent's Answer: {answer}\n"

    grading_prompt += "\nPlease grade the student's answers and provide feedback for each."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    
    feedback = response['choices'][0]['message']['content']
    return feedback

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

            # Display questions in a form to get student responses
            with st.form(key='question_form'):
                answers = []
                
                # Loop through generated questions to create input fields
                for i, question in enumerate(generated_questions):
                    st.write(f"Question {i+1}: {question}")
                    answer = st.text_input(f"Your answer to question {i+1}", key=f"answer_{i}")
                    answers.append(answer)

                # Submit button for form
                submit = st.form_submit_button("Submit Answers")

                # Once the form is submitted, grade the student's answers
                if submit:
                    if all(answers):  # Ensure that all questions have been answered
                        # Display progress while waiting for the AI grading
                        with st.spinner("Grading your answers, please wait..."):
                            feedback = get_grading(answers, generated_questions, lesson_content)
                        
                        # Display feedback in the chatbox area
                        st.subheader("Feedback on Your Answers:")
                        st.markdown(f"<div class='chatbox'>{feedback}</div>", unsafe_allow_html=True)
                    else:
                        st.warning("Please answer all questions before submitting.")
    else:
        st.write("Unable to extract text from PDF.")
else:
    st.write("Please upload a PDF file.")

# Chatbot interaction section (appears after uploading PDF)
if 'lesson_content' in locals():
    st.subheader("Chatbot Interaction")
    student_input = st.text_input("Ask your question about the lesson:")

    if student_input:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Lesson Content: {lesson_content}\n\nStudent Query: {student_input}"}]
        )
        st.markdown('<div class="chatbox">{}</div>'.format(response['choices'][0]['message']['content']), unsafe_allow_html=True)
