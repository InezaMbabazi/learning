import streamlit as st
import openai
import pandas as pd
import PyPDF2  # For reading PDF files
from docx import Document  # For reading Word documents
import re  # For regex pattern matching
import sympy as sp  # For mathematical evaluation
import subprocess  # For running code linting

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get grading from OpenAI based on student submissions and proposed answers
def get_grading_from_openai(student_submission, proposed_answer):
    grading_prompt = f"Proposed Answer: {proposed_answer}\n"
    grading_prompt += f"Student Submission: {student_submission}\n\n"
    grading_prompt += "Please provide feedback on the student's work, grade it out of 10, and suggest improvements if necessary."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    
    feedback = response['choices'][0]['message']['content']
    return feedback

# Function to evaluate mathematical correctness
def check_math_correctness(student_submission, proposed_answer):
    try:
        # Parse the student's submission and the proposed answer into symbolic expressions
        student_expr = sp.sympify(student_submission)
        proposed_expr = sp.sympify(proposed_answer)
        
        # Check if the two expressions are mathematically equivalent
        return student_expr.equals(proposed_expr), None
    except Exception as e:
        return False, f"Error processing math expressions: {str(e)}"

# Function to evaluate programming code
def evaluate_code(student_code, test_input, expected_output):
    try:
        # Create a safe environment to execute the code
        local_vars = {}
        
        # Execute the student's code
        exec(student_code, {}, local_vars)
        
        # Assuming the student's code has a function called 'solution'
        student_result = local_vars['solution'](test_input)
        
        # Compare student's result with expected output
        return student_result == expected_output, student_result
    except Exception as e:
        return False, f"Error executing the code: {str(e)}"

# Function to lint code for quality
def lint_code(student_code):
    # Save the student's code to a temporary file
    with open("student_code.py", "w") as f:
        f.write(student_code)
    
    # Run pylint on the code and capture the output
    result = subprocess.run(['pylint', 'student_code.py'], capture_output=True, text=True)
    
    return result.stdout

# Function to process the grading based on submission type
def get_grading(student_submission, proposed_answer, submission_type='text'):
    if submission_type == 'math':
        # Check mathematical correctness
        is_correct, error_message = check_math_correctness(student_submission, proposed_answer)
        if is_correct:
            return "Math submission is correct."
        else:
            return f"Math submission is incorrect: {error_message}"
    
    elif submission_type == 'code':
        # Test the code for correctness
        test_input = [1, 2, 3]  # Example input for the student's solution
        expected_output = 6      # Example expected output
        
        is_correct, result = evaluate_code(student_submission, test_input, expected_output)
        if is_correct:
            feedback = "Code executed correctly!"
        else:
            feedback = f"Code failed. Error: {result}"
        
        # Optionally run linting to give suggestions on code quality
        lint_feedback = lint_code(student_submission)
        feedback += f"\nCode Quality: {lint_feedback}"
        
        return feedback
    
    else:
        # General text grading using OpenAI
        feedback = get_grading_from_openai(student_submission, proposed_answer)
        return feedback

# Streamlit UI
st.image("header.png", use_column_width=True)
st.title("Kepler College AI-Powered Grading Assistant")

# Instructions for the instructor
st.markdown("""
    <div style="background-color: #f0f0f5; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: #2E86C1;">Welcome to Kepler College's AI-Powered Grading Assistant</h3>
        <p>To use this assistant, follow these steps:</p>
        <ul style="list-style-type: square;">
            <li>Upload the student's work for grading (multiple files).</li>
            <li>Provide the proposed answer you expect from the student.</li>
            <li>Choose the type of submission (text, math, or code).</li>
            <li>Submit to receive grading and feedback for all submissions.</li>
        </ul>
        <p>Enhance your grading experience with AI!</p>
    </div>
    """, unsafe_allow_html=True)

# Upload section for student work and choose submission type
st.subheader("Upload Student Work (Multiple Files)")
submission_type = st.radio("What type of submission are you grading?", ('Text', 'Math', 'Code'))
uploaded_files = st.file_uploader("Upload student work (PDF, Word, or text files)", type=["pdf", "docx", "txt"], accept_multiple_files=True)

# Input for the proposed answer
proposed_answer = st.text_area("Proposed Answer:", placeholder="Type the answer you expect from the student here...")

# Process the uploaded files and proposed answer
if uploaded_files and proposed_answer:
    results = []  # List to store results for each student's submission

    for uploaded_file in uploaded_files:
        try:
            # Initialize student submission variable
            student_submission = ""
            student_name = uploaded_file.name.split('.')[0]  # Assuming filename without extension is the student's name

            if uploaded_file.type == "application/pdf":
                # Load PDF content
                reader = PyPDF2.PdfReader(uploaded_file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        student_submission += text + "\n"
            
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                # Load Word document content
                doc = Document(uploaded_file)
                for para in doc.paragraphs:
                    student_submission += para.text + "\n"
            
            else:  # Assuming the uploaded file is a text file
                student_submission = uploaded_file.read().decode("utf-8")

            # Call the grading function based on the submission type
            feedback = get_grading(student_submission.strip(), proposed_answer, submission_type=submission_type.lower())

            # Append results for this submission
            results.append({
                "Student Name": student_name,
                "Submission": student_submission.strip(),
                "Feedback": feedback
            })
        
        except Exception as e:
            st.error(f"An error occurred while processing the file '{uploaded_file.name}': {e}")

    if results:
        # Convert results to DataFrame
        feedback_df = pd.DataFrame(results)

        # Display the table with auto-sizing cells for better visibility
        st.dataframe(feedback_df[['Student Name', 'Submission', 'Feedback']], width=1000, height=400)

        # Download link for feedback
        feedback_csv = feedback_df.to_csv(index=False)
        st.download_button("Download Feedback as CSV", feedback_csv, "feedback.csv", "text/csv")

else:
    st.write("Please upload the student's work and enter the proposed answer.")
