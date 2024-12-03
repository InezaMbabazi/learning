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
    teacher_stats = {}  # Track teacher hours
    room_shortages = []  # Track courses with room shortages
    hour_shortages = []  # Track teachers with insufficient hours
    used_rooms = set()  # Track used rooms

    # Calculate total required and available room hours
    total_required_hours = sum(row['section'] * 4 for _, row in course_df.iterrows())
    total_room_hours = len(room_df) * 8 * len(selected_days)
    room_hour_shortage = max(0, total_required_hours - total_room_hours)

    for idx, row in course_df.iterrows():
        sections = row['section']
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']
        teacher_weekly_hours = sections * 4

        if teacher not in teacher_stats:
            teacher_stats[teacher] = 0
        teacher_stats[teacher] += teacher_weekly_hours

        if teacher_stats[teacher] > 40:
            hour_shortages.append({'Teacher': teacher, 'Required Hours': teacher_stats[teacher]})

        for section in range(sections):
            available_rooms = room_df[room_df['Population'] >= students]['Room Name'].tolist()
            if not available_rooms:
                room_shortages.append({'Course': course, 'Teacher': teacher, 'Students': students})
                continue
            room = random.choice(available_rooms)
            used_rooms.add(room)
            time_slot = random.choice(time_slots)
            selected_day = random.choice(selected_days)

            timetable[selected_day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Section': f"Section {section+1}"})

    unused_rooms = room_df[~room_df['Room Name'].isin(used_rooms)]
    return timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, room_hour_shortage

# Function to display timetable and weekly summary
def display_timetable_and_summary(timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, room_hour_shortage, selected_days, total_courses, course_df, room_df):
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

    teacher_stats_df = pd.DataFrame(list(teacher_stats.items()), columns=['Teacher', 'Total Weekly Hours'])
    st.subheader("Teacher Weekly Statistics")
    st.dataframe(teacher_stats_df)

    if room_shortages:
        room_shortage_df = pd.DataFrame(room_shortages)
        st.subheader("Courses with Room Shortages")
        st.dataframe(room_shortage_df)

    if hour_shortages:
        hour_shortage_df = pd.DataFrame(hour_shortages)
        st.subheader("Teacher Hour Shortages")
        st.dataframe(hour_shortage_df)

    if not unused_rooms.empty:
        st.subheader("Rooms Without Classes Assigned")
        st.dataframe(unused_rooms[['Room Name', 'Population']])

    if room_hour_shortage > 0:
        st.subheader("Room Hour Shortage")
        st.write(f"Total Room Hours Shortage (Weekly): {room_hour_shortage} hours")

    # Weekly Summary
    unscheduled_courses = len(room_shortages)
    overloaded_teachers = [t['Teacher'] for t in hour_shortages]
    unused_rooms_count = len(unused_rooms)

    # Calculate total course hours and room hours weekly
    total_course_hours_weekly = sum(course_df['section'] * 4)  # Each section requires 4 hours per week
    total_room_hours_weekly = len(room_df) * 8 * len(selected_days)  # Each room is available 8 hours/day for selected days

    st.subheader("Weekly Summary")
    st.write(f"**Selected Days:** {', '.join(selected_days)}")
    st.write(f"**Total Weekly Courses Scheduled:** {total_courses - unscheduled_courses}")
    st.write(f"**Unscheduled Weekly Courses:** {unscheduled_courses}")
    st.write(f"**Teachers Overloaded Weekly:** {len(overloaded_teachers)}")
    st.write(f"**Unused Rooms Weekly:** {unused_rooms_count}")
    st.write(f"**Total Course Hours Weekly:** {total_course_hours_weekly} hours")
    st.write(f"**Total Room Hours Weekly:** {total_room_hours_weekly} hours")


# Streamlit app
def main():
    st.title("Course Timetable Generator")

    st.subheader("Download Templates")
    course_template = generate_course_template()
    room_template = generate_room_template()
    course_csv = course_template.to_csv(index=False)
    room_csv = room_template.to_csv(index=False)

    st.download_button("Download Course Template", course_csv, "course_template.csv", "text/csv")
    st.download_button("Download Room Template", room_csv, "room_template.csv", "text/csv")

    st.subheader("Upload Your Data")
    course_file = st.file_uploader("Upload Course Data (CSV)", type=["csv"])
    room_file = st.file_uploader("Upload Room Data (CSV)", type=["csv"])

    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select Days for Timetable", days_of_week, default=days_of_week)

    if course_file and room_file:
        course_df, room_df = load_data(course_file, room_file)
        timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, room_hour_shortage = generate_timetable(course_df, room_df, selected_days)
        total_courses = len(course_df)
        display_timetable_and_summary(timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, room_hour_shortage, selected_days, total_courses)

if __name__ == "__main__":
    main()
