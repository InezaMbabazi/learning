import streamlit as st
import pandas as pd
import io
import math

# Function to generate the cohort template as an in-memory CSV
def create_cohort_template():
    data = {
        'Cohort Name': ['Computer Science', 'Business Admin', 'Data Science'],
        'Number of Students': [200, 150, 100],
        'Module Code': ['CS101', 'BUS202', 'DS301'],
        'Module Name': ['Introduction to Programming', 'Business Strategy', 'Data Science Basics'],
        'Credits': [10, 15, 20],
        'Term Offered': ['Spring 2025', 'Fall 2025', 'Spring 2025'],
    }
    df = pd.DataFrame(data)
    
    # Save the DataFrame to a StringIO object
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue()

# Function to generate the room template as an in-memory CSV
def create_room_template():
    data = {
        'Room Name': ['Room 101', 'Room 102', 'Room 103'],
        'Area (m²)': [100, 150, 200]  # Area in square meters
    }
    df = pd.DataFrame(data)
    
    # Save the DataFrame to a StringIO object
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue()

# Function to calculate the rooms and sessions required for a cohort based on room capacity
def calculate_room_needs(number_of_students, credits, room_area):
    # Calculate capacity per room based on square meters (1.5 m² per student)
    students_per_room = room_area // 1.5
    
    # Calculate how many rooms are needed for the cohort
    rooms_needed = math.ceil(number_of_students / students_per_room)
    
    # Calculate total room usage per week (assuming modules are taught twice a week)
    total_sessions_needed = rooms_needed * 2  # Twice a week
    
    return rooms_needed, total_sessions_needed

# Streamlit app
st.title("Workload Calculation for Room Occupancy")
st.subheader("Step 1: Download the Templates")

# Provide download links for the templates
st.download_button(
    label="Download Cohort Template",
    data=create_cohort_template(),
    file_name="cohort_template.csv",
    mime="text/csv"
)

st.download_button(
    label="Download Room Template",
    data=create_room_template(),
    file_name="room_template.csv",
    mime="text/csv"
)

st.subheader("Step 2: Upload Your Data")

# File uploaders
uploaded_file_cohort = st.file_uploader("Upload Cohort Table (CSV)", type="csv", key="cohort")
uploaded_file_room = st.file_uploader("Upload Room Table (CSV)", type="csv", key="room")

if uploaded_file_cohort is not None and uploaded_file_room is not None:
    # Read the uploaded CSV files into DataFrames
    df_cohorts = pd.read_csv(uploaded_file_cohort)
    df_rooms = pd.read_csv(uploaded_file_room)

    # Display the uploaded datasets
    st.subheader("Cohorts Table:")
    st.write(df_cohorts)

    st.subheader("Rooms Table:")
    st.write(df_rooms)

    st.subheader("Workload Calculation Results:")

    # Loop through each row in the cohort table to calculate room needs for each module
    results = []
    for index, cohort_row in df_cohorts.iterrows():
        # Loop through each room to calculate the number of rooms needed
        for _, room_row in df_rooms.iterrows():
            rooms_needed, total_sessions_needed = calculate_room_needs(
                cohort_row['Number of Students'], 
                cohort_row['Credits'], 
                room_row['Area (m²)']
            )
            
            # Each room is available for 8 hours a day, 5 days a week (excluding lunch)
            total_room_hours_per_week = 8 * 5  # 8 hours per day, 5 days per week
            
            # If the number of sessions exceeds the available room hours, flag a shortage
            if total_sessions_needed > total_room_hours_per_week:
                shortage_flag = 'Yes'
            else:
                shortage_flag = 'No'
            
            results.append({
                'Cohort/Program': cohort_row['Cohort Name'],
                'Module Name': cohort_row['Module Name'],
                'Term Offered': cohort_row['Term Offered'],
                'Room Name': room_row['Room Name'],
                'Room Area (m²)': room_row['Area (m²)'],
                'Rooms Needed': rooms_needed,
                'Total Sessions Needed (per week)': total_sessions_needed,
                'Shortage': shortage_flag
            })
    
    # Create a DataFrame from the results and display it
    result_df = pd.DataFrame(results)
    st.write(result_df)

    # Optional: Create a bar chart to visualize the room occupancy
    st.bar_chart(result_df['Rooms Needed'])

# Add instructions on the sidebar for the user
st.sidebar.header('Instructions')
st.sidebar.write("""
1. Download the **Cohort Template** and **Room Template**.
2. Fill in the required data in each template and save them as CSV files.
3. Upload the CSV files with your data.
4. The app will calculate the rooms needed for each cohort and flag any room shortages.
""")
