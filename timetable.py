import pandas as pd
import random
import streamlit as st
from io import StringIO

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
def generate_timetable(course_df, room_df):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    timetable = {day: {time: [] for time in time_slots} for day in days_of_week}
    teacher_stats = {}  # To track teacher hours
    room_shortages = []  # To track courses with room shortages
    used_rooms = set()  # To track rooms that are used

    for idx, row in course_df.iterrows():
        sections = row['section']  # The number of sections
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']
        
        # Calculate total weekly hours for the teacher (4 hours per section)
        teacher_weekly_hours = sections * 4

        # Track teacher stats (total weekly hours)
        if teacher not in teacher_stats:
            teacher_stats[teacher] = 0
        teacher_stats[teacher] += teacher_weekly_hours

        for section in range(sections):
            # Room assignment: Choose a room with enough capacity
            available_rooms = room_df[room_df['Population'] >= students]['Room Name'].tolist()
            if not available_rooms:
                room_shortages.append({'Course': course, 'Teacher': teacher, 'Students': students})
                continue
            room = random.choice(available_rooms)  # Randomly choose a room with enough capacity
            used_rooms.add(room)  # Mark this room as used

            # Time slot assignment (ensure no conflicts for the same teacher)
            day = random.choice(days_of_week)  # Randomly assign a day
            time_slot = random.choice(time_slots)

            timetable[day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Section': f"Section {section+1}"})
            
    # Find unused rooms
    unused_rooms = room_df[~room_df['Room Name'].isin(used_rooms)]

    return timetable, teacher_stats, room_shortages, unused_rooms

# Function to display timetable in a weekly format
def display_weekly_timetable(timetable, teacher_stats, room_shortages, unused_rooms):
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']

    # Display timetable as a dataframe
    timetable_data = []
    for day in days_of_week:
        for time_slot in time_slots:
            courses_at_time = timetable[day][time_slot]
            if not courses_at_time:
                timetable_data.append([day, time_slot, "No courses assigned"] * len(courses_at_time))
            else:
                for course in courses_at_time:
                    timetable_data.append([day, time_slot, course['Course'], course['Teacher'], course['Room'], course['Section']])

    timetable_df = pd.DataFrame(timetable_data, columns=['Day', 'Time Slot', 'Course', 'Teacher', 'Room', 'Section'])
    st.subheader("Weekly Timetable")
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

    # Display unused rooms with capacity
    if not unused_rooms.empty:
        st.subheader("Rooms Without Classes Assigned")
        st.dataframe(unused_rooms[['Room Name', 'Population']])

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
    
    if course_file and room_file:
        # Load the data
        course_df, room_df = load_data(course_file, room_file)
        
        # Generate the timetable
        timetable, teacher_stats, room_shortages, unused_rooms = generate_timetable(course_df, room_df)
        
        if timetable is not None:
            st.write("Generated Weekly Timetable:")
            display_weekly_timetable(timetable, teacher_stats, room_shortages, unused_rooms)

if __name__ == "__main__":
    main()
