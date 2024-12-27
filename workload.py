import pandas as pd
import streamlit as st

# Streamlit app
st.title("Enhanced Lecturer Workload Allocation")

# File upload
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
module_file = st.file_uploader("Upload Modules Database Template", type="csv")

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
    modules_df['Class Size'] = modules_df['Number of Students'] / modules_df['Sections']
    modules_df['Assigned Teacher'] = None
    modules_df['Assistant Teacher'] = None

    # Assign modules to teachers
    for idx, module in modules_df.iterrows():
        assigned = False

        # Find eligible teachers for assignment
        eligible_teachers = teachers_df[
            (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
            (teachers_df['Assigned Modules'] < 3)
        ].sort_values(by=['Weekly Assigned Hours', 'Assigned Modules'])

        if not eligible_teachers.empty:
            # Assign the module to the first eligible teacher
            teacher = eligible_teachers.iloc[0]
            teachers_df.loc[teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
            teachers_df.loc[teacher.name, 'Assigned Modules'] += 1
            modules_df.at[idx, 'Assigned Teacher'] = teacher["Teacher's Name"]
            assigned = True

            # Assign assistant teacher for large classes
            if module['Class Size'] > 50:
                assistant_candidates = teachers_df[
                    (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
                    (teachers_df['Assigned Modules'] < 3) &
                    (teachers_df["Teacher's Name"] != teacher["Teacher's Name"])
                ].sort_values(by=['Weekly Assigned Hours', 'Assigned Modules'])

                if not assistant_candidates.empty:
                    assistant_teacher = assistant_candidates.iloc[0]
                    modules_df.at[idx, 'Assistant Teacher'] = assistant_teacher["Teacher's Name"]
                    teachers_df.loc[assistant_teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']

        if not assigned:
            # Log module as unassigned if no teacher is available
            modules_df.at[idx, 'Assigned Teacher'] = 'Unassigned'

    # Ensure no teacher exceeds the weekly limit
    for teacher_name, teacher_data in teachers_df.iterrows():
        if teacher_data['Weekly Assigned Hours'] > 12:
            excess_hours = teacher_data['Weekly Assigned Hours'] - 12
            for idx, module in modules_df[modules_df['Assigned Teacher'] == teacher_name].iterrows():
                if excess_hours <= 0:
                    break
                if module['Total Weekly Hours'] <= excess_hours:
                    # Reassign module
                    eligible_teachers = teachers_df[
                        (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
                        (teachers_df['Assigned Modules'] < 3) &
                        (teachers_df["Teacher's Name"] != teacher_name)
                    ].sort_values(by=['Weekly Assigned Hours', 'Assigned Modules'])

                    if not eligible_teachers.empty:
                        new_teacher = eligible_teachers.iloc[0]
                        modules_df.at[idx, 'Assigned Teacher'] = new_teacher["Teacher's Name"]
                        teachers_df.loc[new_teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                        teachers_df.loc[new_teacher.name, 'Assigned Modules'] += 1
                        teachers_df.loc[teacher_data.name, 'Weekly Assigned Hours'] -= module['Total Weekly Hours']
                        excess_hours -= module['Total Weekly Hours']

    # Check for any teacher exceeding 12 hours and fix
    for teacher_name, teacher_data in teachers_df.iterrows():
        if teacher_data['Weekly Assigned Hours'] > 12:
            excess_hours = teacher_data['Weekly Assigned Hours'] - 12
            for idx, module in modules_df[modules_df['Assigned Teacher'] == teacher_name].iterrows():
                if excess_hours <= 0:
                    break
                if module['Total Weekly Hours'] <= excess_hours:
                    # Reassign module
                    eligible_teachers = teachers_df[
                        (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
                        (teachers_df['Assigned Modules'] < 3) &
                        (teachers_df["Teacher's Name"] != teacher_name)
                    ].sort_values(by=['Weekly Assigned Hours', 'Assigned Modules'])

                    if not eligible_teachers.empty:
                        new_teacher = eligible_teachers.iloc[0]
                        modules_df.at[idx, 'Assigned Teacher'] = new_teacher["Teacher's Name"]
                        teachers_df.loc[new_teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                        teachers_df.loc[new_teacher.name, 'Assigned Modules'] += 1
                        teachers_df.loc[teacher_data.name, 'Weekly Assigned Hours'] -= module['Total Weekly Hours']
                        excess_hours -= module['Total Weekly Hours']

    # Generate outputs
    unassigned_modules = modules_df[modules_df['Assigned Teacher'] == 'Unassigned']
    workload_df = modules_df[modules_df['Assigned Teacher'] != 'Unassigned']

    # Calculate yearly workload
    yearly_workload = (
        workload_df.groupby("Assigned Teacher")
        .agg({"Total Weekly Hours": "sum"})
        .reset_index()
    )
    yearly_workload["Yearly Hours"] = yearly_workload["Total Weekly Hours"] * 12

    # Display results
    st.write("Assigned Workload")
    st.dataframe(workload_df)

    st.write("Yearly Workload")
    st.dataframe(yearly_workload)

    st.write("Unassigned Modules")
    st.dataframe(unassigned_modules)

    # Download buttons
    st.download_button(
        "Download Assigned Workload",
        workload_df.to_csv(index=False),
        "assigned_workload.csv"
    )
    st.download_button(
        "Download Yearly Workload",
        yearly_workload.to_csv(index=False),
        "yearly_workload.csv"
    )
    st.download_button(
        "Download Unassigned Modules",
        unassigned_modules.to_csv(index=False),
        "unassigned_modules.csv"
    )
