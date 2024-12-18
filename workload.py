import streamlit as st
import pandas as pd

# Function to calculate weekly hours based on credits
def calculate_hours(credits):
    if credits == 10:
        return 5  # 4 teaching + 1 office hour
    elif credits == 15:
        return 6  # 4 teaching + 2 office hours
    elif credits == 20:
        return 10  # 6 teaching + 4 office hours
    return 0

# Function to calculate workload and assign teachers
def calculate_workload(student_data, teacher_data):
    teacher_workload = {}
    assignments = []

    # Initialize teacher workload
    for _, row in teacher_data.iterrows():
        teacher_workload[row['Teacher Name']] = {'Total Hours': 0, 'Term Hours': {}}

    # Assign teachers
    for _, row in student_data.iterrows():
        module_code = row['Module Code']
        weekly_hours = row['Weekly Hours']
        sections = row['Sections']
        term = row['Term']

        # Find teachers already assigned to this module
        module_teachers = teacher_data[teacher_data['Module Code'] == module_code]

        for sec in range(1, sections + 1):
            assigned = False

            # Prefer main teachers for the module
            for _, teacher_row in module_teachers.iterrows():
                teacher_name = teacher_row['Teacher Name']
                if teacher_workload[teacher_name]['Total Hours'] + weekly_hours <= 12:
                    teacher_workload[teacher_name]['Total Hours'] += weekly_hours
                    teacher_workload[teacher_name]['Term Hours'][term] = (
                        teacher_workload[teacher_name]['Term Hours'].get(term, 0) + weekly_hours
                    )
                    assignments.append({
                        'Teacher': teacher_name,
                        'Module Code': module_code,
                        'Module Name': row['Module Name'],
                        'Term': term,
                        'Section': sec,
                        'Weekly Hours': weekly_hours
                    })
                    assigned = True
                    break

            # If no assigned teacher is available, assign anyone with capacity
            if not assigned:
                for teacher_name in teacher_workload:
                    if teacher_workload[teacher_name]['Total Hours'] + weekly_hours <= 12:
                        teacher_workload[teacher_name]['Total Hours'] += weekly_hours
                        teacher_workload[teacher_name]['Term Hours'][term] = (
                            teacher_workload[teacher_name]['Term Hours'].get(term, 0) + weekly_hours
                        )
                        assignments.append({
                            'Teacher': teacher_name,
                            'Module Code': module_code,
                            'Module Name': row['Module Name'],
                            'Term': term,
                            'Section': sec,
                            'Weekly Hours': weekly_hours
                        })
                        assigned = True
                        break

            # If no teacher has capacity
            if not assigned:
                assignments.append({
                    'Teacher': 'Unassigned',
                    'Module Code': module_code,
                    'Module Name': row['Module Name'],
                    'Term': term,
                    'Section': sec,
                    'Weekly Hours': weekly_hours
                })

    # Create term-wise workload summary
    workload_summary = []
    for teacher, data in teacher_workload.items():
        for term, hours in data['Term Hours'].items():
            workload_summary.append({
                'Teacher': teacher,
                'Term': term,
                'Weekly Hours': hours
            })
    
    workload_summary_df = pd.DataFrame(workload_summary)
    assignments_df = pd.DataFrame(assignments)
    return assignments_df, workload_summary_df

# Streamlit App
def main():
    st.title("Teacher Workload Management System 📊")
    st.write("Upload student and teacher data to calculate workload by term.")

    # File uploaders
    student_file = st.file_uploader("Upload Student Module Data (CSV)", type=["csv"])
    teacher_file = st.file_uploader("Upload Teacher Data (CSV)", type=["csv"])

    if student_file and teacher_file:
        # Load data
        student_data = pd.read_csv(student_file)
        teacher_data = pd.read_csv(teacher_file)

        # Add weekly hours column to student data
        student_data['Weekly Hours'] = student_data['Credits'].apply(calculate_hours)

        st.subheader("Uploaded Student Module Data:")
        st.write(student_data)

        st.subheader("Uploaded Teacher Data:")
        st.write(teacher_data)

        # Calculate workload
        assignments, workload_summary = calculate_workload(student_data, teacher_data)

        st.subheader("Teacher Assignments:")
        st.write(assignments)

        st.subheader("Workload Summary Grouped by Term:")
        st.write(workload_summary)

        # Highlight unassigned sections
        unassigned_sections = assignments[assignments['Teacher'] == 'Unassigned']
        if not unassigned_sections.empty:
            st.warning("Some sections could not be assigned due to workload constraints:")
            st.write(unassigned_sections)

if __name__ == "__main__":
    main()
