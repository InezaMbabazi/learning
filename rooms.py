import pandas as pd
import streamlit as st
import io

# Helper function to create templates for Cohort and Room
def create_module_template():
    data = {"Cohort": [], "Total Students": [], "Module Code": [], "Module Name": [], "Credits": []}
    df = pd.DataFrame(data)
    return df

def create_room_template():
    data = {"Room Name": [], "Capacity": []}
    df = pd.DataFrame(data)
    return df

def download_template(df, filename):
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output

# Streamlit interface
st.title("Classroom Allocation System")

# Download templates
if st.button("Download Cohort Template"):
    st.download_button(
        label="Download Cohort Template",
        data=download_template(create_module_template(), "cohort_template.csv"),
        file_name="cohort_template.csv",
        mime="text/csv"
    )

if st.button("Download Room Template"):
    st.download_button(
        label="Download Room Template",
        data=download_template(create_room_template(), "room_template.csv"),
        file_name="room_template.csv",
        mime="text/csv"
    )

# Upload data
cohort_file = st.file_uploader("Upload Cohort Data", type=["csv"])
room_file = st.file_uploader("Upload Room Data", type=["csv"])

# Time Slots and Days
time_slots = [
    "08:00 AM - 10:00 AM", 
    "10:30 AM - 12:30 PM", 
    "03:00 PM - 05:00 PM", 
    "05:00 PM - 06:00 PM"
]
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

if cohort_file and room_file:
    cohort_df = pd.read_csv(cohort_file)
    room_df = pd.read_csv(room_file)
    
    # Display uploaded data
    st.write("### Cohort Data")
    st.dataframe(cohort_df)
    st.write("### Room Data")
    st.dataframe(room_df)
    
    # Track room usage per time slot
    room_usage = {room: {time: 0 for time in time_slots} for room in room_df["Room Name"]}
    
    # Function to assign rooms and time slots
    def allocate_rooms(cohort_df, room_df, time_slots, days):
        allocations = []
        for _, row in cohort_df.iterrows():
            cohort = row["Cohort"]
            students = row["Total Students"]
            module_code = row["Module Code"]
            module_name = row["Module Name"]
            credits = row["Credits"]
            
            # Determine the number of sessions per week (2 sessions per week for each module)
            sessions_per_week = 2
            hours_per_week = (credits // 3) * 2  # Each 3 credits = 2 hours per week
            total_space_needed = students * 1.5  # Assume each student requires 1.5 m²
            
            # Track assigned rooms and times
            assigned_rooms = []
            assigned_times = []
            assigned_days = []
            sections_assigned = 0
            
            for day in days:
                if sections_assigned < sessions_per_week:
                    # Try to assign the module to a room during this day
                    for time in time_slots:
                        # Check for available room
                        available_room = None
                        for _, room in room_df.iterrows():
                            if room_usage[room["Room Name"]][time] == 0:  # Room is not booked
                                available_room = room["Room Name"]
                                room_usage[room["Room Name"]][time] += 1  # Mark room as booked
                                break
                        
                        if available_room:
                            assigned_rooms.append(available_room)
                            assigned_times.append(time)
                            assigned_days.append(day)
                            sections_assigned += 1
                            break  # Proceed to next session
                        
            # Store allocation data
            for i in range(sections_assigned):
                allocations.append({
                    "Cohort": cohort,
                    "Module Code": module_code,
                    "Module Name": module_name,
                    "Room Name": assigned_rooms[i],
                    "Assigned Day": assigned_days[i],
                    "Assigned Time": assigned_times[i],
                })
        
        return pd.DataFrame(allocations)

    # Perform room allocation
    allocation_df = allocate_rooms(cohort_df, room_df, time_slots, days)
    
    # Display allocation report
    st.write("### Room Allocation Report")
    st.dataframe(allocation_df)
