import streamlit as st
import pandas as pd

# Function to calculate annual workload based on credits
def calculate_annual_hours(credits, sections):
    if credits == 10:
        return 5 * 12 * sections  # 5 hours per week * 12 weeks * sections
    elif credits == 15:
        return 6 * 12 * sections  # 6 hours per week * 12 weeks * sections
    elif credits == 20:
        return 10 * 12 * sections  # 10 hours per week * 12 weeks * sections
    return 0

# Function to calculate workload and assign teachers
def calculate_workload(student_data, teacher_data):
    teacher_workload = {}
    assignments = []

    # Initialize teacher workload
    for _, row in teacher_data.iterrows():
        teacher_workload[row['Teacher Name']] = 0

    # Assign teachers
    for _, row in student_data.iterrows():
        module_code = row['Module Code']
        annual_hours = calculate_annual_hours(row['Credits'], row['Sections'])

        # Find teachers assigned to this module
        module_teachers = teacher_data[teacher_data['Module Code'] == module_code]
        main_teachers = module_teachers[module_teachers['Teacher Status'] == 'Main']
        assistant_teachers = module_teachers[module_teachers['Teacher Status'] == 'Assistant']

        # Assign main teacher first
        assigned = False
        for _, teacher_row in main_teachers.iterrows():
            teacher_name = teacher_row['Teacher Name']
            if teacher_workload[teacher_name] + annual_hours <= 480:  # Annual cap of 480 hours
                teacher_workload[teacher_name] += annual_hours
                assignments.append({
                    'Teacher': teacher_name,
                    'Module Code': module_code,
                    'Module Name': row['Module Name'],
                    'Annual Hours': annual_hours,
                    'Section': row['Sections'],
                    'Status': 'Main'
                })
                assigned = True
                break

        # Assign assistant teacher if a main teacher is found
        if assigned:
            for _, teacher_row in assistant_teachers.iterrows():
                teacher_name = teacher_row['Teacher Name']
                if teacher_workload[teacher_name] + annual_hours <= 480:
                    teacher_workload[teacher_name] += annual_hours
                    assignments.append({
                        'Teacher': teacher_name,
                        'Module Code': module_code,
                        'Module Name': row['Module Name'],
                        'Annual Hours': annual_hours,
                        'Section': row['Sections'],
                        'Status': 'Assistant'
                    })
                    break

        # If no main teacher, flag as unassigned
        if not assigned:
            assignments.append({
                'Teacher': 'Unassigned',
                'Module Code': module_code,
                'Module Name': row['Module Name'],
                'Annual Hours': annual_hours,
                'Section': row['Sections'],
                'Status': 'Main'
            })

    workload_summary = pd.DataFrame(teacher_workload.items(), columns=['Teacher', 'Total Hours'])
    assignments_df = pd.DataFrame(assignments)
    return assignments_df, workload_summary

# Streamlit App
def main():
    st.title("Annual Teacher Workload Management System 📊")
    st.write("Upload student and teacher data to calculate annual workload.")

    # File uploaders
    student_file = st.file_uploader("Upload Student Module Data (CSV)", type=["csv"])
    teacher_file = st.file_uploader("Upload Teacher Data (CSV)", type=["csv"])

    if student_file and teacher_file:
        # Load data
        student_data = pd.read_csv(student_file)
        teacher_data = pd.read_csv(teacher_file)

        st.subheader("Uploaded Student Module Data:")
        st.write(student_data)

        st.subheader("Uploaded Teacher Data:")
        st.write(teacher_data)

        # Calculate workload
        assignments, workload_summary = calculate_workload(student_data, teacher_data)

        st.subheader("Teacher Assignments:")
        st.write(assignments)

        st.subheader("Workload Summary:")
        st.write(workload_summary)

        # Highlight unassigned sections
        unassigned_sections = assignments[assignments['Teacher'] == 'Unassigned']
        if not unassigned_sections.empty:
            st.warning("Some modules could not be assigned due to constraints:")
            st.write(unassigned_sections)

if __name__ == "__main__":
    main()
