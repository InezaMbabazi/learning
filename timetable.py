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

# Function to calculate available teaching hours based on selected days
def calculate_available_hours(selected_days):
    time_slots_per_day = 4  # e.g., 4 time slots available per day
    available_hours = len(selected_days) * time_slots_per_day * 2  # 2 hours per time slot
    return available_hours

# Function to generate a timetable and check if it's feasible
def generate_timetable(course_df, room_df, selected_days):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    
    # Calculate available hours based on selected days
    available_hours = calculate_available_hours(selected_days)
    
    total_required_hours = 0  # To track total hours required for all sections
    used_rooms = set()  # To track rooms that are used

    # Calculate total required hours based on sections and teaching hours per section (4 hours)
    for idx, row in course_df.iterrows():
        sections = row['section']  # The number of sections
        total_required_hours += sections * 4  # 4 hours per section

    # Check if available hours are enough to cover the total required hours
    if total_required_hours > available_hours:
        shortage_hours = total_required_hours - available_hours
        st.warning(f"Not enough hours! You have a shortage of {shortage_hours} hours.")

    # Room assignments and timetable generation
    timetable = {day: {time: [] for time in time_slots} for day in selected_days}
    teacher_stats = {}  # To track teacher hours
    room_shortages = []  # To track courses with room shortages
    used_rooms = set()  # To track rooms that are used

    for idx, row in course_df.iterrows():
        sections = row['section']  # The number of sections
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']
        
        for section in range(sections):
            # Room assignment: Choose a room with enough capacity
            available_rooms = room_df[room_df['Population'] >= students]['Room Name'].tolist()
            if not available_rooms:
                room_shortages.append({'Course': course, 'Teacher': teacher, 'Students': students})
                continue
            room = random.choice(available_rooms)  # Randomly choose a room with enough capacity
            used_rooms.add(room)  # Mark this room as used

            # Time slot assignment
            time_slot = random.choice(time_slots)
            # Randomly assign the course to any of the selected days
            selected_day = random.choice(selected_days)

            timetable[selected_day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Section': f"Section {section+1}"})

    # Check for unused rooms
    unused_rooms = room_df[~room_df['Room Name'].isin(used_rooms)]
    
    return timetable, teacher_stats, room_shortages, unused_rooms, total_required_hours, available_hours

# Function to display timetable in a weekly format
def display_timetable(timetable, room_shortages, unused_rooms, total_required_hours, available_hours):
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

    # Display room shortages as a dataframe
    if room_shortages:
        room_shortage_df = pd.DataFrame(room_shortages)
        st.subheader("Courses with Room Shortages")
        st.dataframe(room_shortage_df)

    # Display unused rooms with capacity
    if not unused_rooms.empty:
        st.subheader("Rooms Without Classes Assigned")
        st.dataframe(unused_rooms[['Room Name', 'Population']])

    # Display summary of hour shortage and availability
    st.subheader("Timetable Summary")
    st.write(f"Total Required Teaching Hours: {total_required_hours} hours")
    st.write(f"Available Teaching Hours: {available_hours} hours")
    
    if total_required_hours > available_hours:
        shortage = total_required_hours - available_hours
        st.write(f"Shortage of {shortage} hours. Please adjust the days or sections.")

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
        course_df, room_df = load_data(course_file, room_file)
        
        # Generate the timetable
        timetable, teacher_stats, room_shortages, unused_rooms, total_required_hours, available_hours = generate_timetable(course_df, room_df, selected_days)
        
        if timetable is not None:
            st.write("Generated Timetable for Selected Days")
            display_timetable(timetable, room_shortages, unused_rooms, total_required_hours, available_hours)

if __name__ == "__main__":
    main()
