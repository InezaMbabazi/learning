import pandas as pd
import streamlit as st

# Streamlit app
st.title("Lecturer Workload Allocation Model")

# Upload files
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
student_file = st.file_uploader("Upload Students Database Template", type="csv")

if teacher_file and student_file:
    teachers_df = pd.read_csv(teacher_file)
    students_df = pd.read_csv(student_file)
    
    # Preprocess Students Data
    students_df['Sections'] = students_df['Number of Students'] // students_df['Sections']
    students_df['Weekly Hours'] = students_df['Credits'].apply(lambda x: 4 if x == 10 else (6 if x == 15 else 10))
    students_df['Office Hours'] = students_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    students_df['Total Weekly Hours'] = students_df['Weekly Hours'] + students_df['Office Hours']
    
    # Assign modules to teachers
    workload = []
    for _, module in students_df.iterrows():
        available_teachers = teachers_df[teachers_df['Module Code'] == module['Code']]
        for _, teacher in available_teachers.iterrows():
            if teacher['Total Assigned Hours'] + module['Total Weekly Hours'] <= 12:
                workload.append({
                    "Teacher's Name": teacher["Teacher's Name"],
                    "Module Name": module["Module Name"],
                    "Weekly Hours": module["Weekly Hours"],
                    "Office Hours": module["Office Hours"],
                    "When to Take Place": module["When to Take Place"]
                })
                teacher['Total Assigned Hours'] += module['Total Weekly Hours']
                break

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Display and download
    st.write("Workload Allocation")
    st.dataframe(workload_df)
    st.download_button("Download Workload Allocation", workload_df.to_csv(index=False), "workload_allocation.csv")
