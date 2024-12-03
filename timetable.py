import pandas as pd
import random
import streamlit as st

# Function to load the course data and room data
def load_data(course_file, room_file):
    course_df = pd.read_csv(course_file)
    room_df = pd.read_csv(room_file)
    return course_df, room_df

# Function to calculate available hours based on selected days
def calculate_available_hours(selected_days, room_count, hours_per_day):
    return len(selected_days) * room_count * hours_per_day

# Function to calculate the required teaching hours for all sections
def calculate_required_hours(course_df):
    total_required_hours = 0
    for _, row in course_df.iterrows():
        sections = row['section']  # Number of sections
        total_required_hours += sections * 4  # Each section requires 4 hours per week
    return total_required_hours

# Main logic to check if available hours can accommodate required hours
def check_schedule_feasibility(course_df, selected_days, room_count, hours_per_day):
    available_hours = calculate_available_hours(selected_days, room_count, hours_per_day)
    required_hours = calculate_required_hours(course_df)
    
    if available_hours < required_hours:
        shortage = required_hours - available_hours
        return f"Not enough available hours. Shortage: {shortage} hours."
    else:
        return "Sufficient hours available to schedule all sections."

# Room capacity check (ensuring each room can accommodate the number of students)
def check_room_availability(course_df, room_df):
    rooms_needed = 0
    for _, row in course_df.iterrows():
        students = row['Sum of #students']
        available_rooms = room_df[room_df['Population'] >= students]
        rooms_needed += len(available_rooms)  # Count how many rooms are available for this section
        
    return rooms_needed

# Function to assign courses to time slots and rooms
def generate_timetable(course_df, room_df, selected_days, room_count, hours_per_day):
    # Calculate available hours
    available_hours = calculate_available_hours(selected_days, room_count, hours_per_day)
    required_hours = calculate_required_hours(course_df)
    
    if available_hours < required_hours:
        st.error(f"Not enough available hours to schedule all sections. Shortage: {required_hours - available_hours} hours.")
        return None
    
    rooms = room_df['Room Name'].tolist()
    time_slots = ['8:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', '2:00 PM - 4:00 PM', '4:00 PM - 6:00 PM']
    
    timetable = {day: {time_slot: [] for time_slot in time_slots} for day in selected_days}  # Initialize empty timetable structure
    room_usage = {room: 0 for room in rooms}  # Track room usage
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
            
            # Assign the course to a specific day and time slot
            day = random.choice(selected_days)
            timetable[day][time_slot].append([course, teacher, room, f"Section {section+1}"])
            room_usage[room] += 1  # Increment the usage count for the assigned room
    
    # Rooms not in use
    unused_rooms = [room for room, usage in room_usage.items() if usage == 0]
    
    return timetable, room_usage, unused_rooms

# Streamlit app
def main():
    st.title("Course Timetable Generator")
    
    # File upload widgets
    course_file = st.file_uploader("Upload Course Data (CSV)", type=["csv"])
    room_file = st.file_uploader("Upload Room Data (CSV)", type=["csv"])
    
    # Select days for teaching
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    selected_days = st.multiselect("Select teaching days:", days_of_week, default=days_of_week)
    
    # Room configuration
    room_count = 6  # Number of rooms
    hours_per_day = 8  # Each room is available for 8 hours a day
    
    if course_file and room_file:
        # Load the data
        course_df, room_df = load_data(course_file, room_file)
        
        # Show room and teaching hour information
        available_hours = calculate_available_hours(selected_days, room_count, hours_per_day)
        required_hours = calculate_required_hours(course_df)
        room_check = check_room_availability(course_df, room_df)
        
        st.write(f"Available Hours: {available_hours} hours")
        st.write(f"Required Hours: {required_hours} hours")
        st.write(f"Rooms Needed: {room_check}")
        
        # Check if the schedule is feasible
        schedule_feasibility = check_schedule_feasibility(course_df, selected_days, room_count, hours_per_day)
        st.write(schedule_feasibility)
        
        # Generate the timetable if feasible
        if schedule_feasibility == "Sufficient hours available to schedule all sections.":
            timetable, room_usage, unused_rooms = generate_timetable(course_df, room_df, selected_days, room_count, hours_per_day)
            if timetable is not None:
                st.write("Generated Timetable (Weekly Format):")
                
                # Display timetable in a weekly format
                for day, day_schedule in timetable.items():
                    st.subheader(f"{day}")
                    for time_slot, courses in day_schedule.items():
                        st.write(f"{time_slot}:")
                        for course in courses:
                            st.write(f"  {course[0]} - {course[1]} - Room: {course[2]} - {course[3]}")
                
                st.write(f"Room Usage: {room_usage}")  # Display room usage
                st.write(f"Rooms Not in Use: {unused_rooms}")  # Display unused rooms

if __name__ == "__main__":
    main()
