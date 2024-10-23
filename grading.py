import streamlit as st
import openai
import pandas as pd
import PyPDF2  # For reading PDF files
from docx import Document  # For reading Word documents
import re  # For regex pattern matching

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get grading from OpenAI based on student submissions and proposed answers
def get_grading(student_submission, proposed_answer, content_type):
    grading_prompt = f"Evaluate the student's submission based on the proposed answer:\n\n"
    if content_type == "Math (LaTeX)":
        grading_prompt += f"**Proposed Answer (LaTeX)**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Submission (LaTeX)**: {student_submission}\n\n"
        grading_prompt += "Provide feedback on correctness, grade out of 10, and suggest improvements."
    elif content_type == "Programming (Code)":
        grading_prompt += f"**Proposed Code**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Code Submission**: {student_submission}\n\n"
        grading_prompt += "Check logic, efficiency, correctness, and grade out of 10."
    else:
        grading_prompt += f"**Proposed Answer**: {proposed_answer}\n\n"
        grading_prompt += f"**Student Submission**: {student_submission}\n\n"
        grading_prompt += "Provide detailed feedback and grade out of 10. Suggest improvements."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": grading_prompt}]
    )
    
    feedback = response['choices'][0]['message']['content']
    return feedback

# Function to detect AI-generated content
def is_ai_generated(content):
    ai_keywords = ["As an AI", "As a language model", "I don’t have personal opinions", "I cannot", "AI-generated content"]
    return any(keyword.lower() in content.lower() for keyword in ai_keywords)

# Function to extract grade from feedback
def extract_grade(feedback):
    grade_match = re.search(r'(\d+(\.\d+)?)\s*(?:/|out of)\s*(10)', feedback, re.IGNORECASE)
    return grade_match.group(1) if grade_match else "N/A"

# Function to clean feedback by removing grade mention
def clean_feedback(feedback):
    return re.sub(r'(\d+(\.\d+)?)\s*(?:/|out of)\s*(10)', '', feedback).strip()

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
            <li>Select the type of content being evaluated (Text, Math, or Code).</li>
            <li>Submit to receive grading and feedback for all submissions.</li>
        </ul>
        <p>Enhance your grading experience with AI!</p>
    </div>
    """, unsafe_allow_html=True)

# Upload section for student work
st.subheader("Upload Student Work (Multiple Files)")
uploaded_files = st.file_uploader("Upload student work (PDF, Word, or text files)", type=["pdf", "docx", "txt"], accept_multiple_files=True)

# Input for the proposed answer
proposed_answer = st.text_area("Proposed Answer:", placeholder="Type the answer you expect from the student here...")

# Dropdown for selecting content type
content_type = st.selectbox("Select Content Type", options=["Text", "Math (LaTeX)", "Programming (Code)"])

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

            # Get grading feedback
            feedback = get_grading(student_submission.strip(), proposed_answer, content_type)
            
            # Extract the grade from feedback
            grade = extract_grade(feedback)

            # Clean feedback to remove any mention of grades
            feedback_cleaned = clean_feedback(feedback)

            # AI detection for content
            ai_generated = is_ai_generated(student_submission.strip())
            ai_flag = "Yes" if ai_generated else "No"

            # Append results for this submission
            results.append({
                "Student Name": student_name,
                "Submission": student_submission.strip(),
                "Grade": grade,
                "AI Generated": ai_flag,
                "Feedback": feedback_cleaned
            })
        
        except Exception as e:
            st.error(f"An error occurred while processing the file '{uploaded_file.name}': {e}")

    if results:
        # Convert results to DataFrame
        feedback_df = pd.DataFrame(results)

        # Display the table with auto-sizing cells for better visibility
        st.dataframe(feedback_df[['Student Name', 'Submission', 'Grade', 'AI Generated', 'Feedback']], width=1000, height=400)

        # Download link for feedback
        feedback_csv = feedback_df.to_csv(index=False)
        st.download_button("Download Feedback as CSV", feedback_csv, "feedback.csv", "text/csv")

else:
    st.write("Please upload the student's work and enter the proposed answer.")
