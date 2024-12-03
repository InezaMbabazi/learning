import pandas as pd 
import random
import streamlit as st

# Function to load the course data and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to calculate room and course hours and display shortage if any
def calculate_room_course_hours(course_df, room_df, selected_days):
    # Number of rooms and their total capacity
    num_rooms = len(room_df)
    room_hours_available = num_rooms * 8 * len(selected_days)  # 8 hours per day
    
    # Calculate required course hours (each section requires 4 hours)
    total_course_hours_required = course_df['section'].sum() * 4  # 4 hours per section
    
    # Calculate room hours vs course hours
    room_shortage = room_hours_available < total_course_hours_required
    shortage_details = {
        'Available Room Hours': room_hours_available,
        'Required Course Hours': total_course_hours_required,
        'Shortage': room_shortage,
        'Course Sections Affected': []
    }
    
    if room_shortage:
        for idx, row in course_df.iterrows():
            sections = row['section']
            course = row['Courses']
            teacher = row['Main teacher']
            required_hours_for_course = sections * 4
            
            if required_hours_for_course > room_hours_available:
                shortage_details['Course Sections Affected'].append({
                    'Course': course, 
                    'Teacher': teacher,
                    'Required Hours': required_hours_for_course
                })

    return shortage_details

# Function to display the room-course hour calculation and shortage summary
def display_shortage_summary(shortage_details):
    st.subheader("Room and Course Hour Comparison")
    
    st.write(f"**Available Room Hours**: {shortage_details['Available Room Hours']}")
    st.write(f"**Required Course Hours**: {shortage_details['Required Course Hours']}")
    
    if shortage_details['Shortage']:
        st.error("**There is a shortage of room hours for some courses!**")
        affected_courses_df = pd.DataFrame(shortage_details['Course Sections Affected'])
        st.dataframe(affected_courses_df)
    else:
        st.success("**There is no shortage of room hours. All courses can be scheduled!**")

# Streamlit app
def main():
    st.title("Course Timetable and Room Hours Calculator")
    
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
        
        # Calculate room and course hours and display any shortages
        shortage_details = calculate_room_course_hours(course_df, room_df, selected_days)
        display_shortage_summary(shortage_details)

if __name__ == "__main__":
    main()
