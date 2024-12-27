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
            weekly_hours = module['Teaching Hours per Week'] + module['Office Hours per Week']
            if teacher['Total Assigned Hours'] + weekly_hours <= 12:
                workload.append({
                    "Teacher's Name": teacher["Teacher's Name"],
                    "Module Name": module["Module Name"],
                    "Teaching Hours (Weekly)": module["Teaching Hours per Week"],
                    "Office Hours (Weekly)": module["Office Hours per Week"],
                    "Total Hours (Weekly)": weekly_hours,
                    "When to Take Place": module["When to Take Place"]
                })
                teachers_df.loc[teacher.name, 'Total Assigned Hours'] += weekly_hours
                break

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Weekly workload by teacher and When to Take Place
    weekly_workload = workload_df.groupby(["Teacher's Name", "When to Take Place"]).agg(
        Modules=pd.NamedAgg(column="Module Name", aggfunc="count"),
        Total_Teaching_Hours_Weekly=pd.NamedAgg(column="Teaching Hours (Weekly)", aggfunc="sum"),
        Total_Office_Hours_Weekly=pd.NamedAgg(column="Office Hours (Weekly)", aggfunc="sum"),
        Total_Hours_Weekly=pd.NamedAgg(column="Total Hours (Weekly)", aggfunc="sum")
    ).reset_index()

    # Yearly workload by teacher
    yearly_workload = weekly_workload.groupby("Teacher's Name").agg(
        Total_Terms=pd.NamedAgg(column="When to Take Place", aggfunc="count"),
        Yearly_Teaching_Hours=pd.NamedAgg(column="Total_Teaching_Hours_Weekly", aggfunc=lambda x: sum(x) * 3),
        Yearly_Office_Hours=pd.NamedAgg(column="Total_Office_Hours_Weekly", aggfunc=lambda x: sum(x) * 3),
        Yearly_Total_Hours=pd.NamedAgg(column="Total_Hours_Weekly", aggfunc=lambda x: sum(x) * 3)
    ).reset_index()

    # Display tables in Streamlit
    st.write("Weekly Workload by Teacher and When to Take Place")
    st.dataframe(weekly_workload)
    st.download_button(
        "Download Weekly Workload",
        weekly_workload.to_csv(index=False),
        "weekly_workload.csv"
    )

    st.write("Yearly Workload by Teacher")
    st.dataframe(yearly_workload)
    st.download_button(
        "Download Yearly Workload",
        yearly_workload.to_csv(index=False),
        "yearly_workload.csv"
    )
