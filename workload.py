import pandas as pd
import streamlit as st

# Define workload calculation functions
def calculate_workload(row, students):
    credits = row['Credits']
    if credits == 10:
        teaching_hours = 4
        office_hours = 1
        grading_hours = 0.083 * students
    elif credits == 15:
        teaching_hours = 4
        office_hours = 2
        grading_hours = 0.083 * students
    elif credits == 20:
        teaching_hours = 6
        office_hours = 2
        grading_hours = 0.117 * students
    else:
        teaching_hours = office_hours = grading_hours = 0  # Undefined credit hours
    
    return teaching_hours, office_hours, grading_hours

# Generate templates for download
def generate_template(template_type):
    if template_type == "student":
        data = {
            'Module Code': ['MOD101', 'MOD102'],
            'Student Number': [30, 25]
        }
    elif template_type == "teacher":
        data = {
            'Module Code': ['MOD101', 'MOD102'],
            'Teacher Name': ['John Doe', 'Jane Smith'],
            'Credits': [10, 15],
            'Term': ['TERM 1', 'TERM 2']
        }
    return pd.DataFrame(data)

# Enforce maximum 12 teaching hours per week and reassign excess
def enforce_teaching_limit_and_reassign(merged_data):
    teacher_workloads = {}

    # Process each row
    for index, row in merged_data.iterrows():
        teacher = row['Teacher Name']
        module = row['Module Code']
        term = row['Term']
        teaching_hours = row['Teaching Hours']

        # Initialize teacher workload if not already present
        if teacher not in teacher_workloads:
            teacher_workloads[teacher] = 0

        # Check if adding this module exceeds 12 hours
        if teacher_workloads[teacher] + teaching_hours > 12:
            # Find another teacher for the same module
            available_teacher = merged_data[(merged_data['Module Code'] == module) & 
                                            (merged_data['Teacher Name'] != teacher) & 
                                            (teacher_workloads.get(merged_data['Teacher Name'], 0) + teaching_hours <= 12)]

            if not available_teacher.empty:
                new_teacher = available_teacher.iloc[0]['Teacher Name']
                merged_data.at[index, 'Teacher Name'] = new_teacher
                teacher_workloads[new_teacher] = teacher_workloads.get(new_teacher, 0) + teaching_hours
            else:
                merged_data.at[index, 'Teacher Name'] = 'Unassigned (Manual Reassignment Needed)'
        else:
            teacher_workloads[teacher] += teaching_hours

    return merged_data

# Streamlit application
def main():
    st.title("Teacher Workload Calculator")

    # Provide template downloads
    st.subheader("Download Templates")
    student_template = generate_template("student")
    teacher_template = generate_template("teacher")

    student_csv = student_template.to_csv(index=False).encode('utf-8')
    teacher_csv = teacher_template.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="Download Student Database Template",
        data=student_csv,
        file_name='student_template.csv',
        mime='text/csv'
    )

    st.download_button(
        label="Download Teacher Module Template",
        data=teacher_csv,
        file_name='teacher_template.csv',
        mime='text/csv'
    )

    # Upload CSV files
    student_file = st.file_uploader("Upload Student Database CSV", type="csv")
    teacher_file = st.file_uploader("Upload Teacher Module CSV", type="csv")

    if student_file and teacher_file:
        # Read the CSV files
        student_data = pd.read_csv(student_file)
        teacher_data = pd.read_csv(teacher_file)

        # Merge the data for calculations
        merged_data = pd.merge(student_data, teacher_data, on='Module Code', how='inner')

        # Add calculated workload columns
        merged_data['Teaching Hours'], merged_data['Office Hours'], merged_data['Grading Hours'] = zip(
            *merged_data.apply(lambda x: calculate_workload(x, x['Student Number']), axis=1)
        )

        # Add total weekly workload per module
        merged_data['Total Weekly Hours'] = merged_data['Teaching Hours'] + merged_data['Office Hours'] + merged_data['Grading Hours']

        # Enforce 12-hour teaching limit and reassign excess
        merged_data = enforce_teaching_limit_and_reassign(merged_data)

        # Aggregate by Term and Teacher Name
        aggregated_data = merged_data.groupby(['Teacher Name', 'Term']).agg({
            'Teaching Hours': 'sum',
            'Office Hours': 'sum',
            'Grading Hours': 'sum',
            'Total Weekly Hours': 'sum'
        }).reset_index()

        # Create a final summary for each teacher across terms
        teacher_summary = aggregated_data.groupby('Teacher Name').agg({
            'Teaching Hours': 'sum',
            'Office Hours': 'sum',
            'Grading Hours': 'sum',
            'Total Weekly Hours': 'sum'
        }).reset_index()

        # Display data
        st.subheader("Merged and Calculated Data")
        st.dataframe(merged_data)

        st.subheader("Aggregated Workload Data by Term")
        st.dataframe(aggregated_data)

        st.subheader("Teacher Workload Summary")
        st.dataframe(teacher_summary)

        # Downloadable aggregated data
        csv = aggregated_data.to_csv(index=False).encode('utf-8')
        summary_csv = teacher_summary.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="Download Aggregated Data as CSV",
            data=csv,
            file_name='aggregated_workload.csv',
            mime='text/csv'
        )

        st.download_button(
            label="Download Teacher Summary as CSV",
            data=summary_csv,
            file_name='teacher_summary.csv',
            mime='text/csv'
        )

if __name__ == "__main__":
    main()
