import pandas as pd
import streamlit as st

# Function to generate templates for students and teachers
def generate_template(template_type):
    if template_type == "student":
        return pd.DataFrame({
            'Student ID': [],
            'Module Code': [],
            'Term': [],
            'Student Number': [],
            'Credits': []
        })
    elif template_type == "teacher":
        return pd.DataFrame({
            'Module Code': [],
            'Teacher Name': [],
            'Assistant Name': [],
            'Teacher Status': [],  # e.g. 'Main' or 'Assistant'
            'Term': [],
            'Credits': []
        })

# Function to calculate teaching hours, office hours, and grading hours
def calculate_workload(row, max_students_per_section):
    total_students = row['Student Number']
    credits = row['Credits']
    
    # Teaching hours per term based on credits
    teaching_hours = credits * 2  # e.g. 2 hours per credit
    
    # Office and grading hours based on students and credits
    office_hours = total_students * 0.1  # 10% of total students
    grading_hours = total_students * 0.05  # 5% of total students
    
    return teaching_hours, office_hours, grading_hours

# Assign sections and calculate workload
def assign_sections_and_calculate_workload(merged_data, max_students_per_section=30):
    section_data = []
    teacher_workloads = {}
    assistant_workloads = {}

    for index, row in merged_data.iterrows():
        module = row['Module Code']
        term = row['Term']
        total_students = row['Student Number']
        credits = row['Credits']
        
        teaching_hours, office_hours, grading_hours = calculate_workload(row, max_students_per_section)

        num_sections = -(-total_students // max_students_per_section)  # Ceiling division
        available_teachers = merged_data[(merged_data['Module Code'] == module)]['Teacher Name'].unique()

        # Ensure 'Teacher Status' column exists
        if 'Teacher Status' not in merged_data.columns:
            raise KeyError("The 'Teacher Status' column is missing from the teacher data.")
        
        available_assistants = merged_data[(merged_data['Module Code'] == module)]['Teacher Status'].unique()

        for section in range(1, num_sections + 1):
            assigned_teacher = None
            assigned_assistant = None
            for teacher in available_teachers:
                current_workload = teacher_workloads.get((teacher, term), 0)
                if current_workload + teaching_hours <= 12:  # Assign teacher if they have available capacity
                    assigned_teacher = teacher
                    break

            # Assign assistant only if a teacher is assigned
            if assigned_teacher:
                available_assistants_for_section = available_assistants  # We can decide on assigning assistants if available
                assigned_assistant = available_assistants_for_section[0] if len(available_assistants_for_section) > 0 else None

            if assigned_teacher:
                teacher_workloads[(assigned_teacher, term)] = teacher_workloads.get((assigned_teacher, term), 0) + teaching_hours
            else:
                assigned_teacher = 'Unassigned (Manual Reassignment Needed)'

            # Track assistant workload (no teaching hours for assistant)
            if assigned_assistant:
                assistant_workloads[(assigned_assistant, term)] = assistant_workloads.get((assigned_assistant, term), 0) + office_hours + grading_hours

            section_data.append({
                'Module Code': module,
                'Term': term,
                'Section': section,
                'Teacher Name': assigned_teacher,
                'Assistant Name': assigned_assistant,  # Assign assistant if available
                'Teaching Hours': teaching_hours if assigned_teacher else 0,
                'Office Hours': office_hours,
                'Grading Hours': grading_hours,
                'Total Students': min(max_students_per_section, total_students),
                'Student Number': row['Student Number']  # Add Student Number to section data
            })

            total_students -= max_students_per_section

    return pd.DataFrame(section_data), teacher_workloads, assistant_workloads

# Aggregated Workload Data by Term
def create_aggregated_data_with_students(section_data):
    aggregated_data = section_data.groupby(['Teacher Name', 'Assistant Name', 'Term']).agg({
        'Teaching Hours': 'sum',
        'Office Hours': 'sum',
        'Grading Hours': 'sum',
        'Student Number': 'sum'  # Sum the Student Number for each teacher-assistant-term combination
    }).reset_index()
    aggregated_data['Total Weekly Hours'] = aggregated_data['Teaching Hours'] + aggregated_data['Office Hours'] + aggregated_data['Grading Hours']
    return aggregated_data

# Streamlit application main logic
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

        # Check if 'Teacher Status' exists
        if 'Teacher Status' not in merged_data.columns:
            st.error("The 'Teacher Status' column is missing from the uploaded teacher module file.")
            return

        # Assign sections and calculate workload
        section_data, teacher_workloads, assistant_workloads = assign_sections_and_calculate_workload(merged_data)

        # Create the aggregated data including Student Number
        aggregated_data = create_aggregated_data_with_students(section_data)

        # Create a final summary for each teacher across terms
        teacher_summary = aggregated_data.groupby('Teacher Name').agg({
            'Teaching Hours': 'sum',
            'Office Hours': 'sum',
            'Grading Hours': 'sum',
            'Student Number': 'sum',
            'Total Weekly Hours': 'sum'
        }).reset_index()

        # Create a summary for assistants
        assistant_summary = aggregated_data.groupby('Assistant Name').agg({
            'Office Hours': 'sum',
            'Grading Hours': 'sum',
            'Student Number': 'sum',
            'Total Weekly Hours': 'sum'
        }).reset_index()

        # Display data
        st.subheader("Section and Workload Data")
        st.dataframe(section_data)

        st.subheader("Aggregated Workload Data by Term (with Student Numbers)")
        st.dataframe(aggregated_data)

        st.subheader("Teacher Workload Summary")
        st.dataframe(teacher_summary)

        st.subheader("Assistant Workload Summary")
        st.dataframe(assistant_summary)

        # Downloadable aggregated data
        section_csv = section_data.to_csv(index=False).encode('utf-8')
        aggregated_csv = aggregated_data.to_csv(index=False).encode('utf-8')
        summary_csv = teacher_summary.to_csv(index=False).encode('utf-8')
        assistant_csv = assistant_summary.to_csv(index=False).encode('utf-8')

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

        st.download_button(
            label="Download Assistant Summary as CSV",
            data=assistant_csv,
            file_name='assistant_summary.csv',
            mime='text/csv'
        )

if __name__ == "__main__":
    main()
