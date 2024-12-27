import pandas as pd
import streamlit as st

# Streamlit app
st.title("Enhanced Lecturer Workload Allocation with Assistants")

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
    students_df['Yearly Hours'] = students_df['Total Weekly Hours'] * 12

    # Threshold for assigning assistants
    large_class_threshold = 50

    # Assign modules to teachers
    workload = []
    for _, module in students_df.iterrows():
        num_students = module['Number of Students']
        num_sections = module['Sections']
        students_per_section = num_students / num_sections

        # Check if a class is large
        is_large_class = students_per_section > large_class_threshold

        # Find the main teacher for the module
        available_teachers = teachers_df[teachers_df['Module Code'] == module['Code']]
        assistant_teacher = None

        for _, teacher in available_teachers.iterrows():
            weekly_hours = teacher['Weekly Assigned Hours'] + module['Teaching Hours per Week']
            assigned_modules = teacher['Assigned Modules'] + 1

            if weekly_hours <= 12 and assigned_modules <= 3:
                teachers_df.loc[teacher.name, 'Weekly Assigned Hours'] += module['Teaching Hours per Week']
                teachers_df.loc[teacher.name, 'Yearly Assigned Hours'] = teachers_df.loc[teacher.name, 'Weekly Assigned Hours'] * 12
                teachers_df.loc[teacher.name, 'Assigned Modules'] += 1

                # If large class, find an assistant
                if is_large_class:
                    assistant_available = teachers_df[
                        (teachers_df['Weekly Assigned Hours'] < 12) & 
                        (teachers_df['Assigned Modules'] < 3) & 
                        (teachers_df['Teacher\'s Name'] != teacher["Teacher's Name"])
                    ]
                    if not assistant_available.empty:
                        assistant_teacher = assistant_available.iloc[0]["Teacher's Name"]

                workload.append({
                    "Teacher's Name": teacher["Teacher's Name"],
                    "Assistant Teacher": assistant_teacher if is_large_class else "None",
                    "Module Name": module["Module Name"],
                    "Teaching Hours (Weekly)": module["Teaching Hours per Week"],
                    "Office Hours (Weekly)": module["Office Hours per Week"],
                    "Total Hours (Weekly)": module["Total Weekly Hours"],
                    "Yearly Hours": module["Yearly Hours"],
                    "When to Take Place": module["When to Take Place"]
                })
                break

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Display workload
    st.write("Workload with Assistants")
    st.dataframe(workload_df)
    st.download_button(
        "Download Workload",
        workload_df.to_csv(index=False),
        "workload_with_assistants.csv"
    )

    # Teacher with the most weekly hours
    most_hours_teacher = teachers_df.loc[teachers_df['Weekly Assigned Hours'].idxmax()]
    st.write("Teacher with the Most Weekly Hours")
    st.write(most_hours_teacher)

    # Unassigned modules
    unassigned_modules = students_df[~students_df['Module Name'].isin(workload_df['Module Name'])]
    st.write("Unassigned Modules (if any)")
    st.dataframe(unassigned_modules)
    if not unassigned_modules.empty:
        st.download_button(
            "Download Unassigned Modules",
            unassigned_modules.to_csv(index=False),
            "unassigned_modules.csv"
        )
