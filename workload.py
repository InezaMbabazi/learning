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

    # Initialize tracking columns in the teacher dataframe
    if 'Assigned Modules' not in teachers_df.columns:
        teachers_df['Assigned Modules'] = 0
    if 'Weekly Assigned Hours' not in teachers_df.columns:
        teachers_df['Weekly Assigned Hours'] = 0
    if 'Yearly Assigned Hours' not in teachers_df.columns:
        teachers_df['Yearly Assigned Hours'] = 0

    # Preprocess Students Data
    students_df['Teaching Hours per Week'] = students_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    students_df['Office Hours per Week'] = students_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    students_df['Total Weekly Hours'] = students_df['Teaching Hours per Week'] + students_df['Office Hours per Week']

    # Threshold for assigning assistants
    large_class_threshold = 50

    # List to keep track of the modules assigned
    workload = []
    unassigned_modules = []

    for _, module in students_df.iterrows():
        num_students = module['Number of Students']
        num_sections = module['Sections']
        students_per_section = num_students / num_sections

        # Check if a class is large
        is_large_class = students_per_section > large_class_threshold

        # Find the main teacher for the module
        available_main_teachers = teachers_df[
            (teachers_df['Module Code'] == module['Code']) &
            (teachers_df['Teacher Status'] == 'Main Teacher') &
            (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
            (teachers_df['Assigned Modules'] < 3)
        ]

        assistant_teacher = None
        main_teacher = None

        if not available_main_teachers.empty:
            # Check if the main teacher can take more modules for the term
            for teacher in available_main_teachers.itertuples():
                if teacher.Assigned_Modules < 3:
                    main_teacher = teacher
                    teachers_df.loc[teacher.Index, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                    teachers_df.loc[teacher.Index, 'Assigned Modules'] += 1
                    break

            # If large class, assign an assistant teacher
            if is_large_class and main_teacher:
                available_assistants = teachers_df[
                    (teachers_df['Teacher Status'] == 'Assistant') &
                    (teachers_df['Weekly Assigned Hours'] < 12) &
                    (teachers_df['Assigned Modules'] < 3) &
                    (teachers_df['Teacher\'s Name'] != main_teacher["Teacher's Name"])
                ]
                if not available_assistants.empty:
                    assistant_teacher = available_assistants.iloc[0]["Teacher's Name"]

            if main_teacher:
                workload.append({
                    "Teacher's Name": main_teacher["Teacher's Name"],
                    "Assistant Teacher": assistant_teacher if is_large_class else "None",
                    "Module Name": module["Module Name"],
                    "Teaching Hours (Weekly)": module["Teaching Hours per Week"],
                    "Office Hours (Weekly)": module["Office Hours per Week"],
                    "Total Hours (Weekly)": module["Total Weekly Hours"],
                    "When to Take Place": module["When to Take Place"],
                    "Teacher Status": main_teacher['Teacher Status']
                })
        else:
            unassigned_modules.append(module)

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Calculate yearly workload
    yearly_workload = (
        workload_df.groupby("Teacher's Name")
        .agg({
            "Total Hours (Weekly)": "sum"
        })
        .reset_index()
    )
    yearly_workload["Yearly Hours"] = yearly_workload["Total Hours (Weekly)"] * 12

    # Display weekly workload
    st.write("Weekly Workload")
    st.dataframe(workload_df)

    # Display yearly workload
    st.write("Yearly Workload")
    st.dataframe(yearly_workload)

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

    # Teacher with the most weekly hours
    most_hours_teacher = workload_df.groupby("Teacher's Name").sum().reset_index().sort_values(
        "Total Hours (Weekly)", ascending=False).iloc[0]
    st.write("Teacher with the Most Weekly Hours")
    st.write(most_hours_teacher)

    # Unassigned modules report
    if unassigned_modules:
        unassigned_modules_df = pd.DataFrame(unassigned_modules)
        st.write("Unassigned Modules (if any)")
        st.dataframe(unassigned_modules_df)
        st.download_button(
            "Download Unassigned Modules",
            unassigned_modules_df.to_csv(index=False),
            "unassigned_modules.csv"
        )
