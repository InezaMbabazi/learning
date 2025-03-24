import streamlit as st
import pandas as pd
import io

# Constants
sq_m_per_student = 1.5

# Function to calculate required square meters
def calculate_required_space(students, credits):
    return students * sq_m_per_student

# Room assignment function
def assign_rooms(cohorts, rooms):
    assignments = []

    for idx, cohort in cohorts.iterrows():
        module_students = cohort['total_students']
        module_credits = cohort['credits']
        required_sq_meters = calculate_required_space(module_students, module_credits)
        module_name = cohort['module_name']
        
        # Find rooms with enough space
        available_rooms = rooms[rooms['capacity'] >= required_sq_meters]
        
        # Assign rooms
        assigned_rooms = []
        remaining_students = module_students
        for _, room in available_rooms.iterrows():
            room_capacity = room['capacity'] // sq_m_per_student  # Calculate number of students the room can handle
            if remaining_students <= room_capacity:
                assigned_rooms.append({'room_name': room['room_name'], 'students_assigned': remaining_students})
                remaining_students = 0
                break
            else:
                assigned_rooms.append({'room_name': room['room_name'], 'students_assigned': room_capacity})
                remaining_students -= room_capacity
        
        # If not all students are assigned, find another room
        if remaining_students > 0:
            # Handle assigning to additional rooms if necessary
            pass

        assignments.append(assigned_rooms)

    return assignments

# Streamlit app
st.title("Room Assignment for Modules")

# File uploader for room data
uploaded_room_file = st.file_uploader("Upload Room Data (CSV)", type=["csv"])
if uploaded_room_file is not None:
    rooms = pd.read_csv(uploaded_room_file)
    st.subheader("Room Data")
    st.write(rooms)

# File uploader for cohort data
uploaded_cohort_file = st.file_uploader("Upload Cohort Data (CSV)", type=["csv"])
if uploaded_cohort_file is not None:
    cohorts = pd.read_csv(uploaded_cohort_file)
    st.subheader("Cohort Data")
    st.write(cohorts)

    # Run room assignment if both files are uploaded
    if uploaded_room_file is not None and uploaded_cohort_file is not None:
        assignments = assign_rooms(cohorts, rooms)
        st.subheader("Room Assignment Results")
        st.write(assignments)

# Provide a downloadable template
def create_template():
    room_template = pd.DataFrame({
        'room_name': ['Room A', 'Room B', 'Room C'],
        'capacity': [50, 80, 60]
    })

    cohort_template = pd.DataFrame({
        'cohort': ['Cohort 1', 'Cohort 2'],
        'module_name': ['Module 1', 'Module 2'],
        'module_code': ['M101', 'M102'],
        'credits': [10, 20],
        'total_students': [40, 60]
    })

    return room_template, cohort_template

# Download template button
if st.button("Download Data Templates"):
    room_template, cohort_template = create_template()

    # Save templates to CSV
    room_template_path = "/mnt/data/room_template.csv"
    cohort_template_path = "/mnt/data/cohort_template.csv"
    
    room_template.to_csv(room_template_path, index=False)
    cohort_template.to_csv(cohort_template_path, index=False)

    # Provide download links
    st.markdown(f"[Download Room Template](sandbox:/mnt/data/room_template.csv)")
    st.markdown(f"[Download Cohort Template](sandbox:/mnt/data/cohort_template.csv)")

