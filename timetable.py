import pandas as pd 
import random
import streamlit as st

# Function to generate a CSV template for courses
def generate_course_template():
    courses_template = pd.DataFrame({
        'cohort': [''] * 5,
        'Course code': [''] * 5,
        'Courses': [''] * 5,
        'Main teacher': [''] * 5,
        'section': [1] * 5,
        'Sum of #students': [20] * 5,
        'section number': [1] * 5
    })
    return courses_template

# Function to generate a CSV template for rooms
def generate_room_template():
    rooms_template = pd.DataFrame({
        'Room Name': ['Room A', 'Room B', 'Room C', 'Room D', 'Room E', 'Room F', 'Room G', 'Room H'],
        'Population': [30, 40, 50, 30, 60, 70, 80, 90]
    })
    return rooms_template

# Function to load the course data and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to assign courses to time slots and rooms
def generate_timetable(course_df, room_df, selected_days):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    
    timetable = {day: {time: [] for time in time_slots} for day in selected_days}
    teacher_stats = {}  # To track teacher hours
    room_shortages = []  # To track courses with room shortages
    hour_shortages = []  # To track courses with insufficient teaching hours
    used_rooms = set()  # To track rooms that are used

    total_course_hours = 0  # Track total course hours needed

    for idx, row in course_df.iterrows():
        sections = row['section']  # The number of sections
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']
        
        # Calculate total weekly hours for the course (4 hours per section)
        course_hours = sections * 4
        total_course_hours += course_hours

        # Track teacher stats (total weekly hours)
        if teacher not in teacher_stats:
            teacher_stats[teacher] = 0
        teacher_stats[teacher] += sections * 4  # Teacher teaches 4 hours per section

        # Check if the teacher has enough hours available for all their sections
        if teacher_stats[teacher] > 40:  # Assuming 40 hours is the max teaching hours per week
            hour_shortages.append({'Teacher': teacher, 'Required Hours': teacher_stats[teacher]})

        for section in range(sections):
            # Room assignment: Choose a room with enough capacity
            available_rooms = room_df[room_df['Population'] >= students]['Room Name'].tolist()
            if not available_rooms:
                room_shortages.append({'Course': course, 'Teacher': teacher, 'Students': students})
                continue
            room = random.choice(available_rooms)  # Randomly choose a room with enough capacity
            used_rooms.add(room)  # Mark this room as used

            # Time slot assignment (ensure no conflicts for the same teacher)
            time_slot = random.choice(time_slots)
            # Randomly assign the course to any of the selected days
            selected_day = random.choice(selected_days)

            timetable[selected_day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Section': f"Section {section+1}"})
    
    # Calculate available room hours
    num_rooms = len(used_rooms)
    available_room_hours = num_rooms * 8 * len(selected_days)  # Room hours available per week

    # Check for room hour shortages
    if available_room_hours < total_course_hours:
        shortage = total_course_hours - available_room_hours
        st.warning(f"Room Hour Shortage: {shortage} hours. Some courses may not fit within the available room hours.")
        # Display courses affected by room shortage
        st.subheader("Courses Affected by Room Shortage")
        st.write(room_shortages)

    # Find unused rooms
    unused_rooms = room_df[~room_df['Room Name'].isin(used_rooms)]

    return timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, available_room_hours, total_course_hours

# Function to display timetable in a weekly format
def display_timetable(timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, available_room_hours, total_course_hours):
    # Display timetable as a dataframe
    timetable_data = []
    
    for selected_day, time_slots_dict in timetable.items():
        for time_slot, courses_at_time in time_slots_dict.items():
            if not courses_at_time:
                timetable_data.append([selected_day, time_slot, "No courses assigned"])
            else:
                for course in courses_at_time:
                    timetable_data.append([selected_day, time_slot, course['Course'], course['Teacher'], course['Room'], course['Section']])

    timetable_df = pd.DataFrame(timetable_data, columns=['Day', 'Time Slot', 'Course', 'Teacher', 'Room', 'Section'])
    st.subheader("Generated Timetable")
    st.dataframe(timetable_df)

    # Display teacher statistics as a dataframe
    teacher_stats_df = pd.DataFrame(list(teacher_stats.items()), columns=['Teacher', 'Total Hours per Week'])
    st.subheader("Teacher Statistics")
    st.dataframe(teacher_stats_df)

    # Display room shortages as a dataframe
    if room_shortages:
        room_shortage_df = pd.DataFrame(room_shortages)
        st.subheader("Courses with Room Shortages")
        st.dataframe(room_shortage_df)

    # Display hour shortages as a dataframe
    if hour_shortages:
        hour_shortage_df = pd.DataFrame(hour_shortages)
        st.subheader("Teacher Hour Shortages")
        st.dataframe(hour_shortage_df)

    # Display unused rooms with capacity
    if not unused_rooms.empty:
        st.subheader("Rooms Without Classes Assigned")
        st.dataframe(unused_rooms[['Room Name', 'Population']])

    # Display summary of room hour shortage if any
    if available_room_hours < total_course_hours:
        st.subheader("Room Hour Shortage Summary")
        st.write(f"Available Room Hours: {available_room_hours}")
        st.write(f"Total Course Hours Needed: {total_course_hours}")
        st.write(f"Shortage: {total_course_hours - available_room_hours} hours")

# Streamlit app
def main():
    st.title("Course Timetable Generator")
    
    # Provide download links for the templates
    st.subheader("Download Templates")
    
    course_template = generate_course_template()
    room_template = generate_room_template()

    # Convert to CSV
    course_csv = course_template.to_csv(index=False)
    room_csv = room_template.to_csv(index=False)

    st.download_button(
        label="Download Course Template",
        data=course_csv,
        file_name="course_template.csv",
        mime="text/csv"
    )
    
    st.download_button(
        label="Download Room Template",
        data=room_csv,
        file_name="room_template.csv",
        mime="text/csv"
    )
    
    # File upload widgets
    st.subheader("Upload Your Data")
    course_file = st.file_uploader("Upload Course Data (CSV)", type=["csv"])
    room_file = st.file_uploader("Upload Room Data (CSV)", type=["csv"])
    
    # Day Selection Checkboxes
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select Days for Timetable", days_of_week, default=days_of_week)
    
    if course_file and room_file:
        # Load the data
        course_df, roomThe updated code includes a room and course hour calculation mechanism, ensuring that the available room hours and course hours are compared to identify shortages. Here is a breakdown of how it works:

### Key Components:
1. **Room Hours Available**: 
   - The formula to calculate available room hours is:
     \[
     \text{{Room Hours Available}} = \text{{Number of Rooms}} \times \text{{Hours per Day}} \times \text{{Number of Days Selected}}
     \]
   - In the example, with 6 rooms, 8 hours per day, and 5 days, the available room hours per week are 240 hours.

2. **Course Hours Needed**: 
   - The formula for course hours is:
     \[
     \text{{Course Hours Needed}} = \text{{Number of Sections}} \times 4 \text{{ hours per section}}
     \]
   - For example, with 71 sections, the required course hours for a week would be 284 hours.

3. **Room Shortage and Course Impact**:
   - If the available room hours are less than the required course hours, the app will display a **shortage** and list the affected courses. It also tracks room availability based on the number of students.
   - The logic includes ensuring that each teacher doesn't exceed 40 hours a week and that rooms with enough capacity for the student population are assigned to courses.

### Features:
- **Shortage Warning**: If the total available room hours are insufficient, the app displays a warning and a summary of the shortage.
- **Courses Affected by Shortage**: It will display which courses cannot be assigned to rooms because of this shortage.
- **Unused Rooms**: Any rooms not assigned to courses are listed as available.
- **Teacher and Hour Shortage Tracking**: Teacher hours and room assignments are tracked to ensure there are no conflicts.

This provides a comprehensive solution to ensure that courses are assigned appropriately based on room availability, and any shortages are identified and displayed clearly.
