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
    teachers_df['Weekly Assigned Hours'] = 0
    
    # Preprocess Students Data
    students_df['Sections'] = students_df['Number of Students'] // students_df['Sections']
    students_df['Teaching Hours per Week'] = students_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    students_df['Office Hours per Week'] = students_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    students_df['Total Weekly Hours'] = students_df['Teaching Hours per Week'] + students_df['Office Hours per Week']
    
    # Assign modules to teachers, ensuring no teacher exceeds 12 hours per week
    workload = []
    for _, module in students_df.iterrows():
        available_teachers = teachers_df[teachers_df['Module Code'] == module['Code']]
        for _, teacher in available_teachers.iterrows():
            if teacher['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12:
                workload.append({
                    "Teacher's Name": teacher["Teacher's Name"],
                    "Module Name": module["Module Name"],
                    "Teaching Hours per Week": module["Teaching Hours per Week"],
                    "Office Hours per Week": module["Office Hours per Week"],
                    "Total Weekly Hours": module["Total Weekly Hours"],
                    "When to Take Place": module["When to Take Place"]
                })
                teachers_df.loc[teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                break

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Weekly workload grouped by teacher and When to Take Place
    weekly_workload = workload_df.groupby(["Teacher's Name", "When to Take Place"]).agg(
        Modules=pd.NamedAgg(column="Module Name", aggfunc=lambda x: ', '.join(x)),
        Weekly_Teaching_Hours=pd.NamedAgg(column="Teaching Hours per Week", aggfunc="sum"),
        Weekly_Office_Hours=pd.NamedAgg(column="Office Hours per Week", aggfunc="sum"),
        Weekly_Total_Hours=pd.NamedAgg(column="Total Weekly Hours", aggfunc="sum")
    ).reset_index()

    # Ensure no teacher exceeds 12 weekly hours in validation
    weekly_workload = weekly_workload[weekly_workload['Weekly_Total_Hours'] <= 12]

    # Yearly workload for each teacher
    yearly_workload = workload_df.groupby("Teacher's Name").agg(
        Yearly_Teaching_Hours=pd.NamedAgg(column="Teaching Hours per Week", aggfunc="sum"),
        Yearly_Office_Hours=pd.NamedAgg(column="Office Hours per Week", aggfunc="sum"),
        Yearly_Total_Hours=pd.NamedAgg(column="Total Weekly Hours", aggfunc="sum")
    ).reset_index()
    yearly_workload[['Yearly_Teaching_Hours', 'Yearly_Office_Hours', 'Yearly_Total_Hours']] *= 12

    # Display weekly workload
    st.write("Weekly Workload by Teacher and When to Take Place")
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
