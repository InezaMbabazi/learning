import streamlit as st
import openai
import pandas as pd
import os
from datetime import datetime

# Initialize OpenAI API
openai.api_key = st.secrets["openai"]["api_key"]

# Directory for saving student records
RECORDS_DIR = "student_records"
if not os.path.exists(RECORDS_DIR):
    os.makedirs(RECORDS_DIR)

# Function to save student progress
def save_student_progress(student_id, assessment_data):
    file_path = os.path.join(RECORDS_DIR, f"{student_id}_progress.csv")
    new_data = pd.DataFrame([assessment_data])
    if os.path.exists(file_path):
        # Append new data to existing file
        existing_data = pd.read_csv(file_path)
        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
        updated_data.to_csv(file_path, index=False)
    else:
        # Create new file
        new_data.to_csv(file_path, index=False)

# Function to load student progress
def load_student_progress(student_id):
    file_path = os.path.join(RECORDS_DIR, f"{student_id}_progress.csv")
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return None

# Streamlit UI
st.title("Student Performance Tracker")
student_id = st.text_input("Enter your Student ID:", "")

if student_id:
    st.subheader("Assessment and Progress")

    # Example: Dummy data for current assessment (replace with your logic)
    current_assessment = {
        "Assessment Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Score": 8,
        "Total Questions": 10,
        "Percentage": (8 / 10) * 100
    }

    if st.button("Save Current Assessment"):
        save_student_progress(student_id, current_assessment)
        st.success("Assessment saved successfully!")

    # Load student progress
    progress_data = load_student_progress(student_id)

    if progress_data is not None:
        st.subheader("Your Performance Overview")
        
        # Display raw data
        st.write(progress_data)

        # Calculate statistics
        total_attempts = len(progress_data)
        avg_score = progress_data["Percentage"].mean()
        best_score = progress_data["Percentage"].max()
        worst_score = progress_data["Percentage"].min()

        st.write(f"**Total Assessments Attempted:** {total_attempts}")
        st.write(f"**Average Score:** {avg_score:.2f}%")
        st.write(f"**Best Score:** {best_score:.2f}%")
        st.write(f"**Worst Score:** {worst_score:.2f}%")

        # Plot performance trend
        st.line_chart(progress_data[["Percentage"]])

    else:
        st.info("No progress data found. Start by saving your first assessment.")
