import pandas as pd
import streamlit as st

# Streamlit app
st.title("Interactive Lecturer Workload Allocation")

# Upload files
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
student_file = st.file_uploader("Upload Students Database Template", type="csv")

if teacher_file and student_file:
    # Load the data
    teachers_df = pd.read_csv(teacher_file)
    students_df = pd.read_csv(student_file)

    # Initialize tracking columns
    teachers_df['Weekly Assigned Hours'] = 0
    teachers_df['Yearly Assigned Hours'] = 0
    teachers_df['Assigned Modules'] = 0

    # Preprocess Students Data
    students_df['Teaching Hours per Week'] = students_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    students_df['Office Hours per Week'] = students_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    students_df['Total Weekly Hours'] = students_df['Teaching Hours per Week'] + students_df['Office Hours per Week']

    # Assign modules to teachers
    workload = []
    for _, module in students_df.iterrows():
        # Find the main teacher for the module
        available_main_teachers = teachers_df[
            (teachers_df['Teacher Status'] == 'Main Teacher') &
            (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
            (teachers_df['Assigned Modules'] < 3)
        ]
        assistant_teacher = None

        if not available_main_teachers.empty:
            main_teacher = available_main_teachers.iloc[0]
            teachers_df.loc[main_teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
            teachers_df.loc[main_teacher.name, 'Assigned Modules'] += 1

            workload.append({
                "Teacher's Name": main_teacher["Teacher's Name"],
                "Module Name": module["Module Name"],
                "Teaching Hours (Weekly)": module["Teaching Hours per Week"],
                "Office Hours (Weekly)": module["Office Hours per Week"],
                "Total Hours (Weekly)": module["Total Weekly Hours"],
                "When to Take Place": module["When to Take Place"],
                "Teacher Status": main_teacher['Teacher Status']
            })

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Display workload
    st.write("Current Workload")
    st.dataframe(workload_df)

    # Allow reassignment
    st.write("Reassign Teachers for Modules")
    for i, row in workload_df.iterrows():
        module_name = row['Module Name']
        current_teacher = row["Teacher's Name"]
        new_teacher = st.selectbox(
            f"Assign a new teacher for {module_name} (Current: {current_teacher})",
            teachers_df["Teacher's Name"].unique(),
            key=f"reassign_{i}"
        )

        # Update teacher if changed
        if new_teacher != current_teacher:
            old_teacher_idx = teachers_df[teachers_df["Teacher's Name"] == current_teacher].index[0]
            new_teacher_idx = teachers_df[teachers_df["Teacher's Name"] == new_teacher].index[0]

            # Adjust workloads
            teachers_df.loc[old_teacher_idx, 'Weekly Assigned Hours'] -= row["Total Hours (Weekly)"]
            teachers_df.loc[old_teacher_idx, 'Assigned Modules'] -= 1

            teachers_df.loc[new_teacher_idx, 'Weekly Assigned Hours'] += row["Total Hours (Weekly)"]
            teachers_df.loc[new_teacher_idx, 'Assigned Modules'] += 1

            # Update workload_df
            workload_df.at[i, "Teacher's Name"] = new_teacher

    # Display updated workloads
    st.write("Updated Workload")
    st.dataframe(workload_df)

    # Calculate yearly workload
    yearly_workload = (
        workload_df.groupby("Teacher's Name")
        .agg({"Total Hours (Weekly)": "sum"})
        .reset_index()
    )
    yearly_workload["Yearly Hours"] = yearly_workload["Total Hours (Weekly)"] * 12

    st.write("Yearly Workload")
    st.dataframe(yearly_workload)

    # Download buttons
    st.download_button(
        "Download Updated Workload",
        workload_df.to_csv(index=False),
        "updated_workload.csv"
    )
    st.download_button(
        "Download Yearly Workload",
        yearly_workload.to_csv(index=False),
        "yearly_workload.csv"
    )
