import streamlit as st
import openai
import pandas as pd
import fitz  # PyMuPDF for PDFs
from docx import Document

# Set your OpenAI API key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Function to extract text from a Word document
def extract_text_from_word(docx_file):
    doc = Document(docx_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Function to generate feedback based on proposed answers
def generate_feedback(proposed_answer, student_answer):
    prompt = (f"Here is the proposed answer: {proposed_answer}\n"
              f"And here is the student's answer: {student_answer}\n"
              "Evaluate the student's answer out of 10, and provide feedback for improvement.")
    
    response = openai.Completion.create(
        engine="text-davinci-003", 
        prompt=prompt,
        max_tokens=200,
        temperature=0.5
    )
    
    return response.choices[0].text.strip()

# Main function for processing student submissions
def process_student_submissions(text, proposed_answers):
    student_answers = text.split("\n\n")  # Assuming student answers are separated by double newlines
    df = pd.DataFrame(student_answers, columns=["Student Answer"])
    
    # Generate feedback for each student's answer
    df['Feedback'] = df.apply(lambda row: generate_feedback(proposed_answers[row.name], row['Student Answer']), axis=1)
    
    return df

# Streamlit app UI
st.title("Student Answer Evaluation")
st.write("Upload a PDF or Word document containing student answers.")

# File uploader for student answers
uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx"])

# Display the uploaded file content if available
if uploaded_file is not None:
    file_type = "pdf" if uploaded_file.name.endswith('.pdf') else "docx"
    
    # Extract and display file content
    if file_type == "pdf":
        extracted_text = extract_text_from_pdf(uploaded_file)
    else:
        extracted_text = extract_text_from_word(uploaded_file)
    
    st.write("### Uploaded Content:")
    st.text_area("File Content:", extracted_text, height=300)

# Text area for proposed answers
st.write("Input proposed answers below:")
proposed_answers_text = st.text_area("Proposed Answers (separate answers with new lines):", height=200)

# Split proposed answers into a list for processing
if proposed_answers_text:
    proposed_answers = proposed_answers_text.split("\n")
else:
    proposed_answers = []

# Submit for grading
if uploaded_file is not None and proposed_answers and st.button("Submit for Grading"):
    # Process submissions and display results
    df = process_student_submissions(extracted_text, proposed_answers)
    st.write("### Grading Results:")
    st.write(df)

    # Option to download feedback as CSV
    if st.button("Download Feedback as CSV"):
        df.to_csv("student_feedback.csv", index=False)
        st.success("Feedback saved as 'student_feedback.csv'!")
