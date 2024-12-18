import pandas as pd
import streamlit as st
import math

def divide_students_into_sections(total_students, max_students_per_section):
    """Divides total students into sections of a maximum size."""
    sections = []
    num_sections = math.ceil(total_students / max_students_per_section)
    for i in range(1, num_sections + 1):
        start = (i - 1) * max_students_per_section + 1
        end = min(i * max_students_per_section, total_students)
        sections.append(f"{start}-{end}")
    return sections

def enforce_teaching_limit_and_reassign(merged_data, max_hours_per_week):
    """Ensures no teacher exceeds max_hours_per_week by reassigning sections."""
    teacher_workloads = {}
    reassigned_sections = []

    for index, row in merged_data.iterrows():
        teacher = row['Teacher Name']
        teaching_hours = row['Teaching Hours']

        if teacher not in teacher_workloads:
            teacher_workloads[teacher] = 0

        if teacher_workloads[teacher] + teaching_hours <= max_hours_per_week:
            teacher_workloads[teacher] += teaching_hours
        else:
            reassigned_sections.append(index)

    for index in reassigned_sections:
        row = merged_data.loc[index]
        available_teacher = next(
            (t for t, hours in teacher_workloads.items() if hours + row['Teaching Hours'] <= max_hours_per_week),
            None
        )
        if available_teacher:
            teacher_workloads[available_teacher] += row['Teaching Hours']
            merged_data.at[index, 'Teacher Name'] = available_teacher
        else:
            merged_data.at[index, 'Teacher Name'] = 'Unassigned'

    return merged_data

def calculate_workload_per_section(row):
    """Calculate workload for each row based on section details."""
    teaching_hours = row['Teaching Hours']
    office_hours = row['Office Hours']
    grading_hours = row['Grading Hours'] * row['Number of Students']
    total_hours = teaching_hours + office_hours + grading_hours
    return total_hours

def main():
    st.title("Teacher Workload Management")

    max_students_per_section = st.number_input("Max Students per Section", min_value=1, value=30, step=1)
    max_hours_per_week = st.number_input("Max Teaching Hours per Week", min_value=1, value=12, step=1)

    st.subheader("Upload Data")
    teacher_file = st.file_uploader("Upload Teacher Module Template", type=["csv"])
    student_file = st.file_uploader("Upload Student Database Template", type=["csv"])

    if teacher_file and student_file:
        teacher_data = pd.read_csv(teacher_file)
        student_data = pd.read_csv(student_file)

        teacher_data['Sections'] = teacher_data.apply(
            lambda row: divide_students_into_sections(row['Number of Students'], max_students_per_section), axis=1
        )

        exploded_data = teacher_data.explode('Sections').reset_index(drop=True)
        exploded_data['Teaching Hours'] = exploded_data['Credits'].apply(lambda x: 4 if x == 10 else (6 if x == 20 else 4))
        exploded_data['Office Hours'] = exploded_data['Credits'].apply(lambda x: 1 if x == 10 else 2)
        exploded_data['Grading Hours'] = exploded_data['Credits'].apply(lambda x: 0.083 if x == 10 else (0.117 if x == 20 else 0.083))

        exploded_data['Total Weekly Hours'] = exploded_data.apply(calculate_workload_per_section, axis=1)

        assigned_data = enforce_teaching_limit_and_reassign(exploded_data, max_hours_per_week)

        st.subheader("Aggregated Workload Data by Term")
        aggregated_data = assigned_data.groupby(
            ['Teacher Name', 'Term', 'Sections'], as_index=False
        ).agg({
            'Teaching Hours': 'sum',
            'Office Hours': 'sum',
            'Grading Hours': 'sum',
            'Total Weekly Hours': 'sum'
        })
        st.write(aggregated_data)

        st.download_button(
            label="Download Aggregated Data",
            data=aggregated_data.to_csv(index=False),
            file_name="aggregated_workload.csv",
            mime="text/csv"
        )

        st.subheader("Teacher Summary")
        teacher_summary = aggregated_data.groupby('Teacher Name', as_index=False).agg({
            'Total Weekly Hours': 'sum'
        })
        st.write(teacher_summary)

        st.download_button(
            label="Download Teacher Summary",
            data=teacher_summary.to_csv(index=False),
            file_name="teacher_summary.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
