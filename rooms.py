import streamlit as st
import pandas as pd
import io

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

    # Compute Sections, Hours, Square Meters, and Assign Time Slots
    def calculate_allocation(df, rooms):
        results = []
        weekly_schedule = []
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
            
            for _, room in sorted_rooms.iterrows():
                if total_space_needed <= 0:
                    break
                sections += 1
                assigned_rooms.append(room["Room Name"])
                allocated_students = min(students, room["Square Meters"] // 1.5)
                students_per_section.append(int(allocated_students))
                students -= allocated_students
                total_space_needed -= room["Square Meters"]
                
                # Assign time slots for each section (2 time slots per day)
                assigned_times.append(time_slots[sections % len(time_slots)])
            
            results.append({
                "Cohort": cohort,
                "Module Code": module_code,
                "Module Name": module_name,
                "Sections": sections,
                "Total Hours": total_hours,
                "Total Square Meters": students * 1.5,
                "Assigned Rooms": ", ".join(assigned_rooms),
                "Students per Section": ", ".join(map(str, students_per_section)),
                "Assigned Times": ", ".join(assigned_times)
            })
            
            # Weekly Schedule per Module
            weekly_schedule.append({
                "Cohort": cohort,
                "Module Code": module_code,
                "Module Name": module_name,
                "Room Assignments": ", ".join(assigned_rooms),
                "Assigned Times": ", ".join(assigned_times),
                "Week 1": ", ".join(map(str, students_per_section[:sections])),
                "Week 2": ", ".join(map(str, students_per_section[sections:2*sections])),
                "Week 3": ", ".join(map(str, students_per_section[2*sections:3*sections])),
                "Week 4": ", ".join(map(str, students_per_section[3*sections:4*sections])),
                # Repeat for remaining weeks
            })
        return pd.DataFrame(results), pd.DataFrame(weekly_schedule)
    
    allocation_df, schedule_df = calculate_allocation(cohort_df, room_df)
    
    # Display Module Allocation Report
    st.write("### Module Allocation Report")
    st.dataframe(allocation_df)
    
    # Display Weekly Room Assignment Report
    st.write("### Weekly Room Assignment Report")
    st.dataframe(schedule_df)
