import random
import pandas as pd
import streamlit as st

# Function to assign courses to time slots and rooms
def generate_timetable(course_df, room_df, selected_days):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    
    timetable = {day: {time: [] for time in time_slots} for day in selected_days}
    teacher_stats = {}  # To track teacher hours
    room_shortages = []  # To track courses with room shortages
    hour_shortages = []  # To track courses with insufficient teaching hours
    used_rooms = set()  # To track rooms that are used

    total_room_hours_needed = 0  # To track total room hours needed
    total_teacher_hours_needed = 0  # To track total teacher hours needed

    for idx, row in course_df.iterrows():
        sections = row['section']  # The number of sections
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']
        
        # Calculate total weekly hours for the teacher (4 hours per section)
        teacher_weekly_hours = sections * 4
        total_teacher_hours_needed += teacher_weekly_hours  # Update the total teacher hours needed

        # Track teacher stats (total weekly hours)
        if teacher not in teacher_stats:
            teacher_stats[teacher] = 0
        teacher_stats[teacher] += teacher_weekly_hours

        # Check if the teacher has enough hours available for all their sections
        if teacher_stats[teacher] > 40:  # Assuming 40 hours is the max teaching hours per week
            hour_shortages.append({'Course': course, 'Teacher': teacher, 'Required Hours': teacher_stats[teacher]})

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
            
            total_room_hours_needed += 4  # Add 4 room hours per section

    # Calculate shortages
    available_room_hours = 6 * 8 * 5  # 240 available room hours (assuming 5 days a week and 8 hours per day)
    room_shortage = total_room_hours_needed - available_room_hours
    teacher_hour_shortage = total_teacher_hours_needed - (len(course_df) * 40)  # Assuming each teacher can teach 40 hours max

    # Find unused rooms
    unused_rooms = room_df[~room_df['Room Name'].isin(used_rooms)]

    return timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, room_shortage, teacher_hour_shortage

# Function to display the shortage summary
def display_shortages(room_shortage, teacher_hour_shortage):
    st.subheader("Shortage Summary")
    
    if room_shortage > 0:
        st.write(f"**Room Hours Shortage**: {room_shortage} hours needed.")
    else:
        st.write("**No Room Hours Shortage**")
        
    if teacher_hour_shortage > 0:
        st.write(f"**Teacher Hour Shortage**: {teacher_hour_shortage} hours needed.")
    else:
        st.write("**No Teacher Hour Shortage**")

# Updated display function
def display_timetable(timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, room_shortage, teacher_hour_shortage):
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
    
    # Display shortage summary
    display_shortages(room_shortage, teacher_hour_shortage)

# Example usage:
# Assuming you have course_df and room_df dataframes
# selected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
# timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, room_shortage, teacher_hour_shortage = generate_timetable(course_df, room_df, selected_days)
# display_timetable(timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, room_shortage, teacher_hour_shortage)
