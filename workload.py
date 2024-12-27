import pandas as pd
import streamlit as st

# Streamlit app
st.title("Balanced Lecturer Workload Allocation")

# File upload
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
module_file = st.file_uploader("Upload Students Database Template", type="csv")

if teacher_file and module_file:
    # Load data
    teachers_df = pd.read_csv(teacher_file)
    modules_df = pd.read_csv(module_file)

    # Initialize teacher tracking columns
    teachers_df['Weekly Assigned Hours'] = 0
    teachers_df['Assigned Modules'] = 0

    # Preprocess modules data
    modules_df['Teaching Hours per Week'] = modules_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    modules_df['Office Hours per Week'] = modules_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    modules_df['Total Weekly Hours'] = modules_df['Teaching Hours per Week'] + modules_df['Office Hours per Week']

    # Initialize outputs
    workload = []
    unassigned_modules = []

    # Assign modules
    for _, module in modules_df.iterrows():
        assigned = False

        # Sort teachers by least workload and modules assigned
        available_teachers = teachers_df[
            (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
            (teachers_df['Assigned Modules'] < 3)
        ].sort_values(by=['Weekly Assigned Hours', 'Assigned Modules'])

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
            assigned = True

        if not assigned:
            # Add to unassigned modules if no teacher available
            unassigned_modules.append(module.to_dict())

    # Ensure no teacher exceeds 12 weekly hours in any "When to Take Place"
    reassignment_needed = []
    for teacher_name, group in pd.DataFrame(workload).groupby("Teacher's Name"):
        for term, term_group in group.groupby("When to Take Place"):
            if term_group['Total Hours (Weekly)'].sum() > 12:
                # Identify excess modules
                excess_hours = term_group['Total Hours (Weekly)'].sum() - 12
                while excess_hours > 0 and not term_group.empty:
                    # Reassign one module at a time
                    excess_module = term_group.iloc[-1]
                    term_group = term_group.iloc[:-1]  # Remove from current teacher
                    workload.remove(excess_module.to_dict())
                    excess_hours -= excess_module['Total Hours (Weekly)']

                    # Attempt to reassign
                    available_teachers = teachers_df[
                        (teachers_df['Weekly Assigned Hours'] + excess_module['Total Hours (Weekly)'] <= 12) &
                        (teachers_df['Assigned Modules'] < 3) &
                        (teachers_df["Teacher's Name"] != teacher_name)
                    ].sort_values(by=['Weekly Assigned Hours', 'Assigned Modules'])

                    if not available_teachers.empty:
                        new_teacher = available_teachers.iloc[0]
                        teachers_df.loc[new_teacher.name, 'Weekly Assigned Hours'] += excess_module['Total Hours (Weekly)']
                        teachers_df.loc[new_teacher.name, 'Assigned Modules'] += 1
                        workload.append({
                            "Teacher's Name": new_teacher["Teacher's Name"],
                            **excess_module.to_dict(),
                        })
                    else:
                        # Unassign if no teacher is available
                        unassigned_modules.append(excess_module.to_dict())

    # Convert workload and unassigned modules to DataFrames
    workload_df = pd.DataFrame(workload)
    unassigned_modules_df = pd.DataFrame(unassigned_modules)

    # Calculate yearly workload
    yearly_workload = (
        workload_df.groupby("Teacher's Name")
        .agg({"Total Hours (Weekly)": "sum"})
        .reset_index()
    )
    yearly_workload["Yearly Hours"] = yearly_workload["Total Hours (Weekly)"] * 12

    # Display results
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
