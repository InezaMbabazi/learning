import streamlit as st
import openai
import pandas as pd
import PyPDF2  # For reading PDF files
from docx import Document  # For reading Word documents
import re  # For regex pattern matching

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to get grading from OpenAI based on student submissions and proposed answers
def get_grading(student_submission, proposed_answer):
    grading_prompt = f"Proposed Answer: {proposed_answer}\n"
    grading_prompt += f"Student Submission: {student_submission}\n\n"
    grading_prompt += "Please provide feedback on the student's work, grade it out of 10, and suggest improvements if necessary."
    
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
st.title("Kepler College AI-Powered Grading Assistant")

# Instructions for the instructor
st.markdown("""
    <div style="background-color: #f0f0f5; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: #2E86C1;">Welcome to Kepler College's AI-Powered Grading Assistant</h3>
        <p>To use this assistant, follow these steps:</p>
        <ul style="list-style-type: square;">
            <li>Upload the student's work for grading (multiple files).</li>
            <li>Provide the proposed answer you expect from the student.</li>
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
            feedback = get_grading(student_submission.strip(), proposed_answer)
            
            # Extract the grade from feedback using regex
            grade_match = re.search(r'(\d+\.?\d*) out of \d+', feedback)
            grade = grade_match.group(1) if grade_match else "N/A"  # Get the numeric grade, or "N/A" if not found

            # Append results for this submission
            results.append({
                "Student Name": student_name,
                "Submission": student_submission.strip(),
                "Grade": grade,
                "Feedback": feedback
            })
        
        except Exception as e:
            st.error(f"An error occurred while processing the file '{uploaded_file.name}': {e}")

    if results:
        # Convert results to DataFrame
        feedback_df = pd.DataFrame(results)

        # Display results in the app
        st.subheader("Grading Results:")
        st.dataframe(feedback_df)

        # Download link for feedback
        feedback_csv = feedback_df.to_csv(index=False)
        st.download_button("Download Feedback as CSV", feedback_csv, "feedback.csv", "text/csv")

else:
    st.write("Please upload the student's work and enter the proposed answer.")
