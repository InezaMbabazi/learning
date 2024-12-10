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
    cohort_timetable = {}  # New dictionary to track courses by cohort
    teacher_stats = {}
    room_shortages = []
    hour_shortages = []
    used_rooms = set()
    room_usage_hours = {room: {'sections': [], 'hours': 0} for room in rooms}  # Track sections and hours per room

    total_course_hours = 0

    for _, row in course_df.iterrows():
        sections = row['section']
        course = row['Courses']
        teacher = row['Main teacher']
        cohort = row['cohort']
        students = row['Sum of #students']

        course_hours = sections * 4
        total_course_hours += course_hours

        teacher_stats[teacher] = teacher_stats.get(teacher, 0) + course_hours
        if teacher_stats[teacher] > 40:
            hour_shortages.append({'Teacher': teacher, 'Required Hours': teacher_stats[teacher]})

        # Group courses by cohort
        if cohort not in cohort_timetable:
            cohort_timetable[cohort] = {day: {time: [] for time in time_slots} for day in selected_days}

        for section in range(sections):
            available_rooms = room_df[room_df['Population'] >= students]['Room Name'].tolist()
            if not available_rooms:
                room_shortages.append({'Course': course, 'Teacher': teacher, 'Students': students})
                continue
            room = random.choice(available_rooms)
            used_rooms.add(room)

            # Increment room usage hours (each slot = 2 hours)
            room_usage_hours[room]['sections'].append({'Course': course, 'Section': f"Section {section + 1}", 'Hours': 2})
            room_usage_hours[room]['hours'] += 2

            time_slot = random.choice(time_slots)
            selected_day = random.choice(selected_days)
            cohort_timetable[cohort][selected_day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Section': f"Section {section + 1}"})

    total_room_hours = len(used_rooms) * len(selected_days) * len(time_slots) * 2
    room_hour_shortage = max(0, total_course_hours - total_room_hours)

    return cohort_timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage, used_rooms, room_usage_hours

# Function to display the timetable and summary
def display_timetable(cos, cohort_timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage):
    # Show the timetable grouped by cohort
    for cohort, timetable in cohort_timetable.items():
        st.subheader(f"Timetable for Cohort: {cohort}")
        timetable_data = []
        for day, slots in timetable.items():
            for time_slot, courses in slots.items():
                if not courses:
                    timetable_data.append([day, time_slot, "No courses assigned"])
                else:
                    for course in courses:
                        timetable_data.append([day, time_slot, course['Course'], course['Teacher'], course['Room'], course['Section']])
        timetable_df = pd.DataFrame(timetable_data, columns=['Day', 'Time Slot', 'Course', 'Teacher', 'Room', 'Section'])
        st.dataframe(timetable_df)

    # Display teacher statistics
    teacher_stats_df = pd.DataFrame(list(teacher_stats.items()), columns=['Teacher', 'Total Weekly Hours'])
    st.subheader("Teacher Statistics")
    st.dataframe(teacher_stats_df)

    if room_shortages:
        st.subheader("Room Shortages")
        st.dataframe(pd.DataFrame(room_shortages))

    if hour_shortages:
        st.subheader("Teacher Hour Shortages")
        st.dataframe(pd.DataFrame(hour_shortages))

    st.subheader("Weekly Summary")
    st.write(f"Total Course Hours (Weekly): {total_course_hours}")
    st.write(f"Total Room Hours Available (Weekly): {total_room_hours}")
    if room_hour_shortage > 0:
        st.write(f"Room Hour Shortage: {room_hour_shortage} hours")

# Function to display unused rooms with their capacities
def display_unused_rooms_with_capacity(room_df, used_rooms):
    unused_rooms = room_df[~room_df['Room Name'].isin(used_rooms)]
    st.subheader("Rooms Not in Use")
    st.dataframe(unused_rooms)

def display_room_usage_statistics(room_usage_hours, timetable):
    st.subheader("Room Usage Statistics (Weekly)")
    room_usage_data = []
    
    # Iterate over each room and section data
    for room, data in room_usage_hours.items():
        for section in data['sections']:
            # Find the time slot for the section in the timetable
            course_name = section['Course']
            section_name = section['Section']
            hours_assigned = section['Hours']
            
            # Search for the time slot for the course and section in the timetable
            for day, slots in timetable.items():
                for time_slot, courses in slots.items():
                    for course in courses:
                        # Print the course structure for debugging
                        st.write(f"Debug: Course structure: {course}")
                        
                        if isinstance(course, dict) and 'Course' in course and 'Section' in course and 'Room' in course:
                            if course['Course'] == course_name and course['Section'] == section_name and course['Room'] == room:
                                room_usage_data.append([room, course_name, section_name, time_slot, hours_assigned])
                        else:
                            st.write(f"Error: Unexpected course format for {course}")
    
    # Create the DataFrame to display room usage with time slots
    room_usage_df = pd.DataFrame(room_usage_data, columns=['Room', 'Course', 'Section', 'Time Slot', 'Hours Assigned'])
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
        cohort_timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage, used_rooms, room_usage_hours = generate_timetable(course_df, room_df, selected_days)

        display_timetable(course_df, cohort_timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage)
        display_unused_rooms_with_capacity(room_df, used_rooms)
        display_room_usage_statistics(room_usage_hours, cohort_timetable)

if __name__ == "__main__":
    main()
