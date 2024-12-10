import pandas as pd
import random
import streamlit as st

# Function to generate a CSV template for courses
def generate_course_template():
    return pd.DataFrame({
        'cohort': [''] * 5,
        'Course code': [''] * 5,
        'Courses': [''] * 5,
        'Main teacher': [''] * 5,
        'section': [1] * 5,
        'Sum of #students': [20, 35, 50, 80, 15],
        'section number': [1] * 5
    })

# Function to generate a CSV template for rooms
def generate_room_template():
    return pd.DataFrame({
        'Room Name': ['Room A', 'Room B', 'Room C', 'Room D', 'Room E'],
        'Population': [30, 40, 50, 60, 100]
    })

# Function to load the course and room data
def load_data(course_file, room_file):
    return pd.read_csv(course_file), pd.read_csv(room_file)

# Function to generate timetable and calculate stats
def generate_timetable(course_df, room_df, selected_days):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']

    timetable = {day: {time: [] for time in time_slots} for day in selected_days}
    teacher_stats = {}
    room_shortages = []
    unassignable_courses = []
    used_rooms = set()
    room_usage_hours = {room: 0 for room in rooms}  # Track room usage in hours

    total_course_hours = 0

    for _, row in course_df.iterrows():
        sections = row['section']
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']

        course_hours = sections * 4
        total_course_hours += course_hours

        teacher_stats[teacher] = teacher_stats.get(teacher, 0) + course_hours
        if teacher_stats[teacher] > 40:
            room_shortages.append({'Teacher': teacher, 'Required Hours': teacher_stats[teacher]})

        for section in range(sections):
            # Find rooms that can accommodate the students
            suitable_rooms = room_df[room_df['Population'] >= students]
            if suitable_rooms.empty:
                unassignable_courses.append({
                    'Course': course,
                    'Teacher': teacher,
                    'Students': students,
                    'Reason': 'No room can accommodate the number of students'
                })
                continue

            room = suitable_rooms.sample(1)['Room Name'].iloc[0]
            used_rooms.add(room)

            # Increment room usage hours (each slot = 2 hours)
            room_usage_hours[room] += 2

            time_slot = random.choice(time_slots)
            selected_day = random.choice(selected_days)
            timetable[selected_day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Section': f"Section {section+1}"})

    return timetable, teacher_stats, room_shortages, unassignable_courses, used_rooms, room_usage_hours

# Function to display the timetable and summary
def display_timetable(timetable, teacher_stats, room_shortages, unassignable_courses):
    timetable_data = []
    for day, slots in timetable.items():
        for time_slot, courses in slots.items():
            if not courses:
                timetable_data.append([day, time_slot, "No courses assigned"])
            else:
                for course in courses:
                    timetable_data.append([day, time_slot, course['Course'], course['Teacher'], course['Room'], course['Section']])
    timetable_df = pd.DataFrame(timetable_data, columns=['Day', 'Time Slot', 'Course', 'Teacher', 'Room', 'Section'])
    st.subheader("Generated Timetable")
    st.dataframe(timetable_df)

    teacher_stats_df = pd.DataFrame(list(teacher_stats.items()), columns=['Teacher', 'Total Weekly Hours'])
    st.subheader("Teacher Statistics")
    st.dataframe(teacher_stats_df)

    if room_shortages:
        st.subheader("Teacher Hour Shortages")
        st.dataframe(pd.DataFrame(room_shortages))

    if unassignable_courses:
        st.subheader("Unassignable Courses")
        st.dataframe(pd.DataFrame(unassignable_courses))

# Function to display unused rooms with their capacities
def display_unused_rooms_with_capacity(room_df, used_rooms):
    unused_rooms = room_df[~room_df['Room Name'].isin(used_rooms)]
    st.subheader("Rooms Not in Use")
    st.dataframe(unused_rooms)

# Function to display room usage statistics
def display_room_usage_statistics(room_usage_hours):
    st.subheader("Room Usage Statistics (Weekly)")
    room_usage_df = pd.DataFrame(list(room_usage_hours.items()), columns=['Room', 'Total Hours Used'])
    st.dataframe(room_usage_df)

# Streamlit app
def main():
    st.title("Timetable Generator")
    
    st.subheader("Download Templates")
    st.download_button("Download Course Template", generate_course_template().to_csv(index=False), "course_template.csv", "text/csv")
    st.download_button("Download Room Template", generate_room_template().to_csv(index=False), "room_template.csv", "text/csv")

    st.subheader("Upload Your Data")
    course_file = st.file_uploader("Upload Course Data (CSV)", type="csv")
    room_file = st.file_uploader("Upload Room Data (CSV)", type="csv")

    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select Days for Timetable", days_of_week, default=days_of_week)

    if course_file and room_file:
        course_df, room_df = load_data(course_file, room_file)
        timetable, teacher_stats, room_shortages, unassignable_courses, used_rooms, room_usage_hours = generate_timetable(course_df, room_df, selected_days)

        display_timetable(timetable, teacher_stats, room_shortages, unassignable_courses)
        display_unused_rooms_with_capacity(room_df, used_rooms)
        display_room_usage_statistics(room_usage_hours)

if __name__ == "__main__":
    main()
