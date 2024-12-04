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
        'Sum of #students': [20] * 5,
        'section number': [1] * 5
    })

# Function to generate a CSV template for rooms
def generate_room_template():
    return pd.DataFrame({
        'Room Name': ['Room A', 'Room B', 'Room C', 'Room D', 'Room E'],
        'Population': [30, 40, 50, 60, 70]
    })

# Function to load the course and room data
def load_data(course_file, room_file):
    return pd.read_csv(course_file), pd.read_csv(room_file)

# Function to generate timetable and calculate stats
def generate_timetable(course_df, room_df, selected_days):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']

    timetable = {day: {time: [] for time in time_slots} for day in selected_days}
    teacher_stats = {}  # Total hours per teacher
    room_shortages = []  # Courses without suitable rooms
    hour_shortages = []  # Teachers exceeding 40 hours/week
    used_rooms = set()  # Rooms used in the timetable
    total_course_hours = 0

    for _, row in course_df.iterrows():
        sections = row['section']
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']

        # Calculate total course hours (4 hours per section)
        course_hours = sections * 4
        total_course_hours += course_hours

        # Track teacher stats
        teacher_stats[teacher] = teacher_stats.get(teacher, 0) + course_hours
        if teacher_stats[teacher] > 40:
            hour_shortages.append({'Teacher': teacher, 'Required Hours': teacher_stats[teacher]})

        for section in range(sections):
            # Find available rooms for the course
            available_rooms = room_df[room_df['Population'] >= students]['Room Name'].tolist()
            if not available_rooms:
                room_shortages.append({'Course': course, 'Teacher': teacher, 'Students': students})
                continue
            room = random.choice(available_rooms)
            used_rooms.add(room)

            # Assign time slot and day
            time_slot = random.choice(time_slots)
            selected_day = random.choice(selected_days)
            timetable[selected_day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Section': f"Section {section+1}"})

    # Calculate room hours only for used rooms
    total_room_hours = len(used_rooms) * len(selected_days) * len(time_slots) * 2  # 2 hours per slot

    # Calculate room hour shortage
    room_hour_shortage = max(0, total_course_hours - total_room_hours)

    return timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage, used_rooms

# Function to display the timetable and summary
def display_timetable(timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage):
    # Display timetable
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

    # Display teacher stats
    teacher_stats_df = pd.DataFrame(list(teacher_stats.items()), columns=['Teacher', 'Total Weekly Hours'])
    st.subheader("Teacher Statistics")
    st.dataframe(teacher_stats_df)

    # Display room shortages
    if room_shortages:
        st.subheader("Room Shortages")
        st.dataframe(pd.DataFrame(room_shortages))

    # Display hour shortages
    if hour_shortages:
        st.subheader("Teacher Hour Shortages")
        st.dataframe(pd.DataFrame(hour_shortages))

    # Display weekly summary
    st.subheader("Weekly Summary")
    st.write(f"Total Course Hours (Weekly): {total_course_hours}")
    st.write(f"Total Room Hours Available (Weekly): {total_room_hours}")
    if room_hour_shortage > 0:
        st.write(f"Room Hour Shortage: {room_hour_shortage} hours")

# Function to display rooms not in use along with their capacities
def display_unused_rooms_with_capacity(room_df, used_rooms):
    unused_rooms = room_df[~room_df['Room Name'].isin(used_rooms)]
    if not unused_rooms.empty:
        st.subheader("Rooms Not in Use")
        st.dataframe(unused_rooms[['Room Name', 'Population']].rename(columns={'Population': 'Capacity'}))
    else:
        st.write("All rooms are in use.")

# Streamlit app
def main():
    st.title("Timetable Generator")
    
    # Downloadable templates
    st.subheader("Download Templates")
    st.download_button("Download Course Template", generate_course_template().to_csv(index=False), "course_template.csv", "text/csv")
    st.download_button("Download Room Template", generate_room_template().to_csv(index=False), "room_template.csv", "text/csv")

    # File upload
    st.subheader("Upload Your Data")
    course_file = st.file_uploader("Upload Course Data (CSV)", type="csv")
    room_file = st.file_uploader("Upload Room Data (CSV)", type="csv")

    # Day selection
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select Days for Timetable", days_of_week, default=days_of_week)

    if course_file and room_file:
        # Load data
        course_df, room_df = load_data(course_file, room_file)

        # Generate timetable and stats
        timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage, used_rooms = generate_timetable(course_df, room_df, selected_days)

        # Display timetable and summary
        display_timetable(timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage)

        # Display rooms not in use with their capacities
        display_unused_rooms_with_capacity(room_df, used_rooms)

if __name__ == "__main__":
    main()
