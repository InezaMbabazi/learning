import pandas as pd
import streamlit as st

# Streamlit app
st.title("Lecturer Workload Allocation Model")

# Upload files
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
student_file = st.file_uploader("Upload Students Database Template", type="csv")

if teacher_file and student_file:
    # Load the data
    teachers_df = pd.read_csv(teacher_file)
    students_df = pd.read_csv(student_file)
    
    # Initialize a column to track assigned hours for each teacher
    teachers_df['Total Assigned Hours'] = 0
    
    # Preprocess Students Data
    students_df['Sections'] = students_df['Number of Students'] // students_df['Sections']
    students_df['Weekly Hours'] = students_df['Credits'].apply(lambda x: 4 if x == 10 else (6 if x == 15 else 10))
    students_df['Office Hours'] = students_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    students_df['Total Weekly Hours'] = students_df['Weekly Hours'] + students_df['Office Hours']
    
    # Assign modules to teachers
    workload = []
    for _, module in students_df.iterrows():
        available_teachers = teachers_df[teachers_df['Module Code'] == module['Code']]
        for _, teacher in available_teachers.iterrows():
            if teacher['Total Assigned Hours'] + module['Total Weekly Hours'] <= 12:
                workload.append({
                    "Teacher's Name": teacher["Teacher's Name"],
                    "Module Name": module["Module Name"],
                    "Weekly Hours": module["Weekly Hours"],
                    "Office Hours": module["Office Hours"],
                    "Total Weekly Hours": module["Total Weekly Hours"],
                    "When to Take Place": module["When to Take Place"]
                })
                # Update teacher's assigned hours
                teachers_df.loc[teacher.name, 'Total Assigned Hours'] += module['Total Weekly Hours']
                break

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Aggregate total hours per teacher by `When to Take Place`
    total_hours_df = (
        workload_df.groupby(["Teacher's Name", "When to Take Place"])
        .agg(
            Total_Teaching_Hours=("Weekly Hours", "sum"),
            Total_Office_Hours=("Office Hours", "sum"),
            Total_Hours=("Total Weekly Hours", "sum"),
        )
        .reset_index()
    )

    # Display the workload allocation and aggregated total hours
    st.write("Workload Allocation")
    st.dataframe(workload_df)

    st.write("Total Hours per Teacher per 'When to Take Place'")
    st.dataframe(total_hours_df)

    # Allow download of both tables
    st.download_button(
        "Download Workload Allocation",
        workload_df.to_csv(index=False),
        "workload_allocation.csv",
    )
    st.download_button(
        "Download Total Hours Summary",
        total_hours_df.to_csv(index=False),
        "total_hours_summary.csv",
    )
