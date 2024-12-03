import pandas as pd
import streamlit as st

# Function to load the course and room data from uploaded CSV files
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to generate a course template (empty template for user)
def generate_course_template():
    # Generate empty dataframe with sample column names
    course_data = {
        'Course': [],
        'Teacher': [],
        'Room': [],
        'Section': []
    }
    return pd.DataFrame(course_data)

# Function to generate a room template (empty template for user)
def generate_room_template():
    # Generate empty dataframe with sample column names
    room_data = {
        'Room Name': [],
        'Capacity': []
    }
    return pd.DataFrame(room_data)

# Function to generate the timetable based on course and room data
def generate_timetable(course_df, room_df, selected_days):
    timetable = {day: {} for day in selected_days}
    teacher_stats = {}
    room_shortages = []
    hour_shortages = []
    unused_rooms = room_df.copy()
    
    # Assume the course_df has columns: Course, Teacher, Room, Section
    for _, row in course_df.iterrows():
        course = row['Course']
        teacher = row['Teacher']
        room = row['Room']
        section = row['Section']

        # Logic to allocate rooms and teachers to timetable
        for day in selected_days:
            # Check if room is available for the day (just an example logic)
            if room in unused_rooms['Room Name'].values:
                room_shortages.append({'Course': course, 'Room': room})
                unused_rooms = unused_rooms[unused_rooms['Room Name'] != room]
            
            # Logic to add teacher hours
            if teacher not in teacher_stats:
                teacher_stats[teacher] = 0
            teacher_stats[teacher] += 4  # Assume each class takes 4 hours

            if day not in timetable:
                timetable[day] = {}
            timetable[day][f"{course}-{section}"] = {'Course': course, 'Teacher': teacher, 'Room': room, 'Section': section}

    # Assuming the room shortage logic
    return timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms

# Function to display the timetable and other statistics
def display_timetable(timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, selected_days, room_df):
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
        st.dataframe(unused_rooms[['Room Name', 'Capacity']])

    # Calculate total room hours available
    total_room_hours = len(room_df) * 8 * len(selected_days)  # Total room hours for all rooms
    st.write(f"Total Room Hours Available: {total_room_hours}")

    # Calculate total hours required for courses
    total_course_hours = sum([4 for _ in timetable_data])  # Assuming each class takes 4 hours
    st.write(f"Total Course Hours Needed: {total_course_hours}")

    # Calculate room shortages if any
    if total_course_hours > total_room_hours:
        room_shortage_count = total_course_hours - total_room_hours
        st.write(f"Room Shortage: {room_shortage_count} hours")
    else:
        st.write("No room shortage detected.")

# Main function that brings everything together
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

    # Day Selection Checkboxes
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select Days for Timetable", days_of_week, default=days_of_week)

    if course_file and room_file:
        # Load the data
        course_df, room_df = load_data(course_file, room_file)

        # Generate the timetable
        timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms = generate_timetable(course_df, room_df, selected_days)

        if timetable is not None:
            st.write("Generated Timetable for Selected Days")
            display_timetable(timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms, selected_days, room_df)

if __name__ == "__main__":
    main()
