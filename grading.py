import streamlit as st
import pandas as pd
import openai
from docx import Document
from io import BytesIO
from PIL import Image
import os

# Set OpenAI API Key
openai.api_key = "1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH"

# Load header image
header_image = Image.open("header.png")

# Streamlit app layout with styling and header image
st.set_page_config(page_title="Kepler College Grading System", layout="centered")
st.image(header_image, use_column_width=True)
st.title("Kepler College Grading System")
st.markdown("<h4 style='color: #4B8BBE; text-align: center;'>Automated Submission Grading</h4>", unsafe_allow_html=True)

# File upload section with visible "Submission Text" styling
st.sidebar.header("Upload Submission")
uploaded_file = st.sidebar.file_uploader("Choose a file (txt, docx, or xlsx)", type=['txt', 'docx', 'xlsx'])
if st.sidebar.button("Browse Files from Local"):
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=['txt', 'docx', 'xlsx'], accept_multiple_files=False)

# Load proposed answer input area
proposed_answer = st.text_area("Proposed Answer", height=150, help="Enter the correct answer here for comparison.")

# Read the uploaded file content function
def read_file_content(file):
    if file.type == "text/plain":  # .txt files
        return file.read().decode("utf-8")
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":  # .docx files
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":  # .xlsx files
        df = pd.read_excel(file)
        return df  # Return as DataFrame for column display

# Display uploaded file content in Submission Text
if uploaded_file is not None:
    submission_content = read_file_content(uploaded_file)
    
    if isinstance(submission_content, pd.DataFrame):  # Display DataFrame in columns for .xlsx content
        st.write("### Submission Content")
        st.dataframe(submission_content.style.set_properties(**{
            'background-color': '#E8F0FE',
            'color': '#1D3557',
            'border': '1px solid #A8DADC',
            'border-radius': '3px',
            'padding': '5px'
        }))
    else:  # Display plain text for .txt and .docx content
        st.markdown("<div style='border: 2px solid #4B8BBE; padding: 10px; background-color: #E8F0FE;'>"
                    f"<strong>Submission Text:</strong><br>{submission_content}</div>", 
                    unsafe_allow_html=True)

# Function to generate grading and feedback with improvement suggestions
def generate_grading_feedback(submission_text, proposed_answer):
    if openai.api_key is None:
        st.error("OpenAI API key is missing. Please configure it to proceed.")
        return None, None

    # Prompt for OpenAI to provide alignment feedback, suggestions, and improvements
    prompt = (
        f"Evaluate the following student's submission against the proposed answer. "
        f"Provide alignment feedback and rate it from 0 to 100. If there is no alignment, specify 'no alignment' "
        f"without giving a grade. Also, provide suggestions and improvements.\n\n"
        f"Submission: {submission_text}\n"
        f"Proposed Answer: {proposed_answer}\n\n"
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    feedback_content = response['choices'][0]['message']['content'].strip()
    
    # Extract feedback and grade
    if "no alignment" in feedback_content.lower():
        grade = None  # No grade if no alignment
        feedback = "No alignment with the proposed answer. Please revise by aligning the submission with the proposed content structure and points."
    else:
        lines = feedback_content.split("\n")
        grade = lines[0].split(": ")[1].strip() if "Grade:" in lines[0] else "Not Assigned"
        feedback = "\n".join(lines[1:]).strip()
    
    return grade, feedback

# Grading and feedback section
if st.button("Grade Submission"):
    if uploaded_file is not None and proposed_answer:
        if isinstance(submission_content, pd.DataFrame):  # Convert DataFrame content to string for grading
            submission_text = submission_content.to_string(index=False)
        else:
            submission_text = submission_content
        
        grade, feedback = generate_grading_feedback(submission_text, proposed_answer)
        
        # Display grade and feedback with color-coded message box
        if grade:
            st.markdown(f"<div style='color: #FFFFFF; background-color: #4CAF50; padding: 10px; border-radius: 5px;'>"
                        f"<strong>Grade:</strong> {grade}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color: #1D3557; background-color: #F1FAEE; border: 1px solid #A8DADC; "
                    f"padding: 10px; border-radius: 5px;'><strong>Feedback:</strong> {feedback}</div>",
                    unsafe_allow_html=True)
    else:
        st.warning("Please upload a submission file and enter the proposed answer before grading.")

# Send feedback button to Canvas (Placeholder for Canvas integration)
if st.button("Send Feedback to Canvas"):
    st.success("Feedback and grade sent to Canvas!")  # Replace with actual integration call if available
