import pandas as pd
import streamlit as st
import math

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

    max_hours_per_week = st.number_input("Max Teaching Hours per Week", min_value=1, value=12, step=1)

    st.subheader("Upload Data")
    teacher_file = st.file_uploader("Upload Teacher Module Template", type=["csv"])
    student_file = st.file_uploader("Upload Student Database Template", type=["csv"])

    if teacher_file and student_file:
        teacher_data = pd.read_csv(teacher_file)
        student_data = pd.read_csv(student_file)

        # Merge teacher and student data
        merged_data = pd.merge(teacher_data, student_data, on=['Course Code', 'Term'], how='inner')

        # Assign teaching, office, and grading hours based on credits
        merged_data['Teaching Hours'] = merged_data['Credits'].apply(lambda x: 4 if x == 10 else (6 if x == 20 else 4))
        merged_data['Office Hours'] = merged_data['Credits'].apply(lambda x: 1 if x == 10 else 2)
        merged_data['Grading Hours'] = merged_data['Credits'].apply(lambda x: 0.083 if x == 10 else (0.117 if x == 20 else 0.083))

        # Calculate total weekly hours
        merged_data['Total Weekly Hours'] = merged_data.apply(calculate_workload_per_section, axis=1)

        # Enforce teaching limit and reassign sections if needed
        assigned_data = enforce_teaching_limit_and_reassign(merged_data, max_hours_per_week)

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
