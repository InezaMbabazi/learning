import pandas as pd
import streamlit as st

# Sample data for teaching modules and students
# Teacher database (for demonstration purposes)
teacher_data = {
    'Teacher Name': ['John Doe', 'Jane Smith', 'Alice Brown'],
    'Teacher Status': ['Main', 'Main', 'Assistant'],
    'Total Assigned Hours': [0, 0, 0]
}

# Student database (for demonstration purposes)
student_data = {
    'Cohort': ['Cohort 1', 'Cohort 2', 'Cohort 3'],
    'Number of Students': [40, 50, 60],
    'Module Name': ['Math 101', 'Science 101', 'History 101'],
    'Code': ['MATH101', 'SCI101', 'HIST101'],
    'Term': ['Term 1', 'Term 1', 'Term 1'],
    'Sections': [2, 2, 3],
    'Year': [2024, 2024, 2024],
    'Credits': [10, 15, 20],
    'Programme': ['BSc', 'BSc', 'BA'],
    'When to Take Place': ['Week 1', 'Week 1', 'Week 2']
}

# Convert to DataFrames
teacher_df = pd.DataFrame(teacher_data)
student_df = pd.DataFrame(student_data)

# Define function to calculate weekly workload for each teacher
def calculate_workload(student_df, teacher_df):
    # Define the teaching hours based on credits
    teaching_hours = {10: 4, 15: 4, 20: 6}
    office_hours = {10: 1, 15: 2, 20: 4}
    
    # Add columns to student dataframe for weekly hours calculation
    student_df['Weekly Teaching Hours'] = student_df['Credits'].map(teaching_hours)
    student_df['Weekly Office Hours'] = student_df['Credits'].map(office_hours)
    
    # Group by teacher and "When to Take Place" and assign workload
    workload_data = []

    for index, row in student_df.iterrows():
        # Get the teacher
        available_teachers = teacher_df[teacher_df['Total Assigned Hours'] < 12]
        
        # Assign teachers and assistants
        for teacher_index, teacher_row in available_teachers.iterrows():
            if teacher_row['Total Assigned Hours'] + row['Weekly Teaching Hours'] <= 12:
                # Update teacher workload
                teacher_df.at[teacher_index, 'Total Assigned Hours'] += row['Weekly Teaching Hours']
                
                # Assign main teacher and assistant
                workload_data.append({
                    'Teacher\'s Name': teacher_row['Teacher Name'],
                    'Module Name': row['Module Name'],
                    'Credits': row['Credits'],
                    'Weekly Teaching Hours': row['Weekly Teaching Hours'],
                    'Weekly Office Hours': row['Weekly Office Hours'],
                    'When to Take Place': row['When to Take Place'],
                    'Assistant Teacher': 'N/A' if teacher_row['Teacher Status'] == 'Main' else 'Assistant',
                })
                break

    # Create a DataFrame for workload
    workload_df = pd.DataFrame(workload_data)
    
    # Calculate Year Workload by multiplying weekly hours by 12
    workload_df['Year Teaching Hours'] = workload_df['Weekly Teaching Hours'] * 12
    workload_df['Year Office Hours'] = workload_df['Weekly Office Hours'] * 12
    
    return workload_df

# Calculate workload
workload_df = calculate_workload(student_df, teacher_df)

# Display the workload table
st.write("### Teacher Workload Table")
st.dataframe(workload_df)

# Form to edit workload entries
st.write("### Edit Workload Entry")
with st.form("edit_workload"):
    selected_index = st.selectbox(
        "Select Row to Edit",
        options=workload_df.index,
        format_func=lambda x: f"{workload_df.loc[x, 'Teacher\'s Name']} - {workload_df.loc[x, 'Module Name']}"
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
        st.experimental_rerun()  # Refresh app

# Show teacher with the highest workload in a week
teacher_max_workload = teacher_df.loc[teacher_df['Total Assigned Hours'].idxmax()]
st.write("### Teacher with Maximum Weekly Hours")
st.write(f"Teacher: {teacher_max_workload['Teacher Name']}, Total Weekly Hours: {teacher_max_workload['Total Assigned Hours']}")
