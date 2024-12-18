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
        'Year': [2024, 2024, 2024],
        'Program': ['Program A', 'Program B', 'Program C'],
        'Cohort': ['Cohort 1', 'Cohort 2', '']  # Module M103 has no cohort
    })
    
    # Sample teacher module template
    teacher_template = pd.DataFrame({
        'Teacher Name': ['Alice', 'Bob', 'Carol'],
        'Module Code': ['M101', 'M102', 'M103'],
        'Module Name': ['Course 1', 'Course 2', 'Course 3']
    })
    
    # Sample student database template (Section now contains numbers instead of strings)
    student_template = pd.DataFrame({
        'Cohort': ['Cohort 1', 'Cohort 2', 'Cohort 1'],
        'Student Number': ['S001', 'S002', 'S003'],
        'Module Name': ['Course 1', 'Course 2', 'Course 3'],
        'Module Code': ['M101', 'M102', 'M103'],
        'Term': ['Term 1', 'Term 2', 'Term 3'],
        'Section': [1, 2, 3],  # Section is now numeric
        'Year': [2024, 2024, 2024]
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

# Function to calculate the workload
def calculate_workload(course_data, teacher_modules, student_db):
    # Clean column names to avoid issues with extra spaces
    course_data.columns = course_data.columns.str.strip()
    teacher_modules.columns = teacher_modules.columns.str.strip()
    student_db.columns = student_db.columns.str.strip()
    
    # Merge the dataframes: First merge course_data and teacher_modules on 'Module Code' and 'Module Name'
    merged_data = pd.merge(course_data, teacher_modules, on=['Module Code', 'Module Name'], how='inner')
    
    # Only keep the rows where the module has a cohort
    merged_data = merged_data[merged_data['Cohort'].notna() & (merged_data['Cohort'] != '')]
    
    # Filter student_db by the Cohort in the merged_data
    student_db_filtered = student_db[student_db['Cohort'].isin(merged_data['Cohort'].unique())]
    
    # Calculate the number of students per module (filtered by cohort)
    student_count = student_db_filtered.groupby(['Module Code', 'Module Name', 'Term']).size().reset_index(name='Number of Students')
    
    # Merge the student count into the merged_data DataFrame
    merged_data = pd.merge(merged_data, student_count, on=['Module Code', 'Module Name', 'Term'], how='inner')

    # Calculate the number of sections (classes) by dividing students by sections
    merged_data['Number of Sections'] = merged_data['Number of Students'] // 30  # Assuming max 30 students per section
    merged_data['Remaining Students'] = merged_data['Number of Students'] % 30  # Remaining students in the last section
    
    # Now we need to distribute the students across sections (classes)
    section_assignments = []
    for index, row in merged_data.iterrows():
        # Assign students to sections
        for section in range(1, row['Number of Sections'] + 1):
            section_assignments.append({'Module Code': row['Module Code'], 
                                        'Module Name': row['Module Name'], 
                                        'Term': row['Term'], 
                                        'Cohort': row['Cohort'],
                                        'Section': section, 
                                        'Students Assigned': 30})
        
        # If there are remaining students, assign them to a new section
        if row['Remaining Students'] > 0:
            section_assignments.append({'Module Code': row['Module Code'], 
                                        'Module Name': row['Module Name'], 
                                        'Term': row['Term'], 
                                        'Cohort': row['Cohort'],
                                        'Section': row['Number of Sections'] + 1, 
                                        'Students Assigned': row['Remaining Students']})

    # Create a DataFrame with section assignments
    section_data = pd.DataFrame(section_assignments)
    
    # Merge this section data back into the main merged_data
    merged_data = pd.merge(merged_data, section_data, on=['Module Code', 'Module Name', 'Term', 'Cohort'], how='left')

    # Add the number of hours based on credit value
    merged_data['Teaching Hours'] = merged_data['Credit'].apply(lambda x: 4 if x == 10 else (4 if x == 15 else 6))
    merged_data['Office Hours'] = merged_data['Credit'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 2))
    merged_data['Grading Hours'] = merged_data['Students Assigned'] * merged_data['Credit'].apply(
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

    # Group the data by Term and Teacher
    grouped_data = merged_data.groupby(['Term', 'Teacher Name', 'Module Code', 'Module Name', 'Cohort', 'Section']).agg(
        {
            'Students Assigned': 'sum',
            'Teaching Hours': 'sum',
            'Office Hours': 'sum',
            'Grading Hours': 'sum',
            'Research Hours': 'sum',
            'Meetings Hours': 'sum',
            'Curriculum Development Hours': 'sum',
            'Other Responsibilities Hours': 'sum',
            'Total Weekly Hours': 'sum',
            'Total Term Workload': 'sum'
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
    teacher_modules = pd.read_csv(teacher_file)
    course_data = pd.read_csv(course_file)
    student_db = pd.read_csv(student_file)
    
    # Calculate the workload
    workload_data = calculate_workload(course_data, teacher_modules, student_db)
    
    # Display the workload data
    st.subheader("Calculated Workload Data")
    st.dataframe(workload_data)

    # Optionally, you can display as a table or download as CSV
    st.download_button(
        label="Download Workload Data as CSV",
        data=workload_data.to_csv(index=False),
        file_name="calculated_workload.csv",
        mime="text/csv"
    )
