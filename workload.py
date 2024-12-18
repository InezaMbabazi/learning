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

# Divide students into sections and assign to teachers
def assign_sections_and_calculate_workload(merged_data, max_students_per_section=30):
    section_data = []
    teacher_workloads = {}

    for index, row in merged_data.iterrows():
        module = row['Module Code']
        term = row['Term']
        total_students = row['Student Number']
        credits = row['Credits']
        
        teaching_hours, office_hours, grading_hours = calculate_workload(row, max_students_per_section)

        num_sections = -(-total_students // max_students_per_section)  # Ceiling division
        available_teachers = merged_data[(merged_data['Module Code'] == module)]['Teacher Name'].unique()

        for section in range(1, num_sections + 1):
            assigned_teacher = None
            for teacher in available_teachers:
                current_workload = teacher_workloads.get((teacher, term), 0)
                if current_workload + teaching_hours <= 12:
                    assigned_teacher = teacher
                    break

            if assigned_teacher:
                teacher_workloads[(assigned_teacher, term)] = teacher_workloads.get((assigned_teacher, term), 0) + teaching_hours
            else:
                assigned_teacher = 'Unassigned (Manual Reassignment Needed)'

            section_data.append({
                'Module Code': module,
                'Term': term,
                'Section': section,
                'Teacher Name': assigned_teacher,
                'Teaching Hours': teaching_hours,
                'Office Hours': office_hours,
                'Grading Hours': grading_hours,
                'Total Students': min(max_students_per_section, total_students),
            })

            total_students -= max_students_per_section

    return pd.DataFrame(section_data)

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

        # Assign sections and calculate workload
        section_data = assign_sections_and_calculate_workload(merged_data)

        # Aggregate by Term and Teacher Name
        aggregated_data = section_data.groupby(['Teacher Name', 'Term']).agg({
            'Teaching Hours': 'sum',
            'Office Hours': 'sum',
            'Grading Hours': 'sum'
        }).reset_index()
        aggregated_data['Total Weekly Hours'] = aggregated_data['Teaching Hours'] + aggregated_data['Office Hours'] + aggregated_data['Grading Hours']

        # Create a final summary for each teacher across terms
        teacher_summary = aggregated_data.groupby('Teacher Name').agg({
            'Teaching Hours': 'sum',
            'Office Hours': 'sum',
            'Grading Hours': 'sum',
            'Total Weekly Hours': 'sum'
        }).reset_index()

        # Display data
        st.subheader("Section and Workload Data")
        st.dataframe(section_data)

        st.subheader("Aggregated Workload Data by Term")
        st.dataframe(aggregated_data)

        st.subheader("Teacher Workload Summary")
        st.dataframe(teacher_summary)

        # Downloadable aggregated data
        section_csv = section_data.to_csv(index=False).encode('utf-8')
        aggregated_csv = aggregated_data.to_csv(index=False).encode('utf-8')
        summary_csv = teacher_summary.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="Download Section Data as CSV",
            data=section_csv,
            file_name='section_data.csv',
            mime='text/csv'
        )

        st.download_button(
            label="Download Aggregated Data as CSV",
            data=aggregated_csv,
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
