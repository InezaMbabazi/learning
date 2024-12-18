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

# Function to calculate annual workload
def calculate_workload(student_data, teacher_data):
    teacher_workload = {}
    assignments = []

    # Initialize teacher workload
    for _, row in teacher_data.iterrows():
        teacher_workload[row['Teacher Name']] = 0

    # Assign teachers and calculate workload
    for _, row in student_data.iterrows():
        module_code = row['Module Code']
        total_hours = row['Weekly Hours'] * row['Sections'] * 15  # Annual hours (15 weeks assumed)
        module_teachers = teacher_data[teacher_data['Module Code'] == module_code]

        # Main teacher is required
        main_teachers = module_teachers[module_teachers['Teacher Status'] == 'Main']

        if not main_teachers.empty:
            main_teacher = main_teachers.iloc[0]['Teacher Name']
            teacher_workload[main_teacher] += total_hours
            assignments.append({
                'Teacher': main_teacher,
                'Module Code': module_code,
                'Module Name': row['Module Name'],
                'Sections': row['Sections'],
                'Total Annual Hours': total_hours,
                'Status': 'Main'
            })
        else:
            # If no main teacher is found
            assignments.append({
                'Teacher': 'Unassigned (No Main Teacher)',
                'Module Code': module_code,
                'Module Name': row['Module Name'],
                'Sections': row['Sections'],
                'Total Annual Hours': total_hours,
                'Status': 'Unassigned'
            })

        # Assign assistant teachers (if any)
        assistant_teachers = module_teachers[module_teachers['Teacher Status'] == 'Assistant']
        for _, assistant in assistant_teachers.iterrows():
            assistant_teacher = assistant['Teacher Name']
            teacher_workload[assistant_teacher] += total_hours * 0.5  # Assistants get 50% workload
            assignments.append({
                'Teacher': assistant_teacher,
                'Module Code': module_code,
                'Module Name': row['Module Name'],
                'Sections': row['Sections'],
                'Total Annual Hours': total_hours * 0.5,
                'Status': 'Assistant'
            })

    workload_summary = pd.DataFrame(teacher_workload.items(), columns=['Teacher', 'Total Annual Hours'])
    assignments_df = pd.DataFrame(assignments)
    return assignments_df, workload_summary

# Streamlit App
def main():
    st.title("Teacher Annual Workload Management System 📊")
    st.write("Upload student and teacher data to calculate annual workload.")

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

        st.subheader("Annual Workload Summary:")
        st.write(workload_summary)

        # Highlight unassigned modules
        unassigned_modules = assignments[assignments['Teacher'] == 'Unassigned (No Main Teacher)']
        if not unassigned_modules.empty:
            st.warning("Some modules could not be assigned due to missing main teachers:")
            st.write(unassigned_modules)

if __name__ == "__main__":
    main()
