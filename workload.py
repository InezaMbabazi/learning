import pandas as pd
import streamlit as st

# Streamlit app
st.title("Lecturer Workload Allocation")

# Upload files
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
student_file = st.file_uploader("Upload Students Database Template", type="csv")

if teacher_file and student_file:
    # Load the data
    teachers_df = pd.read_csv(teacher_file)
    students_df = pd.read_csv(student_file)

    # Initialize tracking columns
    teachers_df['Weekly Assigned Hours'] = 0
    teachers_df['Assigned Modules'] = 0

    # Preprocess Students Data
    students_df['Teaching Hours per Week'] = students_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    students_df['Office Hours per Week'] = students_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    students_df['Total Weekly Hours'] = students_df['Teaching Hours per Week'] + students_df['Office Hours per Week']

    # Track module assignments
    workload = []
    unassigned_modules = []

    for _, module in students_df.iterrows():
        # Find available teachers
        available_teachers = teachers_df[
            (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
            (teachers_df['Assigned Modules'] < 3)
        ]

        if not available_teachers.empty:
            # Assign to the first available teacher
            assigned_teacher = available_teachers.iloc[0]
            teachers_df.loc[assigned_teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
            teachers_df.loc[assigned_teacher.name, 'Assigned Modules'] += 1

            workload.append({
                "Teacher's Name": assigned_teacher["Teacher's Name"],
                "Module Name": module["Module Name"],
                "Teaching Hours (Weekly)": module["Teaching Hours per Week"],
                "Office Hours (Weekly)": module["Office Hours per Week"],
                "Total Hours (Weekly)": module["Total Weekly Hours"],
                "When to Take Place": module["When to Take Place"],
            })
        else:
            # Add to unassigned modules
            unassigned_modules.append(module.to_dict())

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Convert unassigned modules to DataFrame
    unassigned_modules_df = pd.DataFrame(unassigned_modules)

    # Calculate yearly workload
    yearly_workload = (
        workload_df.groupby("Teacher's Name")
        .agg({"Total Hours (Weekly)": "sum"})
        .reset_index()
    )
    yearly_workload["Yearly Hours"] = yearly_workload["Total Hours (Weekly)"] * 12

    # Display tables
    st.write("Weekly Workload")
    st.dataframe(workload_df)

    st.write("Yearly Workload")
    st.dataframe(yearly_workload)

    st.write("Unassigned Modules")
    st.dataframe(unassigned_modules_df)

    # Download buttons
    st.download_button(
        "Download Weekly Workload",
        workload_df.to_csv(index=False),
        "weekly_workload.csv"
    )
    st.download_button(
        "Download Yearly Workload",
        yearly_workload.to_csv(index=False),
        "yearly_workload.csv"
    )
    st.download_button(
        "Download Unassigned Modules",
        unassigned_modules_df.to_csv(index=False),
        "unassigned_modules.csv"
    )
