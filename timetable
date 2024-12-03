import pandas as pd
import random
import streamlit as st

# Function to load the course data and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to assign courses to time slots and rooms
def generate_timetable(course_df, room_df):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    
    timetable = []
    for idx, row in course_df.iterrows():
        sections = row['section']  # The number of sections
        for section in range(sections):
            teacher = row['Main teacher']
            course = row['Courses']
            students = row['Sum of #students']
            
            # Room assignment: Choose a room with enough capacity
            available_rooms = room_df[room_df['Population'] >= students]['Room Name'].tolist()
            if not available_rooms:
                st.error(f"No room available for course {course} with {students} students")
                return None
            room = random.choice(available_rooms)  # Randomly choose a room with enough capacity

            # Time slot assignment (ensure no conflicts for the same teacher)
            time_slot = random.choice(time_slots)
            
            timetable.append([course, teacher, time_slot, room, f"Section {section+1}"])
    
    timetable_df = pd.DataFrame(timetable, columns=['Course', 'Teacher', 'Time Slot', 'Room', 'Section'])
    return timetable_df

# Streamlit app
def main():
    st.title("Course Timetable Generator")
    
    # File upload widgets
    course_file = st.file_uploader("Upload Course Data (CSV)", type=["csv"])
    room_file = st.file_uploader("Upload Room Data (CSV)", type=["csv"])
    
    if course_file and room_file:
        # Load the data
        course_df, room_df = load_data(course_file, room_file)
        
        # Generate the timetable
        timetable_df = generate_timetable(course_df, room_df)
        
        if timetable_df is not None:
            st.write("Generated Timetable:")
            st.dataframe(timetable_df)

if __name__ == "__main__":
    main()
