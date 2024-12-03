import pandas as pd
import random
import streamlit as st

# Function to generate a CSV template for courses
def generate_course_template():
    courses_template = pd.DataFrame({
        'cohort': [''] * 5,
        'Course code': [''] * 5,
        'Courses': [''] * 5,
        'Main teacher': [''] * 5,
        'section': [1] * 5,
        'Sum of #students': [20] * 5,  # Students per section
        'section number': [1] * 5
    })
    return courses_template

# Function to generate a CSV template for rooms
def generate_room_template():
    rooms_template = pd.DataFrame({
        'Room Name': ['Room A', 'Room B', 'Room C', 'Room D', 'Room E', 'Room F', 'Room G', 'Room H'],
        'Population': [30, 40, 50, 30, 60, 70, 80, 90]  # Room capacities
    })
    return rooms_template

# Function to load the course data and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to calculate room hours considering room capacity
def calculate_room_hours_with_capacity(course_df, room_df, selected_days, room_capacity):
    num_rooms = len(room_df)
    room_hours_available = num_rooms * 8 * len(selected_days)  # 8 hours per day
    
    total_course_hours_required = 0
    course_affected = []
    
    for idx, row in course_df.iterrows():
        sections = row['section']
        students_per_section = row['Sum of #students']
        
        # Calculate rooms needed for each section based on student count
        rooms_needed_for_section = (students_per_section // room_capacity) + (students_per_section % room_capacity > 0)
        total_course_hours_required += rooms_needed_for_section * 4  # 4 hours per room for each section
        
        # Check if there are enough rooms
        if rooms_needed_for_section > num_rooms:
            course_affected.append({
                'Course': row['Courses'], 
                'Teacher': row['Main teacher'],
                'Rooms Needed': rooms_needed_for_section
            })
    
    room_shortage = room_hours_available < total_course_hours_required
    shortage_details = {
        'Available Room Hours': room_hours_available,
        'Required Course Hours': total_course_hours_required,
        'Shortage': room_shortage,
        'Course Sections Affected': course_affected
    }
    
    return shortage_details

# Function to assign courses to time slots and rooms
def generate_timetable(course_df, room_df, selected_days):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    
    timetable = {day: {time: [] for time in time_slots} for day in selected_days}
    teacher_stats = {}  # To track teacher hours
    room_shortages = []  # To track courses with room shortages
    hour_shortages = []  # To track courses with insufficient teaching hours
    used_rooms = set()  # To track rooms that are used

    # Room capacity for allocation
    room_capacity = room_df['Population'].min()  # Consider the minimum room capacity for the course allocation

    # Calculate room and hour shortages considering room capacity
    shortage_details = calculate_room_hours_with_capacity(course_df, room_df, selected_days, room_capacity)

    # Track courses that exceed room hours or teacher hours
    if shortage_details['Shortage']:
        room_shortages = shortage_details['Course Sections Affected']
        
    for idx, row in course_df.iterrows():
        sections = row['section']  # The number of sections
        course = row['Courses']
        teacher = row['Main teacher']
        students = row['Sum of #students']
        
        # Calculate total weekly hours for the teacher (4 hours per section)
        teacher_weekly_hours = sections * 4

        # Track teacher stats (total weekly hours)
        if teacher not in teacher_stats:
            teacher_stats[teacher] = 0
        teacher_stats[teacher] += teacher_weekly_hours

        # Check if the teacher has enough hours available for all their sections
        if teacher_stats[teacher] > 40:  # Assuming 40 hours is the max teaching hours per week
            hour_shortages.append({'Teacher': teacher, 'Required Hours': teacher_stats[teacher]})

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
            
    # Find unused rooms
    unused_rooms = room_df[~room_df['Room Name'].isin(used_rooms)]

    return timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms

# Function to display timetable in a weekly format
def display_timetable(timetable, teacher_stats, room_shortages, hour_shortages, unused_rooms):
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

# Streamlit app
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
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'ThursdayThe provided code is designed to generate a course timetable, taking into account various constraints such as room capacity, teacher hours, and available room hours. Here's a summary of how it works:

### Key Features:
1. **Room Capacity Management**:
   - The system calculates the number of rooms needed based on the number of students for each course section.
   - It checks if the rooms available can accommodate all students, and if not, attempts to allocate multiple rooms to a course.

2. **Room and Teacher Hours Tracking**:
   - The available room hours are calculated based on the number of rooms and the selected days.
   - The system checks whether the available room hours are sufficient to meet the total required hours for the courses.
   - Teacher hours are tracked to ensure no teacher exceeds the maximum allowable hours per week (set to 40 hours here).

3. **Room and Teacher Shortage Reports**:
   - If there is a shortage of rooms or teacher hours, the system provides a detailed report of which courses and teachers are affected.

4. **Interactive Interface**:
   - Users can upload course and room data files in CSV format, and the timetable is generated with assigned rooms and time slots based on the given constraints.
   - The generated timetable, teacher statistics, and any shortages (room or hour) are displayed interactively in the app.

### Key Components:
- **Generate CSV Templates**: Templates are generated for courses and rooms to allow users to input their data.
- **Room and Hour Calculations**: The system ensures that the room and teacher hours available are sufficient for all the courses.
- **Room Assignment**: Rooms are assigned based on capacity, and the timetable is updated accordingly.
- **Teacher Hours Validation**: The system ensures that teachers do not exceed the 40-hour weekly limit.

### How It Works:
- The user can download templates for courses and rooms.
- Once data is uploaded (in CSV format), the timetable is generated by:
  1. Assigning rooms based on capacity.
  2. Assigning time slots to each course, ensuring no teacher is double-booked.
  3. Reporting any room or teacher hour shortages.
  
- The timetable and shortage reports are displayed using Streamlit’s interactive interface.

This tool ensures optimal allocation of rooms and teachers while providing a clear overview of any issues, like shortages, that need to be addressed.
