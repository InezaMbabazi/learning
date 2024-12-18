import pandas as pd
import streamlit as st
from tabulate import tabulate

# Function to calculate the workload
def calculate_workload(course_data, teacher_modules, student_db):
    # Clean column names to avoid issues with extra spaces
    course_data.columns = course_data.columns.str.strip()
    teacher_modules.columns = teacher_modules.columns.str.strip()
    student_db.columns = student_db.columns.str.strip()
    
    # Merge the dataframes: First merge course_data and teacher_modules on 'Module Code' and 'Module Name'
    merged_data = pd.merge(course_data, teacher_modules, on=['Module Code', 'Module Name'], how='inner')
    
    # Merge the student database to get the number of students
    student_count = student_db.groupby(['Module Code', 'Module Name']).size().reset_index(name='Number of Students')
    merged_data = pd.merge(merged_data, student_count, on=['Module Code', 'Module Name'], how='inner')
    
    # Add the 'Term' column from course_data or student_db after the merge
    if 'Term' in course_data.columns:
        merged_data['Term'] = course_data['Term']
    elif 'Term' in student_db.columns:
        merged_data['Term'] = student_db['Term']
    
    # Calculate the number of hours based on the credit value
    merged_data['Teaching Hours'] = merged_data['Credit'].apply(lambda x: 4 if x == 10 else (4 if x == 15 else 6))
    merged_data['Office Hours'] = merged_data['Credit'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 2))
    merged_data['Grading Hours'] = merged_data['Number of Students'] * merged_data['Credit'].apply(
        lambda x: 0.083 if x == 10 else (0.083 if x == 15 else 0.117))

    # Add placeholders for other responsibilities (adjust as needed)
    merged_data['Research Hours'] = 3  # Placeholder value
    merged_data['Meetings Hours'] = 3  # Placeholder value
    merged_data['Curriculum Development Hours'] = 3  # Placeholder value
    merged_data['Other Responsibilities Hours'] = 0  # As per your input

    # Calculate Total Weekly Hours
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

    # Split the data by term
    term_columns = [
        'Teacher Name', 'Module Code', 'Module Name', 'Section', 'Number of Students',
        'Teaching Hours', 'Office Hours', 'Grading Hours', 'Research Hours', 
        'Meetings Hours', 'Curriculum Development Hours', 'Other Responsibilities Hours', 
        'Total Weekly Hours', 'Total Term Workload'
    ]

    # Creating separate dataframes for each term
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
    final_output = calculate_workload(course_structure, teacher_modules, student_db)

    # Display the final output
    st.subheader("Calculated Workload")
    st.write(final_output)

    # Display the result in a tabular format using tabulate
    st.subheader("Workload Summary in Table Format")
    table_output = tabulate(final_output, headers='keys', tablefmt='grid', showindex=False)
    st.text(table_output)

else:
    st.warning("Please upload all three CSV files to proceed.")
