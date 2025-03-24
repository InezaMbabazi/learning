import streamlit as st
import pandas as pd
import math

# Function to calculate the rooms and sessions required for a cohort based on room capacity
def calculate_room_needs(number_of_students, credits, room_area, weeks=12):
    # Calculate capacity per room based on square meters (1.5 m² per student)
    students_per_room = room_area // 1.5
    
    # Calculate how many rooms (sections) are needed for the cohort
    sections_needed = math.ceil(number_of_students / students_per_room)
    
    # Calculate total room usage for one module (hours per week times number of weeks)
    if credits == 10:
        hours_per_week = 5  # 10 credits module = 5 hours per week
    elif credits == 15:
        hours_per_week = 5  # 15 credits module = 5 hours per week
    elif credits == 20:
        hours_per_week = 8  # 20 credits module = 8 hours per week
    
    # Calculate total hours for the module over the course of the term (weeks)
    total_hours_needed = hours_per_week * weeks
    
    return sections_needed, total_hours_needed, students_per_room

# Streamlit UI for user input
st.title('Module Room Allocation Report')

# User input for Cohorts (example: BsBA 2024)
cohort_name = st.text_input('Enter Cohort Name (e.g., BsBA 2024)', 'BsBA 2024')
num_students = st.number_input('Enter Number of Students', min_value=1, value=200)
module_code = st.text_input('Enter Module Code (e.g., BSA82102)', 'BSA82102')
module_name = st.text_input('Enter Module Name (e.g., Python for Business Analytics)', 'Python for Business Analytics')
credits = st.selectbox('Select Module Credits', options=[10, 15, 20], index=1)

# Define example rooms
rooms = pd.DataFrame({
    'Room Name': ['Room 101', 'Room 102', 'Room 103'],
    'Area (m²)': [150, 150, 150]  # Area in square meters for each room
})

# Report Generation: Loop through each room to calculate the number of rooms needed for the cohort
assigned_rooms = []  # List to track assigned room names for each module
module_results = {}

sections_needed, total_hours_needed, students_per_room = calculate_room_needs(
    num_students, credits, rooms.iloc[0]['Area (m²)']  # Use the first room for calculation
)

# Add room name to the assigned rooms list for the module
assigned_rooms.extend([rooms.iloc[0]['Room Name']] * sections_needed)

# Aggregate data per module and cohort (cohort name, module name)
cohort_module_key = (cohort_name, module_name)

if cohort_module_key not in module_results:
    module_results[cohort_module_key] = {
        'Total Sections Assigned': 0,
        'Total Square Meters Used': 0,
        'Total Hours Needed': 0,
        'Assigned Rooms': []  # List to store assigned rooms
    }

module_results[cohort_module_key]['Total Sections Assigned'] += sections_needed
module_results[cohort_module_key]['Total Square Meters Used'] += sections_needed * rooms.iloc[0]['Area (m²)']
module_results[cohort_module_key]['Total Hours Needed'] += total_hours_needed
module_results[cohort_module_key]['Assigned Rooms'] = list(set(assigned_rooms))  # Ensure unique room names

# Create a DataFrame from the results and display it
results_list = []
for (cohort_name, module_name), data in module_results.items():
    results_list.append({
        'Cohort Name': cohort_name,
        'Module Name': module_name,
        'Total Sections Assigned': data['Total Sections Assigned'],
        'Total Square Meters Used': data['Total Square Meters Used'],
        'Total Hours Needed (Term)': data['Total Hours Needed'],
        'Assigned Rooms': ', '.join(data['Assigned Rooms'])  # Concatenate room names into a single string
    })
    
result_df = pd.DataFrame(results_list)

# Display the final results
st.subheader('Room Allocation Report')
st.write(result_df)

