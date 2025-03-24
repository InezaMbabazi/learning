import pandas as pd
import streamlit as st

# Function to assign rooms
def assign_rooms(cohorts, rooms):
    assignments = []  # List to store room assignment results
    
    # Iterate through each cohort and assign rooms
    for index, cohort in cohorts.iterrows():
        module_students = cohort['total_students']
        required_sq_meters = module_students * 1.5  # 1.5 square meters per student
        
        # Filter rooms based on capacity (you might need to adjust based on your column names)
        available_rooms = rooms[rooms['capacity'] >= required_sq_meters]
        
        # Assign room(s) based on availability
        if not available_rooms.empty:
            assigned_room = available_rooms.iloc[0]  # Assign the first available room
            assignments.append({
                'Cohort': cohort['cohort'],
                'Module': cohort['module_name'],
                'Room Assigned': assigned_room['room_name'],
                'Room Capacity (SQM)': assigned_room['capacity'],
                'Students': module_students,
            })
        else:
            assignments.append({
                'Cohort': cohort['cohort'],
                'Module': cohort['module_name'],
                'Room Assigned': 'No Room Available',
                'Room Capacity (SQM)': 'N/A',
                'Students': module_students,
            })
    
    # Convert to DataFrame
    assignments_df = pd.DataFrame(assignments)
    return assignments_df

# Sample cohorts DataFrame (replace this with your actual data)
cohorts = pd.DataFrame({
    'cohort': ['Cohort 1', 'Cohort 2'],
    'module_name': ['Module 1', 'Module 2'],
    'total_students': [40, 50],
})

# Sample rooms DataFrame (replace this with your actual data)
rooms = pd.DataFrame({
    'room_name': ['Room A', 'Room B', 'Room C'],
    'capacity': [100, 50, 30],  # Room capacity in square meters
})

# Generate the room assignments
assignments_df = assign_rooms(cohorts, rooms)

# Display the results in a table
st.write("Room Assignment Results")
st.dataframe(assignments_df)  # Displaying the results as a table

# Alternatively, you can use st.table() for a simpler static table
# st.table(assignments_df)
