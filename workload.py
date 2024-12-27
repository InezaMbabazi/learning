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
    teachers_df['Weekly Modules'] = ""

    # Preprocess Students Data
    students_df['Sections'] = students_df['Number of Students'] // students_df['Sections']
    students_df['Teaching Hours per Week'] = students_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    students_df['Office Hours per Week'] = students_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    students_df['Teaching Hours per Term'] = students_df['Teaching Hours per Week'] * 12
    students_df['Office Hours per Term'] = students_df['Office Hours per Week'] * 12
    students_df['Total Hours per Term'] = students_df['Teaching Hours per Term'] + students_df['Office Hours per Term']
    
    # Assign modules to teachers
    workload = []
    for _, module in students_df.iterrows():
        available_teachers = teachers_df[teachers_df['Module Code'] == module['Code']]
        for _, teacher in available_teachers.iterrows():
            if teacher['Total Assigned Hours'] + module['Total Hours per Term'] <= 12 * 12:
                workload.append({
                    "Teacher's Name": teacher["Teacher's Name"],
                    "Module Name": module["Module Name"],
                    "Teaching Hours": module["Teaching Hours per Term"],
                    "Office Hours": module["Office Hours per Term"],
                    "Total Hours": module["Total Hours per Term"],
                    "When to Take Place": module["When to Take Place"]
                })
                
                # Update the teacher's total assigned hours and weekly modules
                teachers_df.loc[teacher.name, 'Total Assigned Hours'] += module['Total Hours per Term']
                teachers_df.loc[teacher.name, 'Weekly Modules'] += f"{module['Module Name']} (Teaching: {module['Teaching Hours per Term']} hrs, Office: {module['Office Hours per Term']} hrs), "
                break

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Group workload by teacher and When to Take Place
    grouped_workload = workload_df.groupby(["Teacher's Name", "When to Take Place"]).agg(
        Total_Teaching_Hours=pd.NamedAgg(column="Teaching Hours", aggfunc="sum"),
        Total_Office_Hours=pd.NamedAgg(column="Office Hours", aggfunc="sum"),
        Total_Hours=pd.NamedAgg(column="Total Hours", aggfunc="sum")
    ).reset_index()

    # Filter teachers who exceed 12 hours per week
    grouped_workload = grouped_workload[grouped_workload['Total_Teaching_Hours'] <= 12]

    # Display grouped workload
    st.write("Grouped Workload by Teacher and When to Take Place (with Modules Assigned)")
    st.dataframe(grouped_workload)

    # Weekly workload for each teacher (grouped by When to Take Place)
    weekly_workload = grouped_workload.copy()
    weekly_workload['Weekly_Teaching_Hours'] = weekly_workload['Total_Teaching_Hours'] / 12
    weekly_workload['Weekly_Office_Hours'] = weekly_workload['Total_Office_Hours'] / 12
    weekly_workload['Weekly_Total_Hours'] = weekly_workload['Total_Hours'] / 12

    # Yearly workload for each teacher
    yearly_workload = grouped_workload.groupby("Teacher's Name").agg(
        Yearly_Teaching_Hours=pd.NamedAgg(column="Total_Teaching_Hours", aggfunc="sum"),
        Yearly_Office_Hours=pd.NamedAgg(column="Total_Office_Hours", aggfunc="sum"),
        Yearly_Total_Hours=pd.NamedAgg(column="Total_Hours", aggfunc="sum")
    ).reset_index()

    # Display weekly workload
    st.write("Weekly Workload by Teacher and When to Take Place (Modules Included)")
    st.dataframe(weekly_workload)
    st.download_button(
        "Download Weekly Workload",
        weekly_workload.to_csv(index=False),
        "weekly_workload.csv"
    )

    # Display yearly workload
    st.write("Yearly Workload by Teacher")
    st.dataframe(yearly_workload)
    st.download_button(
        "Download Yearly Workload",
        yearly_workload.to_csv(index=False),
        "yearly_workload.csv"
    )
