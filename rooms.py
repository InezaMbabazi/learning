import streamlit as st
import pandas as pd
import io
import math

# Function to generate the cohort template as an in-memory CSV
def create_cohort_template():
    data = {
        'Cohort Name': ['Computer Science', 'Business Admin', 'Data Science'],
        'Number of Students': [200, 120, 60],
        'Module Code': ['CS101', 'BUS202', 'DS301'],
        'Module Name': ['Introduction to Programming', 'Business Strategy', 'Data Science Basics'],
        'Credits': [10, 15, 20],
        'Term Offered': ['Spring 2025', 'Fall 2025', 'Spring 2025'],
        'Sessions Per Week': [2, 2, 2]  # Modules are taught twice a week
    }
    df = pd.DataFrame(data)
    
    # Save the DataFrame to a StringIO object
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue()

# Function to generate the room template as an in-memory CSV
def create_room_template():
    data = {
        'Room Name': ['Room 101', 'Room 102', 'Room 103'],
        'Capacity': [0, 0, 0],  # Will be calculated
        'Area (m²)': [100, 150, 200]  # Area in square meters
    }
    df = pd.DataFrame(data)
    
    # Save the DataFrame to a StringIO object
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue()

# Function to calculate total hours and rooms needed based on room area and number of students
def calculate_room_needs(number_of_students, credits, room_area, sessions_per_week):
    # Calculate total hours per student for the module
    if credits == 10:
        hours_per_week = 5
    elif credits == 15:
        hours_per_week = 6
    elif credits == 20:
        hours_per_week = 8
    else:
        hours_per_week = 0  # Invalid credits, no calculation
    
    total_hours = hours_per_week * 12  # 12 weeks in a trimester

    # Calculate the capacity of the room based on the square meters
    students_per_room = room_area // 1.5  # 1.5 m² per student

    # Calculate number of rooms needed per session
    rooms_needed_per_session = math.ceil(number_of_students / students_per_room)  # Ceiling division

    # Calculate total room usage per week
    total_room_usage = rooms_needed_per_session * sessions_per_week  # Twice per week

    return total_hours, rooms_needed_per_session, total_room_usage

# Streamlit app
st.title("Workload Calculation for Room Occupancy")
st.subheader("Step 1: Download the Templates")

# Provide download links for the templates
st.download_button(
    label="Download Cohort Template",
    data=create_cohort_template(),
    file_name="cohort_template.csv",
    mime="text/csv"
)

st.download_button(
    label="Download Room Template",
    data=create_room_template(),
    file_name="room_template.csv",
    mime="text/csv"
)

st.subheader("Step 2: Upload Your Data")

# File uploaders
uploaded_file_cohort = st.file_uploader("Upload Cohort Table (CSV)", type="csv", key="cohort")
uploaded_file_room = st.file_uploader("Upload Room Table (CSV)", type="csv", key="room")

if uploaded_file_cohort is not None and uploaded_file_room is not None:
    # Read the uploaded CSV files into DataFrames
    df_cohorts = pd.read_csv(uploaded_file_cohort)
    df_rooms = pd.read_csv(uploaded_file_room)

    # Display the uploaded datasets
    st.subheader("Cohorts Table:")
    st.write(df_cohorts)

    st.subheader("Rooms Table:")
    st.write(df_rooms)

    st.subheader("Workload Calculation Results:")

    # Loop through each row in the cohort table to calculate room needs for each module
    results = []
    for index, cohort_row in df_cohorts.iterrows():
        # Loop through each room to check how many are needed
        remaining_students = cohort_row['Number of Students']
        room_assignments = []
        
        for _, room_row in df_rooms.iterrows():
            # Calculate number of rooms needed for this cohort in this room
            total_hours, rooms_needed, total_room_usage = calculate_room_needs(
                remaining_students, 
                cohort_row['Credits'], 
                room_row['Area (m²)'], 
                cohort_row['Sessions Per Week']
            )
            
            # Check how many students will be assigned to this room
            if rooms_needed <= remaining_students // room_row['Capacity']:
                room_assignments.append(f"{rooms_needed} rooms in {room_row['Room Name']}")
                remaining_students -= rooms_needed * room_row['Capacity']
            else:
                # Assign the remaining students to this room
                room_assignments.append(f"{remaining_students} students in {room_row['Room Name']}")
                remaining_students = 0
                break

        shortage_flag = 'Yes' if remaining_students > 0 else 'No'
        results.append({
            'Cohort/Program': cohort_row['Cohort Name'],
            'Module Name': cohort_row['Module Name'],
            'Term Offered': cohort_row['Term Offered'],
            'Room Assignments': ', '.join(room_assignments),
            'Shortage': shortage_flag
        })
    
    # Create a DataFrame from the results and display it
    result_df = pd.DataFrame(results)
    st.write(result_df)

    # Optional: Create a bar chart to visualize the room occupancy
    st.bar_chart(result_df['Shortage'])

# Add instructions on the sidebar for the user
st.sidebar.header('Instructions')
st.sidebar.write("""
1. Download the **Cohort Template** and **Room Template**.
2. Fill in the required data in each template and save them as CSV files.
3. Upload the CSV files with your data.
4. The app will calculate the total hours required for each module and the number of rooms needed.
5. The app will also flag any room shortages based on the capacity.
""")
