import streamlit as st
import openai
import pandas as pd
import fitz  # PyMuPDF for PDFs
from docx import Document

# Set your OpenAI API key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Function to extract text from a Word document
def extract_text_from_word(docx_path):
    doc = Document(docx_path)
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
def process_student_submissions(doc_path, proposed_answers, file_type="pdf"):
    if file_type == "pdf":
        text = extract_text_from_pdf(doc_path)
    elif file_type == "docx":
        text = extract_text_from_word(doc_path)
    else:
        raise ValueError("Unsupported file type. Use 'pdf' or 'docx'.")

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

# Text area for proposed answers
st.write("Input proposed answers below:")
proposed_answers_text = st.text_area("Proposed Answers (separate answers with new lines):", height=200)

# Split proposed answers into a list for processing
if proposed_answers_text:
    proposed_answers = proposed_answers_text.split("\n")
else:
    proposed_answers = []

if uploaded_file is not None and proposed_answers:
    file_type = "pdf" if uploaded_file.name.endswith('.pdf') else "docx"
    
    # Process submissions and display results
    df = process_student_submissions(uploaded_file, proposed_answers, file_type)
    st.write(df)

    # To allow users to download the results
    if st.button("Download Feedback as CSV"):
        df.to_csv("student_feedback.csv", index=False)
        st.success("Feedback saved as 'student_feedback.csv'!")
