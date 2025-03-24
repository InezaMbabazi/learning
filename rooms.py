import streamlit as st
import pandas as pd
import io
import math

# Function to generate the cohort template as an in-memory CSV
def create_cohort_template():
    data = {
        'Cohort Name': ['Computer Science', 'Business Admin', 'Data Science'],
        'Number of Students': [200, 150, 100],
        'Module Code': ['CS101', 'BUS202', 'DS301'],
        'Module Name': ['Introduction to Programming', 'Business Strategy', 'Data Science Basics'],
        'Credits': [10, 15, 20],
        'Term Offered': ['Spring 2025', 'Fall 2025', 'Spring 2025'],
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
        'Area (m²)': [100, 150, 200]  # Area in square meters
    }
    df = pd.DataFrame(data)
    
    # Save the DataFrame to a StringIO object
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue()

# Function to calculate the rooms and sessions required for a cohort based on room capacity
def calculate_room_needs(number_of_students, credits, room_area):
    # Calculate capacity per room based on square meters (1.5 m² per student)
    students_per_room = room_area // 1.5
    
    # Calculate how many rooms are needed for the cohort
    rooms_needed = math.ceil(number_of_students / students_per_room)
    
    # Calculate total room usage per week (assuming modules are taught twice a week)
    if credits == 10:
        hours_per_week = 5  # 10 credits module = 5 hours per week
    elif credits == 15:
        hours_per_week = 6  # 15 credits module = 6 hours per week
    elif credits == 20:
        hours_per_week = 8  # 20 credits module = 8 hours per week
    
    # Each module has 2 sessions per week
    total_sessions_needed = 2
    total_hours_needed = hours_per_week * total_sessions_needed
    
    return rooms_needed, total_sessions_needed, total_hours_needed, students_per_room

# Streamlit app
st.title("Module Room Allocation Report")
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

    st.subheader("Module Allocation Report:")

    # Loop through each row in the cohort table to calculate room needs for each module
    module_results = {}
    
    for index, cohort_row in df_cohorts.iterrows():
        # Loop through each room to calculate the number of rooms needed
        for _, room_row in df_rooms.iterrows():
            rooms_needed, total_sessions_needed, total_hours_needed, students_per_room = calculate_room_needs(
                cohort_row['Number of Students'], 
                cohort_row['Credits'], 
                room_row['Area (m²)']
            )
            
            # Aggregate data per module (module name)
            if cohort_row['Module Name'] not in module_results:
                module_results[cohort_row['Module Name']] = {
                    'Total Sections Assigned': 0,
                    'Total Square Meters Used': 0,
                    'Total Hours Needed': 0
                }
            
            module_results[cohort_row['Module Name']]['Total Sections Assigned'] += rooms_needed
            module_results[cohort_row['Module Name']]['Total Square Meters Used'] += rooms_needed * room_row['Area (m²)']
            module_results[cohort_row['Module Name']]['Total Hours Needed'] += total_hours_needed

    # Create a DataFrame from the results and display it
    results_list = []
    for module_name, data in module_results.items():
        results_list.append({
            'Module Name': module_name,
            'Total Sections Assigned': data['Total Sections Assigned'],
            'Total Square Meters Used': data['Total Square Meters Used'],
            'Total Hours Needed': data['Total Hours Needed']
        })
    
    result_df = pd.DataFrame(results_list)
    st.write(result_df)

    # Optional: Create a bar chart to visualize the total sections assigned
    st.bar_chart(result_df['Total Sections Assigned'])

# Add instructions on the sidebar for the user
st.sidebar.header('Instructions')
st.sidebar.write("""
1. Download the **Cohort Template** and **Room Template**.
2. Fill in the required data in each template and save them as CSV files.
3. Upload the CSV files with your data.
4. The app will calculate the total sections assigned, square meters used, and total hours needed for each module.
""")
