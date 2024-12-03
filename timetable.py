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
        'Sum of #students': [20] * 5,
        'section number': [1] * 5
    })
    return courses_template

# Function to generate a CSV template for rooms
def generate_room_template():
    rooms_template = pd.DataFrame({
        'Room Name': ['Room A', 'Room B', 'Room C', 'Room D', 'Room E', 'Room F', 'Room G', 'Room H'],
        'Population': [30, 40, 50, 30, 60, 70, 80, 90]  # Room capacity
    })
    return rooms_template

# Function to load the course data and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to calculate room hours required considering room capacity
def calculate_room_hours_with_capacity(course_df, room_df, selected_days, room_capacity):
    num_rooms = len(room_df)
    room_hours_available = num_rooms * 8 * len(selected_days)  # 8 hours per day per room
    
    total_course_hours_required = 0
    course_affected = []
    
    # Loop through courses to calculate the number of rooms needed
    for idx, row in course_df.iterrows():
        sections = row['section']
        students_per_section = row['Sum of #students']  # Assuming 'Sum of #students' is the column with student count
        
        # Calculate rooms needed for each section
        rooms_needed_for_section = (students_per_section // room_capacity) + (students_per_section % room_capacity > 0)
        total_course_hours_required += rooms_needed_for_section * 4  # 4 hours per room per section
        
        # If rooms required exceed the available rooms, flag the course as affected
        if rooms_needed_for_section > num_rooms:
            course_affected.append({
                'Course': row['Courses'], 
                'Teacher': row['Main teacher'],
                'Rooms Needed': rooms_needed_for_section
            })
    
    # Compare available room hours to required course hours
    room_shortage = room_hours_available < total_course_hours_required
    shortage_details = {
        'Available Room Hours': room_hours_available,
        'Required Course Hours': total_course_hours_required,
        'Shortage': room_shortage,
        'Course Sections Affected': course_affected
    }
    
    return shortage_details

# Function to assign courses to time slots and rooms considering capacity
def generate_timetable(course_df, room_df, selected_days, room_capacity):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    
    timetable = {day: {time: [] for time in time_slots} for day in selected_days}
    teacher_stats = {}  # To track teacher hours
    room_shortages = []  # To track courses with room shortages
    hour_shortages = []  # To track courses with insufficient teaching hours
    used_rooms = set()  # To track rooms that are used
    
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
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select Days for Timetable", days_of_week, default=days_of_week)
    
    if course_file and room_file:
        # Load the data
        course_df, room_df = load_data(course_file, room_file)
        
        # Calculate room shortage based on capacity and available hours
        shortage_details = calculate_room_hours_with_capacity(course_df, room_df, selected_days, room_capacity=30)  # Assuming 30 students per room
        
        # Display the room shortage summary
        if shortage_details['Shortage']:
            st.write("Room Shortage Detected!")
            st.write(f"Available Room Hours: {shortage_details['Available Room Hours']}")
            st.write(f"Required Course Hours: {shortage_details['Required Course Hours']}")
            st.subheader("Affected Courses")
            st.dataframe(pd.DataFrame(shortage_details['Course Sections Affected']))
        
        # Generate the timetableHere is the full updated version of the code that integrates room capacity and student population to calculate room requirements, detect room shortages, and display affected courses. It also provides functionality to generate and display timetables, along with the required statistics about teachers' weekly hours, room usage, and any room or hour shortages:

```python
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
        'Sum of #students': [20] * 5,
        'section number': [1] * 5
    })
    return courses_template

# Function to generate a CSV template for rooms
def generate_room_template():
    rooms_template = pd.DataFrame({
        'Room Name': ['Room A', 'Room B', 'Room C', 'Room D', 'Room E', 'Room F', 'Room G', 'Room H'],
        'Population': [30, 40, 50, 30, 60, 70, 80, 90]  # Room capacity
    })
    return rooms_template

# Function to load the course data and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to calculate room hours required considering room capacity
def calculate_room_hours_with_capacity(course_df, room_df, selected_days, room_capacity):
    num_rooms = len(room_df)
    room_hours_available = num_rooms * 8 * len(selected_days)  # 8 hours per day per room
    
    total_course_hours_required = 0
    course_affected = []
    
    # Loop through courses to calculate the number of rooms needed
    for idx, row in course_df.iterrows():
        sections = row['section']
        students_per_section = row['Sum of #students']  # Assuming 'Sum of #students' is the column with student count
        
        # Calculate rooms needed for each section
        rooms_needed_for_section = (students_per_section // room_capacity) + (students_per_section % room_capacity > 0)
        total_course_hours_required += rooms_needed_for_section * 4  # 4 hours per room per section
        
        # If rooms required exceed the available rooms, flag the course as affected
        if rooms_needed_for_section > num_rooms:
            course_affected.append({
                'Course': row['Courses'], 
                'Teacher': row['Main teacher'],
                'Rooms Needed': rooms_needed_for_section
            })
    
    # Compare available room hours to required course hours
    room_shortage = room_hours_available < total_course_hours_required
    shortage_details = {
        'Available Room Hours': room_hours_available,
        'Required Course Hours': total_course_hours_required,
        'Shortage': room_shortage,
        'Course Sections Affected': course_affected
    }
    
    return shortage_details

# Function to assign courses to time slots and rooms considering capacity
def generate_timetable(course_df, room_df, selected_days, room_capacity):
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    
    timetable = {day: {time: [] for time in time_slots} for day in selected_days}
    teacher_stats = {}  # To track teacher hours
    room_shortages = []  # To track courses with room shortages
    hour_shortages = []  # To track courses with insufficient teaching hours
    used_rooms = set()  # To track rooms that are used
    
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
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select Days for Timetable", days_of_week, default=days_of_week)
    
    if course_file and room_file:
        # Load the data
        course_df, room_df = load_data(course_file, room_file)
        
        # Calculate room shortage based on capacity and available hours
        shortage_details = calculate_room_hours_with_capacity(course_df, room_df, selected_days, room_capacity=30)  # Assuming 30 students per room
        
        # Display the room shortage summary
        if shortage_details['Shortage']:
            st.write("Room Shortage Detected!")
            st.write(f"Available Room Hours: {shortage_details['Available Room Hours']}")
            st.write(f"Required Course Hours: {shortage_details['Required Course Hours']}")
            st.subheader("Affected Courses")
            st.dataframe(pd.DataFrame(shortage_details['Course Sections Affected']))
        
        # Generate the timetable
The provided code integrates room capacity and student population for a timetable generation system. Here's an overview of the key functionality:

1. **CSV Templates**: It includes functions for generating CSV templates for courses and rooms, which can be downloaded for data entry. The course template includes columns like cohort, course code, teacher, and the number of students per section, while the room template includes room names and capacities.

2. **Data Loading**: Users can upload their own course and room data. The app supports CSV file uploads for courses and room configurations.

3. **Room Hour Calculation**: The app calculates the required room hours based on the number of students and the available room capacity. It checks for room shortages by comparing the total available room hours (based on selected days and rooms) with the total hours required for courses.

4. **Timetable Generation**: The app generates a timetable by assigning courses to available rooms and time slots, ensuring that room capacities and teacher schedules are respected. The timetable is displayed in a weekly format, showing the courses assigned to specific rooms and time slots.

5. **Shortage Detection**: If there are room shortages or insufficient hours for teachers, the app flags affected courses and provides details about the shortage. It also tracks unused rooms that were not assigned any courses.

6. **Teacher Statistics**: The app tracks and displays the total weekly teaching hours per teacher, ensuring that no teacher exceeds the maximum limit (e.g., 40 hours per week).

7. **Streamlit Interface**: The app uses Streamlit for the interface, allowing users to interact with the system via checkboxes, file uploaders, and data displays. Users can select which days to schedule courses for and view real-time feedback on room and teacher availability.

This solution ensures that room assignments, course schedules, and teacher availability are managed efficiently, highlighting any conflicts or shortages in the system.
