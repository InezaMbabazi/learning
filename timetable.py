import pandas as pd
import random
import streamlit as st

# Function to load the course and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    
    # Ensure 'Current Capacity' column exists, otherwise initialize it with 0
    if 'Current Capacity' not in room_df.columns:
        room_df['Current Capacity'] = 0
    
    return course_df, room_df

# Function to generate timetable and calculate stats considering room capacity
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
            # Find available rooms with enough capacity for the course
            available_rooms = room_df[(room_df['Population'] >= students) & 
                                      (room_df['Current Capacity'] + students <= room_df['Population'])]['Room Name'].tolist()]
            if not available_rooms:
                room_shortages.append({'Course': course, 'Teacher': teacher, 'Students': students})
                continue
            
            room = random.choice(available_rooms)
            used_rooms.add(room)

            # Update the room's current capacity
            room_df.loc[room_df['Room Name'] == room, 'Current Capacity'] += students

            # Assign time slot and day
            time_slot = random.choice(time_slots)
            selected_day = random.choice(selected_days)
            timetable[selected_day][time_slot].append({'Course': course, 'Teacher': teacher, 'Room': room, 'Section': f"Section {section+1}"})

    # Calculate room hours only for used rooms
    total_room_hours = len(used_rooms) * len(selected_days) * len(time_slots) * 2  # 2 hours per slot

    # Calculate room hour shortage
    room_hour_shortage = max(0, total_course_hours - total_room_hours)

    return timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage

# Main function to drive Streamlit app
def main():
    st.title("Timetable Generator")
    
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
        timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage = generate_timetable(course_df, room_df, selected_days)

        # Display timetable and summary
        display_timetable(timetable, teacher_stats, room_shortages, hour_shortages, total_course_hours, total_room_hours, room_hour_shortage)

if __name__ == "__main__":
    main()
