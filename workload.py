import pandas as pd
import streamlit as st
from tabulate import tabulate

# Function to calculate the workload
def calculate_workload(course_data, teacher_modules, student_db):
    # Clean column names to avoid issues with extra spaces
    course_data.columns = course_data.columns.str.strip()
    teacher_modules.columns = teacher_modules.columns.str.strip()
    student_db.columns = student_db.columns.str.strip()

    # Ensure 'Term' exists in teacher_modules DataFrame (add a placeholder if it's missing)
    if 'Term' not in teacher_modules.columns:
        teacher_modules['Term'] = 'Default Term'  # Replace 'Default Term' with the actual logic if needed

    # Merge the course_data and teacher_modules first (on 'Module Code' and 'Module Name')
    merged_data = pd.merge(course_data, teacher_modules, on=['Module Code', 'Module Name'], how='inner')
    
    # Merge the student_db separately to include 'Term' column
    student_count = student_db.groupby(['Module Code', 'Module Name', 'Term']).size().reset_index(name='Number of Students')
    merged_data = pd.merge(merged_data, student_count, on=['Module Code', 'Module Name', 'Term'], how='left')
    
    # Calculate workload components
    merged_data['Teaching Hours'] = merged_data['Credit'].apply(lambda x: 4 if x == 10 else (4 if x == 15 else 6))
    merged_data['Office Hours'] = merged_data['Credit'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 2))
    merged_data['Grading Hours'] = merged_data['Number of Students'] * merged_data['Credit'].apply(
        lambda x: 0.083 if x == 10 else (0.083 if x == 15 else 0.117))

    # Placeholder for other responsibilities
    merged_data['Research Hours'] = 3
    merged_data['Meetings Hours'] = 3
    merged_data['Curriculum Development Hours'] = 3
    merged_data['Other Responsibilities Hours'] = 0

    # Calculate total weekly hours and total term workload
    merged_data['Total Weekly Hours'] = (
        merged_data['Teaching Hours'] +
        merged_data['Office Hours'] +
        merged_data['Grading Hours'] +
        merged_data['Research Hours'] +
        merged_data['Meetings Hours'] +
        merged_data['Curriculum Development Hours'] +
        merged_data['Other Responsibilities Hours']
    )

    # Assuming 12 weeks per term
    merged_data['Total Term Workload'] = merged_data['Total Weekly Hours'] * 12

    # Define columns for display
    term_columns = [
        'Teacher Name', 'Module Code', 'Module Name', 'Section', 'Number of Students',
        'Teaching Hours', 'Office Hours', 'Grading Hours', 'Research Hours', 
        'Meetings Hours', 'Curriculum Development Hours', 'Other Responsibilities Hours', 
        'Total Weekly Hours', 'Total Term Workload', 'Term'
    ]
    
    # Now filter based on Term and display for different terms
    term_1_data = merged_data[merged_data['Term'] == 'Term 1'][term_columns].copy()
    term_2_data = merged_data[merged_data['Term'] == 'Term 2'][term_columns].copy()
    term_3_data = merged_data[merged_data['Term'] == 'Term 3'][term_columns].copy()

    # Renaming columns to reflect Term 1, Term 2, Term 3
    term_1_data.columns = [f'TERM 1 {col}' for col in term_1_data.columns]
    term_2_data.columns = [f'TERM 2 {col}' for col in term_2_data.columns]
    term_3_data.columns = [f'TERM 3 {col}' for col in term_3_data.columns]

    # Merge all terms into one dataframe
    final_output = pd.concat([term_1_data, term_2_data, term_3_data], axis=1)

    return final_output

# Streamlit UI
st.title('Workload Calculation for Teachers')

# Upload CSV files
teacher_file = st.file_uploader("Upload Teacher Modules CSV", type=["csv"])
course_file = st.file_uploader("Upload Course Structure CSV", type=["csv"])
student_file = st.file_uploader("Upload Student Database CSV", type=["csv"])

if teacher_file is not None and course_file is not None and student_file is not None:
    # Read the uploaded CSV files into DataFrames
    teacher_modules = pd.read_csv(teacher_file)
    course_structure = pd.read_csv(course_file)
    student_db = pd.read_csv(student_file)
    
    # Process the data and calculate the workload
    try:
        final_output = calculate_workload(course_structure, teacher_modules, student_db)
        # Display the final output
        st.subheader("Calculated Workload")
        st.write(final_output)

        # Display the result in a tabular format using tabulate
        st.subheader("Workload Summary in Table Format")
        table_output = tabulate(final_output, headers='keys', tablefmt='grid', showindex=False)
        st.text(table_output)
    except KeyError as e:
        st.error(f"Error: {e}")

else:
    st.warning("Please upload all three CSV files to proceed.")

