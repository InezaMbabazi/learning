import streamlit as st
import pandas as pd

# Define workload calculation rules
def calculate_workload(course_structure, student_database, teacher_module):
    # Merge the data for complete information
    merged_data = pd.merge(teacher_module, course_structure, on="Module Code")
    merged_data = pd.merge(merged_data, student_database, on="Module Code")

    # Workload calculation logic
    def compute_hours(row):
        teaching_hours = 0
        office_hours = 0
        grading_hours = 0

        if row["Credit"] == 10:
            teaching_hours = 4
            office_hours = 1
            grading_hours = 0.083 * row["Student Number"]
        elif row["Credit"] == 15:
            teaching_hours = 4
            office_hours = 2
            grading_hours = 0.083 * row["Student Number"]
        elif row["Credit"] == 20:
            teaching_hours = 6
            office_hours = 2
            grading_hours = 0.117 * row["Student Number"]

        return teaching_hours + office_hours + grading_hours

    # Apply workload calculation
    merged_data["Total Workload"] = merged_data.apply(compute_hours, axis=1)
    return merged_data

# Streamlit app
st.title("Teacher Workload Calculator")

# File upload
st.sidebar.header("Upload Files")
student_file = st.sidebar.file_uploader("Upload Student Database", type=["csv"])
teacher_file = st.sidebar.file_uploader("Upload Teacher Module Database", type=["csv"])
course_file = st.sidebar.file_uploader("Upload Course Structure", type=["csv"])

if student_file and teacher_file and course_file:
    # Load data
    student_database = pd.read_csv(student_file)
    teacher_module = pd.read_csv(teacher_file)
    course_structure = pd.read_csv(course_file)

    # Display uploaded data
    st.subheader("Uploaded Data")
    st.write("**Student Database:**")
    st.dataframe(student_database)
    st.write("**Teacher Module Database:**")
    st.dataframe(teacher_module)
    st.write("**Course Structure:**")
    st.dataframe(course_structure)

    # Calculate workload
    workload_data = calculate_workload(course_structure, student_database, teacher_module)

    # Display results
    st.subheader("Calculated Workload")
    st.dataframe(workload_data)
    
    # Option to download results
    csv = workload_data.to_csv(index=False)
    st.download_button(label="Download Workload Data as CSV", data=csv, file_name="workload_data.csv", mime="text/csv")
else:
    st.write("Please upload all required files to proceed.")
