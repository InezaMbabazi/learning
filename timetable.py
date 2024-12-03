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
