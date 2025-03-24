import streamlit as st
import pandas as pd
import math

# Function to calculate the number of rooms and total hours for a module
def calculate_room_needs(number_of_students, credit_hours, room_capacity):
    hours_per_week = (credit_hours / 10) * 5  # Calculate weekly hours based on credit
    total_hours = hours_per_week * 12  # 12 weeks in a trimester
    
    # Calculate the number of rooms needed for the given number of students
    rooms_needed = math.ceil(number_of_students / room_capacity)
    
    return total_hours, rooms_needed

# Streamlit file uploader
st.title("Workload Calculation for Room Occupancy")
st.subheader("Step 1: Download the Templates")

# Provide download links for the templates
@st.cache
def create_module_template():
    # Define column names and sample data
    data = {
        'Module Code': ['CS101', 'BUS202', 'DS301'],
        'Module Name': ['Introduction to Programming', 'Business Strategy', 'Data Science Basics'],
        'Credit Hours': [10, 15, 20]
    }
    df = pd.DataFrame(data)
    file_path = '/mnt/data/module_template.csv'
    df.to_csv(file_path, index=False)
    return file_path

@st.cache
def create_cohort_template():
    # Define column names and sample data
    data = {
        'Cohort Name': ['Computer Science', 'Business Admin', 'Data Science'],
        'Module Code': ['CS101', 'BUS202', 'DS301'],
        'Number of Students': [60, 45, 30],
        'Term Offered': ['Spring 2025', 'Fall 2025', 'Spring 2025']
    }
    df = pd.DataFrame(data)
    file_path = '/mnt/data/cohort_template.csv'
    df.to_csv(file_path, index=False)
    return file_path

@st.cache
def create_room_template():
    # Define column names and sample data
    data = {
        'Room Name': ['Room 101', 'Room 102', 'Room 103'],
        'Capacity': [30, 40, 50]
    }
    df = pd.DataFrame(data)
    file_path = '/mnt/data/room_template.csv'
    df.to_csv(file_path, index=False)
    return file_path

# Buttons to download templates
st.download_button(
    label="Download Module Template",
    data=create_module_template(),
    file_name="module_template.csv",
    mime="text/csv"
)

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
uploaded_file_module = st.file_uploader("Upload Module Table (CSV)", type="csv", key="module")
uploaded_file_cohort = st.file_uploader("Upload Cohort Table (CSV)", type="csv", key="cohort")
uploaded_file_room = st.file_uploader("Upload Room Table (CSV)", type="csv", key="room")

if uploaded_file_module is not None and uploaded_file_cohort is not None and uploaded_file_room is not None:
    # Read the uploaded CSV files into DataFrames
    df_modules = pd.read_csv(uploaded_file_module)
    df_cohorts = pd.read_csv(uploaded_file_cohort)
    df_rooms = pd.read_csv(uploaded_file_room)

    # Display the uploaded datasets
    st.subheader("Modules Table:")
    st.write(df_modules)

    st.subheader("Cohorts Table:")
    st.write(df_cohorts)

    st.subheader("Rooms Table:")
    st.write(df_rooms)

    st.subheader("Workload Calculation Results:")

    # Loop through each row in the cohort table to calculate room needs for each module
    results = []
    for index, cohort_row in df_cohorts.iterrows():
        # Find the corresponding module
        module_row = df_modules[df_modules['Module Code'] == cohort_row['Module Code']].iloc[0]
        # Find the corresponding room capacity
        room_row = df_rooms[df_rooms['Capacity'] >= cohort_row['Number of Students']].iloc[0]
        
        total_hours, rooms_needed = calculate_room_needs(cohort_row['Number of Students'], module_row['Credit Hours'], room_row['Capacity'])
        
        results.append({
            'Cohort/Program': cohort_row['Cohort Name'],
            'Module Name': module_row['Module Name'],
            'Term Offered': cohort_row['Term Offered'],
            'Total Hours (12 weeks)': total_hours,
            'Rooms Needed': rooms_needed
        })
    
    # Create a DataFrame from the results and display it
    result_df = pd.DataFrame(results)
    st.write(result_df)

    # Optional: Create a bar chart to visualize the room occupancy
    st.bar_chart(result_df['Rooms Needed'])

# Add instructions on the sidebar for the user
st.sidebar.header('Instructions')
st.sidebar.write("""
1. Download the **Module Template**, **Cohort Template**, and **Room Template**.
2. Fill in the required data in each template and save them as CSV files.
3. Upload the CSV files with your data.
4. The app will calculate the total hours required for each module and the number of rooms needed.
""")
