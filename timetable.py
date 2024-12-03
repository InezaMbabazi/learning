import pandas as pd
import random
import streamlit as st

# Function to load course and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to generate timetable and calculate statistics
def generate_timetable(course_df, room_df, selected_days):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    
    timetable = []
    teacher_hours = {teacher: 0 for teacher in course_df['Main teacher'].unique()}
    room_usage = {room: 0 for room in rooms}
    unused_rooms = rooms.copy()

    # Generate the timetable
    for idx, row in course_df.iterrows():
        sections = row['section']
        for section in range(sections):
            teacher = row['Main teacher']
            course = row['Courses']
            students = row['Sum of #students']
            
            available_rooms = room_df[room_df['Population'] >= students]['Room Name'].tolist()
            if not available_rooms:
                st.error(f"No room available for course {course} with {students} students")
                return None
            room = random.choice(available_rooms)
            time_slot = random.choice(time_slots)

            # Check for room availability
            room_usage[room] += 1
            unused_rooms.remove(room) if room in unused_rooms else None

            # Check teacher hours
            teacher_hours[teacher] += 4  # Assuming each course section is 4 hours

            timetable.append([course, teacher, time_slot, room, f"Section {section+1}"])
    
    timetable_df = pd.DataFrame(timetable, columns=['Course', 'Teacher', 'Time Slot', 'Room', 'Section'])
    
    # Display statistics
    teacher_stats = pd.DataFrame(list(teacher_hours.items()), columns=['Teacher', 'Total Hours'])
    room_stats = pd.DataFrame(list(room_usage.items()), columns=['Room', 'Usage'])
    unused_room_list = pd.DataFrame(unused_rooms, columns=['Unused Rooms'])
    
    st.write("Generated Timetable:")
    st.dataframe(timetable_df)
    
    st.write("Teacher Hour Statistics:")
    st.dataframe(teacher_stats)
    
    st.write("Room Usage Statistics:")
    st.dataframe(room_stats)
    
    st.write("Unused Rooms:")
    st.dataframe(unused_room_list)

# Streamlit app
def main():
    st.title("Course Timetable Generator with Statistics")
    
    # File upload widgets
    course_file = st.file_uploader("Upload Course Data (CSV)", type=["csv"])
    room_file = st.file_uploader("Upload Room Data (CSV)", type=["csv"])

    # Day selection with checkboxes
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select Days for Courses", days)

    if course_file and room_file:
        # Load the data
        course_df, room_df = load_data(course_file, room_file)
        
        # Generate the timetable and display statistics
        generate_timetable(course_df, room_df, selected_days)

if __name__ == "__main__":
    main()
