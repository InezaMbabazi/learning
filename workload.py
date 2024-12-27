import pandas as pd
import streamlit as st

# Streamlit app
st.title("Lecturer Workload Allocation with Reassignment")

# Upload files
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
student_file = st.file_uploader("Upload Students Database Template", type="csv")

if teacher_file and student_file:
    # Load data
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
        # Filter available teachers
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

    # Check for teachers exceeding the module limit in any term
    workload_df = pd.DataFrame(workload)
    module_reassignments = []

    for teacher_name, group in workload_df.groupby("Teacher's Name"):
        for when, term_group in group.groupby("When to Take Place"):
            if len(term_group) > 3:
                # Identify excess modules
                excess_modules = term_group.iloc[3:]

                for _, excess_module in excess_modules.iterrows():
                    # Reassign excess module
                    available_teachers = teachers_df[
                        (teachers_df['Weekly Assigned Hours'] + excess_module['Total Hours (Weekly)'] <= 12) &
                        (teachers_df['Assigned Modules'] < 3) &
                        (teachers_df["Teacher's Name"] != teacher_name)
                    ]

                    if not available_teachers.empty:
                        new_teacher = available_teachers.iloc[0]
                        teachers_df.loc[new_teacher.name, 'Weekly Assigned Hours'] += excess_module['Total Hours (Weekly)']
                        teachers_df.loc[new_teacher.name, 'Assigned Modules'] += 1

                        module_reassignments.append({
                            "Reassigned From": teacher_name,
                            "Reassigned To": new_teacher["Teacher's Name"],
                            "Module Name": excess_module["Module Name"],
                            "When to Take Place": excess_module["When to Take Place"]
                        })
                        workload_df.loc[excess_module.name, "Teacher's Name"] = new_teacher["Teacher's Name"]
                    else:
                        # If no available teacher, add to unassigned modules
                        unassigned_modules.append(excess_module.to_dict())

    # Convert reassignment data to DataFrame
    reassignment_df = pd.DataFrame(module_reassignments)
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

    st.write("Module Reassignments")
    st.dataframe(reassignment_df)

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
        "Download Module Reassignments",
        reassignment_df.to_csv(index=False),
        "module_reassignments.csv"
    )
    st.download_button(
        "Download Unassigned Modules",
        unassigned_modules_df.to_csv(index=False),
        "unassigned_modules.csv"
    )
