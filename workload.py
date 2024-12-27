import pandas as pd
import numpy as np
import streamlit as st

# Sample Data - replace with your actual data sources
teacher_data = {
    'Teacher\'s Name': ['John Doe', 'Jane Smith', 'Michael Johnson'],
    'Teacher Status': ['Main', 'Assistant', 'Main']
}

module_data = {
    'Module Name': ['Math 101', 'Physics 102', 'History 103'],
    'Module Code': ['M101', 'P102', 'H103'],
    'Credits': [10, 15, 20],  # Module credits
}

student_data = {
    'Cohort': [1, 1, 2],
    'Number of Students': [60, 50, 70],
    'Module Name': ['Math 101', 'Physics 102', 'History 103'],
    'Code': ['M101', 'P102', 'H103'],
    'Term': ['Term 1', 'Term 2', 'Term 3'],
    'Sections': [3, 2, 4],
    'Year': [2024, 2024, 2024],
    'Credits': [10, 15, 20],
    'Programme': ['Engineering', 'Science', 'Arts'],
    'When to Take Place': ['Term 1', 'Term 2', 'Term 3'],
}

# Convert data to DataFrames
teachers_df = pd.DataFrame(teacher_data)
modules_df = pd.DataFrame(module_data)
students_df = pd.DataFrame(student_data)

# Assigning Workload
def calculate_workload():
    # Initialize an empty list to store workload assignments
    workload = []

    for index, row in students_df.iterrows():
        num_students = row['Number of Students']
        num_sections = row['Sections']
        students_per_section = num_students / num_sections

        # Get the corresponding module data
        module = modules_df[modules_df['Module Name'] == row['Module Name']].iloc[0]
        credits = module['Credits']

        # Calculate teaching and office hours based on credits
        if credits == 10:
            teaching_hours = 4
            office_hours = 1
        elif credits == 15:
            teaching_hours = 4
            office_hours = 2
        elif credits == 20:
            teaching_hours = 6
            office_hours = 4

        total_weekly_hours = teaching_hours + office_hours

        # Find an available teacher for this module
        available_teachers = teachers_df[teachers_df['Teacher Status'] == 'Main']
        assigned_teacher = available_teachers.iloc[0]  # Just pick the first available teacher
        assistant_teacher = teachers_df[teachers_df['Teacher Status'] == 'Assistant'].iloc[0]  # Pick assistant
        
        # Assign the workload
        workload.append({
            'Teacher\'s Name': assigned_teacher['Teacher\'s Name'],
            'Module Name': row['Module Name'],
            'Credits': credits,
            'Total Weekly Hours': total_weekly_hours,
            'When to Take Place': row['When to Take Place'],
            'Assistant Teacher': assistant_teacher['Teacher\'s Name']
        })

    return pd.DataFrame(workload)

# Calculate the initial workload
workload_df = calculate_workload()

# Display the initial workload
st.write("### Initial Workload Assignment")
st.dataframe(workload_df)

# Option to edit the workload
st.write("### Edit Workload Entry")
with st.form("edit_workload"):
    selected_index = st.selectbox(
        "Select Row to Edit",
        options=workload_df.index,
        format_func=lambda x: f"{workload_df.loc[x, \"Teacher's Name\"]} - {workload_df.loc[x, 'Module Name']}"
    )
    new_teacher = st.text_input("Teacher's Name", workload_df.loc[selected_index, "Teacher's Name"])
    new_assistant = st.text_input("Assistant Teacher", workload_df.loc[selected_index, "Assistant Teacher"])
    new_when_to_take_place = st.selectbox(
        "When to Take Place",
        options=workload_df["When to Take Place"].unique(),
        index=list(workload_df["When to Take Place"].unique()).index(
            workload_df.loc[selected_index, "When to Take Place"]
        )
    )
    submit_edit = st.form_submit_button("Update Entry")

    if submit_edit:
        workload_df.loc[selected_index, "Teacher's Name"] = new_teacher
        workload_df.loc[selected_index, "Assistant Teacher"] = new_assistant
        workload_df.loc[selected_index, "When to Take Place"] = new_when_to_take_place
        st.success("Entry updated successfully!")
        st.experimental_rerun()  # Refresh the app to reflect changes

# Calculate the weekly and yearly workload for each teacher
def calculate_teacher_workload(workload_df):
    weekly_workload = workload_df.groupby(['Teacher\'s Name', 'When to Take Place']).agg({
        'Total Weekly Hours': 'sum'
    }).reset_index()

    yearly_workload = workload_df.groupby('Teacher\'s Name').agg({
        'Total Weekly Hours': 'sum'
    }).reset_index()
    yearly_workload['Total Yearly Hours'] = yearly_workload['Total Weekly Hours'] * 12  # Assuming 12 weeks per term

    return weekly_workload, yearly_workload

# Calculate weekly and yearly workload
weekly_workload, yearly_workload = calculate_teacher_workload(workload_df)

# Display weekly and yearly workload
st.write("### Weekly Workload")
st.dataframe(weekly_workload)

st.write("### Yearly Workload")
st.dataframe(yearly_workload)

# Optionally, you could show the teacher with the most weekly hours
max_weekly_teacher = weekly_workload.loc[weekly_workload['Total Weekly Hours'].idxmax()]
st.write(f"### Teacher with the Most Weekly Hours: {max_weekly_teacher['Teacher\'s Name']} - {max_weekly_teacher['Total Weekly Hours']} hours")
