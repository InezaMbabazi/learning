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

# Function to load the course and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to generate the timetable
def generate_timetable(course_df, room_df, selected_days):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    timetable = {day: {time: [] for time in time_slots} for day in selected_days}
    teacher_stats = {}  # Track teacher hours
    student_weekly_stats = []  # Track student statistics
    room_shortages = []  # Track courses with room shortages
    hour_shortages = []  # Track teacher hour issues

    for idx, row in course_df.iterrows():
        sections = row['section']
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']
        required_teacher_hours = sections * 4
        days_allocated = random.sample(selected_days, min(len(selected_days), sections))

        # Update teacher stats
        if teacher not in teacher_stats:
            teacher_stats[teacher] = 0
        teacher_stats[teacher] += required_teacher_hours
        if teacher_stats[teacher] > 40:
            hour_shortages.append({'Teacher': teacher, 'Assigned Hours': teacher_stats[teacher]})

        # Assign sections to days and time slots
        for day in days_allocated:
            available_rooms = room_df[room_df['Population'] >= students]['Room Name'].tolist()
            if not available_rooms:
                room_shortages.append({'Course': course, 'Students': students, 'Teacher': teacher})
                continue
            room = random.choice(available_rooms)
            time_slot = random.choice(time_slots)

            timetable[day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Students': students})
            student_weekly_stats.append({'Day': day, 'Course': course, 'Room': room, 'Students': students})

    return timetable, teacher_stats, room_shortages, hour_shortages, student_weekly_stats

# Function to display timetable and summary
def display_summary(timetable, teacher_stats, room_shortages, hour_shortages, student_weekly_stats, selected_days):
    # Timetable Data
    timetable_data = []
    for day, slots in timetable.items():
        for time_slot, courses in slots.items():
            for course in courses:
                timetable_data.append([day, time_slot, course['Course'], course['Teacher'], course['Room'], course['Students']])

    timetable_df = pd.DataFrame(timetable_data, columns=['Day', 'Time Slot', 'Course', 'Teacher', 'Room', 'Students'])
    st.subheader("Weekly Timetable")
    st.dataframe(timetable_df)

    # Teacher Stats
    teacher_stats_df = pd.DataFrame(list(teacher_stats.items()), columns=['Teacher', 'Total Hours per Week'])
    st.subheader("Teacher Weekly Statistics")
    st.dataframe(teacher_stats_df)

    # Room Shortages
    if room_shortages:
        room_shortage_df = pd.DataFrame(room_shortages)
        st.subheader("Room Shortages")
        st.dataframe(room_shortage_df)

    # Hour Shortages
    if hour_shortages:
        hour_shortage_df = pd.DataFrame(hour_shortages)
        st.subheader("Teacher Hour Overload")
        st.dataframe(hour_shortage_df)

    # Student Statistics
    student_stats_df = pd.DataFrame(student_weekly_stats)
    st.subheader("Student Statistics per Week")
    st.dataframe(student_stats_df)

    # Weekly Summary
    st.subheader("Weekly Summary")
    total_courses = len(set(course['Course'] for course in timetable_data))
    total_students = sum(stat['Students'] for stat in student_weekly_stats)
    overloaded_teachers = len(hour_shortages)
    room_issues = len(room_shortages)
    st.write(f"**Total Courses Scheduled:** {total_courses}")
    st.write(f"**Total Students Allocated:** {total_students}")
    st.write(f"**Teachers Overloaded:** {overloaded_teachers}")
    st.write(f"**Courses with Room Shortages:** {room_issues}")

# Streamlit App
def main():
    st.title("Weekly Timetable Generator")

    # Templates
    st.subheader("Download Templates")
    course_template = generate_course_template()
    room_template = generate_room_template()
    st.download_button("Download Course Template", course_template.to_csv(index=False), "course_template.csv", "text/csv")
    st.download_button("Download Room Template", room_template.to_csv(index=False), "room_template.csv", "text/csv")

    # Data Upload
    st.subheader("Upload Your Data")
    course_file = st.file_uploader("Upload Course Data (CSV)", type=["csv"])
    room_file = st.file_uploader("Upload Room Data (CSV)", type=["csv"])

    # Days Selection
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select Days for the Week", days_of_week, default=days_of_week)

    if course_file and room_file:
        course_df, room_df = load_data(course_file, room_file)
        timetable, teacher_stats, room_shortages, hour_shortages, student_weekly_stats = generate_timetable(course_df, room_df, selected_days)
        display_summary(timetable, teacher_stats, room_shortages, hour_shortages, student_weekly_stats, selected_days)

if __name__ == "__main__":
    main()
