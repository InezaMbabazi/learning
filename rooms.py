import streamlit as st
import pandas as pd
import io

# Function to generate the module template as an in-memory CSV
def create_module_template():
    data = {
        'Module Code': ['CS101', 'BUS202', 'DS301'],
        'Module Name': ['Introduction to Programming', 'Business Strategy', 'Data Science Basics'],
        'Credit Hours': [10, 15, 20]
    }
    df = pd.DataFrame(data)
    
    # Save the DataFrame to a StringIO object
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue()

# Function to generate the cohort template as an in-memory CSV
def create_cohort_template():
    data = {
        'Cohort Name': ['Computer Science', 'Business Admin', 'Data Science'],
        'Module Code': ['CS101', 'BUS202', 'DS301'],
        'Number of Students': [60, 45, 30],
        'Term Offered': ['Spring 2025', 'Fall 2025', 'Spring 2025']
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
        'Capacity': [30, 40, 50]
    }
    df = pd.DataFrame(data)
    
    # Save the DataFrame to a StringIO object
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue()

# Streamlit app
st.title("Workload Calculation for Room Occupancy")
st.subheader("Step 1: Download the Templates")

# Provide download links for the templates
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
