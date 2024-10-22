import streamlit as st
import openai
import pandas as pd

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
            <li>Upload the student's work for grading.</li>
            <li>Provide the proposed answer you expect from the student.</li>
            <li>Submit to receive grading and feedback.</li>
        </ul>
        <p>Enhance your grading experience with AI!</p>
    </div>
    """, unsafe_allow_html=True)

# Upload section for student work
st.subheader("Upload Student Work")
uploaded_file = st.file_uploader("Upload student work (PDF or text file)", type=["pdf", "txt"])

# Input for the proposed answer
proposed_answer = st.text_area("Proposed Answer:", placeholder="Type the answer you expect from the student here...")

# Process the uploaded file and proposed answer
if uploaded_file is not None and proposed_answer:
    if uploaded_file.type == "application/pdf":
        # Load PDF content
        reader = PyPDF2.PdfReader(uploaded_file)
        student_submission = ''
        for page in reader.pages:
            text = page.extract_text()
            if text:
                student_submission += text + "\n"
    else:  # Assuming the uploaded file is a text file
        student_submission = uploaded_file.read().decode("utf-8")

    if st.button("Grade Submission"):
        feedback = get_grading(student_submission, proposed_answer)
        
        # Display feedback
        st.subheader("Feedback on Student Submission:")
        st.markdown(f"<div class='chatbox'>{feedback}</div>", unsafe_allow_html=True)
else:
    st.write("Please upload the student's work and enter the proposed answer.")

# Save feedback in a DataFrame and allow download
if uploaded_file is not None and proposed_answer and feedback:
    feedback_df = pd.DataFrame({
        "Student Work": [student_submission],
        "Proposed Answer": [proposed_answer],
        "Feedback": [feedback]
    })
    
    # Download link for feedback
    feedback_csv = feedback_df.to_csv(index=False)
    st.download_button("Download Feedback as CSV", feedback_csv, "feedback.csv", "text/csv")
