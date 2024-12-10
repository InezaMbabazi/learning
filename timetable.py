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
    # Sort rooms by capacity (ascending order) for optimal allocation
    room_df = room_df.sort_values(by='Population')
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    timetable = {day: {time: [] for time in time_slots} for day in selected_days}

    teacher_stats = {}
    room_shortages = []
    used_rooms = set()
    room_usage_hours = {room: 0 for room in room_df['Room Name']}  # Track room usage in hours
    unscheduled_hours = []

    for _, row in course_df.iterrows():
        sections = row['section']
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']
        course_hours = sections * 4  # Each section requires 4 hours weekly
        remaining_hours = course_hours

        for section in range(sections):
            for day in selected_days:
                for time_slot in time_slots:
                    # Filter rooms that can accommodate the number of students
                    suitable_rooms = room_df[room_df['Population'] >= students]
                    
                    if suitable_rooms.empty:
                        # No room available for this number of students
                        room_shortages.append({'Course': course, 'Teacher': teacher, 'Students': students})
                        continue

                    if remaining_hours <= 0:
                        break

                    # Select the smallest suitable room
                    room = suitable_rooms.iloc[0]['Room Name']
                    used_rooms.add(room)

                    # Assign course to time slot
                    timetable[day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Section': f"Section {section+1}"})
                    room_usage_hours[room] += 2
                    remaining_hours -= 2  # Deduct hours scheduled

        if remaining_hours > 0:
            unscheduled_hours.append({'Course': course, 'Teacher': teacher, 'Remaining Hours': remaining_hours})

    return timetable, teacher_stats, room_shortages, used_rooms, room_usage_hours, unscheduled_hours

# Function to display the timetable and summary
def display_timetable(timetable):
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

# Function to display room shortages
def display_room_shortages(room_shortages):
    if room_shortages:
        st.subheader("Room Shortages")
        st.dataframe(pd.DataFrame(room_shortages))

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

# Function to display unscheduled hours
def display_unscheduled_hours(unscheduled_hours):
    if unscheduled_hours:
        st.subheader("Unscheduled Hours")
        unscheduled_df = pd.DataFrame(unscheduled_hours)
        st.dataframe(unscheduled_df)

# Streamlit app
def main():
    st.title("Timetable Generator with Room Population Check")

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
        timetable, teacher_stats, room_shortages, used_rooms, room_usage_hours, unscheduled_hours = generate_timetable(course_df, room_df, selected_days)

        display_timetable(timetable)
        display_room_shortages(room_shortages)
        display_unused_rooms_with_capacity(room_df, used_rooms)
        display_room_usage_statistics(room_usage_hours)
        display_unscheduled_hours(unscheduled_hours)

if __name__ == "__main__":
    main()
