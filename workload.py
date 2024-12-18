import streamlit as st
import pandas as pd
import numpy as np
from tabulate import tabulate
import io

# Function to generate a template
def generate_template():
    # Sample course structure template
    course_template = pd.DataFrame({
        'Module Code': ['M101', 'M102', 'M103'],
        'Module Name': ['Course 1', 'Course 2', 'Course 3'],
        'Credit': [10, 15, 20],
        'Term': ['Term 1', 'Term 2', 'Term 3'],
        'Program': ['Program A', 'Program B', 'Program C']
    })
    
    # Sample teacher module template
    teacher_template = pd.DataFrame({
        'Teacher Name': ['Alice', 'Bob', 'Carol'],
        'Module Code': ['M101', 'M102', 'M103'],
        'Module Name': ['Course 1', 'Course 2', 'Course 3']
    })
    
    # Sample student database template
    student_template = pd.DataFrame({
        'Cohort': ['Cohort 1', 'Cohort 2', 'Cohort 3'],
        'Student Number': ['S001', 'S002', 'S003'],
        'Module Name': ['Course 1', 'Course 2', 'Course 3'],
        'Module Code': ['M101', 'M102', 'M103'],
        'Term': ['Term 1', 'Term 2', 'Term 3'],
        'Section': [1, 2, 3],  # Changed to numeric sections
        'Year': [1, 2, 3]  # Representing student year (1st, 2nd, 3rd)
    })
    
    # Convert DataFrames to CSV strings and then to bytes
    course_buffer = io.BytesIO()
    teacher_buffer = io.BytesIO()
    student_buffer = io.BytesIO()
    
    course_template.to_csv(course_buffer, index=False)
    teacher_template.to_csv(teacher_buffer, index=False)
    student_template.to_csv(student_buffer, index=False)
    
    # Ensure the buffers are set to the beginning so they can be read
    course_buffer.seek(0)
    teacher_buffer.seek(0)
    student_buffer.seek(0)
    
    return course_buffer, teacher_buffer, student_buffer

def calculate_workload(course_data, teacher_modules, student_db):
    # Clean column names to avoid issues with extra spaces
    course_data.columns = course_data.columns.str.strip()
    teacher_modules.columns = teacher_modules.columns.str.strip()
    student_db.columns = student_db.columns.str.strip()
    
    # Merge the dataframes: First merge course_data and teacher_modules on 'Module Code' and 'Module Name'
    merged_data = pd.merge(course_data, teacher_modules, on=['Module Code', 'Module Name'], how='inner')
    
    # Merge student database with the course and teacher data based on 'Module Code' and 'Module Name'
    merged_data = pd.merge(merged_data, student_db[['Module Code', 'Module Name', 'Term', 'Cohort', 'Student Number', 'Section', 'Year']], 
                           on=['Module Code', 'Module Name'], how='left')

    # Debugging: Print the columns to check if they are correct
    st.write("Columns in merged_data:", merged_data.columns)

    # Ensure that we are considering only valid students (i.e., cohort is not empty)
    merged_data = merged_data[merged_data['Cohort'].notna() & (merged_data['Cohort'] != '')]

    # Simplified debug: Check if grouping by a single column works
    simplified_group = merged_data.groupby('Module Code').size().reset_index(name='Number of Students')
    st.write(simplified_group)

    # Now try to group by all the necessary columns
    student_count = merged_data.groupby(['Module Code', 'Module Name', 'Term', 'Cohort', 'Year']).size().reset_index(name='Number of Students')

    # Merge the student count back into the merged data
    merged_data = pd.merge(merged_data, student_count, on=['Module Code', 'Module Name', 'Term', 'Cohort', 'Year'], how='inner')

    # Calculate the number of classes per section based on student count divided by the section number
    merged_data['Classes'] = (merged_data['Number of Students'] / merged_data['Section']).apply(np.ceil)

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

    # Group the data by Term, Teacher Name, and other relevant variables
    grouped_data = merged_data.groupby(['Term', 'Teacher Name', 'Module Code', 'Module Name', 'Year']).agg(
        {
            'Number of Students': 'sum',
            'Teaching Hours': 'sum',
            'Office Hours': 'sum',
            'Grading Hours': 'sum',
            'Research Hours': 'sum',
            'Meetings Hours': 'sum',
            'Curriculum Development Hours': 'sum',
            'Other Responsibilities Hours': 'sum',
            'Total Weekly Hours': 'sum',
            'Total Term Workload': 'sum',
            'Classes': 'sum'  # Sum up the number of classes
        }).reset_index()

    return grouped_data


# Streamlit UI
st.title('Workload Calculation for Teachers')

# Provide option to download the template
st.subheader("Download Template Files for Upload")

course_buffer, teacher_buffer, student_buffer = generate_template()

st.download_button(
    label="Download Course Structure Template",
    data=course_buffer,
    file_name="course_structure_template.csv",
    mime="text/csv"
)

st.download_button(
    label="Download Teacher Module Template",
    data=teacher_buffer,
    file_name="teacher_module_template.csv",
    mime="text/csv"
)

st.download_button(
    label="Download Student Database Template",
    data=student_buffer,
    file_name="student_database_template.csv",
    mime="text/csv"
)

# File upload widgets
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
    st.subheader("Workload Summary")
    st.write(final_output)

    # Option to download the final output
    st.download_button(
        label="Download Workload Summary",
        data=final_output.to_csv(index=False).encode('utf-8'),
        file_name="workload_summary.csv",
        mime="text/csv"
    )
