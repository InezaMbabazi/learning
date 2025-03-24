import pandas as pd
import streamlit as st
import io

# Helper functions to create templates
def create_module_template():
    data = {"Cohort": [], "Total Students": [], "Module Code": [], "Module Name": [], "Credits": []}
    df = pd.DataFrame(data)
    return df

def create_room_template():
    data = {"Room Name": [], "Square Meters": []}
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

if cohort_file and room_file:
    cohort_df = pd.read_csv(cohort_file)
    room_df = pd.read_csv(room_file)
    
    # Display full tables
    st.write("### Cohort Data")
    st.dataframe(cohort_df)
    st.write("### Room Data")
    st.dataframe(room_df)
    
    # Time Slots (assuming 2 time slots per day: Morning and Afternoon)
    time_slots = ["08:00 AM - 10:00 AM", "10:30 AM - 12:30 PM", "01:30 PM - 03:30 PM", "04:00 PM - 06:00 PM"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]  # Use all weekdays

    # Track room-time assignments to avoid conflicts
    room_time_assignments = {f"{room['Room Name']}": {time: 0 for time in time_slots} for _, room in room_df.iterrows()}

    # Compute Sections, Hours, Square Meters, and Assign Time Slots with Days
    def calculate_allocation(df, rooms):
        results = []
        weekly_schedule = []
        shortage_report = []
        
        for _, row in df.iterrows():
            cohort = row["Cohort"]
            students = row["Total Students"]
            module_code = row["Module Code"]
            module_name = row["Module Name"]
            credits = row["Credits"]
            
            # Calculate hours per week
            hours_per_week = (credits // 3) * 2  # Each 3 credits = 2 hours per week
            total_hours = hours_per_week * 12
            
            # Calculate sections based on room sizes
            total_space_needed = students * 1.5
            sorted_rooms = rooms.sort_values(by="Square Meters", ascending=False)
            sections = 0
            assigned_rooms = []
            students_per_section = []
            assigned_times = []
            assigned_days = []  # Track the days for each section
            room_time_assignments_for_module = []  # Track the room-time assignments for this module
            
            # Track room usage per time slot to avoid double booking
            room_usage_count = {f"{room['Room Name']}": {time: 0 for time in time_slots} for _, room in rooms.iterrows()}
            
            # Limit the room assignment to 2 sections per module
            time_slot_index = 0  # To switch between time slots for 2 sessions per week
            day_index = 0  # To switch between days (Monday, Tuesday, etc.)
            
            for _, room in sorted_rooms.iterrows():
                if total_space_needed <= 0 or sections >= 2:  # Only allocate 2 sections per week
                    break
                # If room has space and is available for this time slot, assign it
                if room_usage_count[room["Room Name"]][time_slots[time_slot_index]] < 1:  # No more than 1 use per room in same time
                    sections += 1
                    assigned_rooms.append(room["Room Name"])
                    allocated_students = min(students, room["Square Meters"] // 1.5)
                    students_per_section.append(int(allocated_students))
                    students -= allocated_students
                    total_space_needed -= room["Square Meters"]
                    
                    # Assign time slots and days for each section
                    assigned_time = time_slots[time_slot_index % len(time_slots)]
                    assigned_day = days[day_index % len(days)]
                    
                    # Track room-time usage
                    room_usage_count[room["Room Name"]][assigned_time] += 1
                    room_time_assignments_for_module.append(f"{room['Room Name']} at {assigned_day} {assigned_time}")
                    
                    assigned_times.append(assigned_time)
                    assigned_days.append(assigned_day)
                else:
                    # If the room is already booked at this time, try the next available time slot
                    continue
                
                time_slot_index += 1  # Switch to next time slot for the next section
                day_index += 1  # Switch to next day for the next section
            
            # Now assign each room and time slot separately
            for i in range(sections):
                results.append({
                    "Cohort": cohort,
                    "Module Code": module_code,
                    "Module Name": module_name,
                    "Room Name": assigned_rooms[i],
                    "Assigned Time": assigned_times[i],
                    "Assigned Day": assigned_days[i],
                    "Students per Section": students_per_section[i]
                })
            
            # Weekly Schedule per Module (not going into weekly breakdown for simplicity)
            weekly_schedule.append({
                "Cohort": cohort,
                "Module Code": module_code,
                "Module Name": module_name,
                "Room Assignments and Times": ", ".join(room_time_assignments_for_module),
                "Assigned Days": ", ".join(assigned_days),
                "Week 1": ", ".join(map(str, students_per_section[:sections])),
                "Week 2": ", ".join(map(str, students_per_section[sections:])),
                # Repeat for remaining weeks if needed
            })
            
            # Track shortages if the available rooms couldn't accommodate all students
            if total_space_needed > 0:
                shortage_report.append({
                    "Cohort": cohort,
                    "Module Code": module_code,
                    "Module Name": module_name,
                    "Shortage (Students)": total_space_needed // 1.5  # Remaining students who couldn't be assigned rooms
                })
        
        return pd.DataFrame(results), pd.DataFrame(weekly_schedule), pd.DataFrame(shortage_report)
    
    allocation_df, schedule_df, shortage_df = calculate_allocation(cohort_df, room_df)
    
    # Display Module Allocation Report
    st.write("### Module Allocation Report")
    st.dataframe(allocation_df)
    
    # Display Weekly Room Assignment Report with Room Details
    st.write("### Weekly Room Assignment Report")
    room_assignments_split_expanded = schedule_df.explode("Room Assignments and Times")
    st.dataframe(room_assignments_split_expanded)
    
    # Display Shortage Report
    st.write("### Room Shortage Report")
    if len(shortage_df) > 0:
        st.dataframe(shortage_df)
    else:
        st.write("No shortage detected!")
