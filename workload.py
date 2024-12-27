import pandas as pd
import streamlit as st

# Streamlit app
st.title("Enhanced Lecturer Workload Allocation Model with Assistants")

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
    students_df['Teaching Hours per Term'] = students_df['Teaching Hours per Week'] * 12
    students_df['Office Hours per Term'] = students_df['Office Hours per Week'] * 12
    students_df['Total Hours per Term'] = students_df['Teaching Hours per Term'] + students_df['Office Hours per Term']

    # Threshold for assigning assistants (number of students per section)
    large_class_threshold = 50

    # Assign modules to teachers with constraints
    workload = []
    for _, module in students_df.iterrows():
        num_students = module['Number of Students']
        num_sections = module['Sections']
        students_per_section = num_students / num_sections

        # Check if a class is large
        is_large_class = students_per_section > large_class_threshold

        available_teachers = teachers_df[teachers_df['Module Code'] == module['Code']]
        for _, teacher in available_teachers.iterrows():
            weekly_hours = teacher['Weekly Assigned Hours'] + module['Teaching Hours per Week']
            yearly_hours = teacher['Yearly Assigned Hours'] + module['Total Hours per Term']
            assigned_modules = teacher['Assigned Modules'] + 1
            
            if weekly_hours <= 12 and assigned_modules <= 3 and yearly_hours <= 3 * 12 * 12:
                workload.append({
                    "Teacher's Name": teacher["Teacher's Name"],
                    "Module Name": module["Module Name"],
                    "Teaching Hours (Weekly)": module["Teaching Hours per Week"],
                    "Office Hours (Weekly)": module["Office Hours per Week"],
                    "Total Hours (Weekly)": module["Teaching Hours per Week"] + module["Office Hours per Week"],
                    "When to Take Place": module["When to Take Place"],
                    "Assisted by": "Assistant" if is_large_class else "None"
                })
                
                teachers_df.loc[teacher.name, 'Weekly Assigned Hours'] += module['Teaching Hours per Week']
                teachers_df.loc[teacher.name, 'Yearly Assigned Hours'] += module['Total Hours per Term']
                teachers_df.loc[teacher.name, 'Assigned Modules'] += 1
                break

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Group workload by teacher and When to Take Place
    grouped_workload = workload_df.groupby(["Teacher's Name", "When to Take Place"]).agg(
        Total_Teaching_Hours=pd.NamedAgg(column="Teaching Hours (Weekly)", aggfunc="sum"),
        Total_Office_Hours=pd.NamedAgg(column="Office Hours (Weekly)", aggfunc="sum"),
        Total_Hours=pd.NamedAgg(column="Total Hours (Weekly)", aggfunc="sum"),
        Assigned_Modules=pd.NamedAgg(column="Module Name", aggfunc="count")
    ).reset_index()

    # Yearly workload for each teacher
    yearly_workload = grouped_workload.groupby("Teacher's Name").agg(
        Yearly_Teaching_Hours=pd.NamedAgg(column="Total_Teaching_Hours", aggfunc="sum"),
        Yearly_Office_Hours=pd.NamedAgg(column="Total_Office_Hours", aggfunc="sum"),
        Yearly_Total_Hours=pd.NamedAgg(column="Total_Hours", aggfunc="sum"),
        Total_Modules=pd.NamedAgg(column="Assigned_Modules", aggfunc="sum")
    ).reset_index()

    # Display grouped workload
    st.write("Grouped Weekly Workload by Teacher and When to Take Place")
    st.dataframe(grouped_workload)
    st.download_button(
        "Download Weekly Workload",
        grouped_workload.to_csv(index=False),
        "grouped_weekly_workload.csv"
    )

    # Display yearly workload
    st.write("Yearly Workload by Teacher")
    st.dataframe(yearly_workload)
    st.download_button(
        "Download Yearly Workload",
        yearly_workload.to_csv(index=False),
        "yearly_workload.csv"
    )

    # Display teacher with the most weekly hours
    max_weekly_hours_teacher = grouped_workload.loc[grouped_workload['Total_Hours'].idxmax()]
    st.write("Teacher with the Most Weekly Hours")
    st.write(max_weekly_hours_teacher)

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
