import streamlit as st
import pandas as pd
import math

# Function to calculate the required sections and total hours for each module
def calculate_room_needs(number_of_students, credits, room_area, weeks=12):
    students_per_room = room_area // 1.5  # Each student requires 1.5 m²
    sections_needed = math.ceil(number_of_students / students_per_room)

    if credits == 10:
        hours_per_week = 5  # 10 credits = 5 hours per week
    elif credits == 15:
        hours_per_week = 5  # 15 credits = 5 hours per week
    elif credits == 20:
        hours_per_week = 8  # 20 credits = 8 hours per week
    else:
        hours_per_week = 0  # Default to 0 if credits are not standard

    total_hours_needed = hours_per_week * weeks
    return sections_needed, total_hours_needed, students_per_room

# Streamlit UI
st.title("Module Room Allocation Report")

# File uploader
uploaded_file = st.file_uploader("Upload your cohort data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Read file into DataFrame
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Expected columns: Cohort, Students, Module Code, Module Name, Credits
    st.write("### Uploaded Data Preview:")
    st.write(df.head())

    # Upload room information
    room_file = st.file_uploader("Upload room capacity data (CSV or Excel)", type=["csv", "xlsx"])
    
    if room_file:
        if room_file.name.endswith('.csv'):
            rooms_df = pd.read_csv(room_file)
        else:
            rooms_df = pd.read_excel(room_file)

        # Expected columns: Room Name, Area (m²)
        st.write("### Uploaded Room Data Preview:")
        st.write(rooms_df.head())

        # Process each module
        results_list = []

        for _, row in df.iterrows():
            cohort_name = row["Cohort"]
            num_students = row["Students"]
            module_code = row["Module Code"]
            module_name = row["Module Name"]
            credits = row["Credits"]

            # Assign room based on first available room in the list
            assigned_rooms = []
            total_square_meters_used = 0
            total_sections = 0
            total_hours = 0

            for _, room_row in rooms_df.iterrows():
                room_name = room_row["Room Name"]
                room_area = room_row["Area (m²)"]

                sections_needed, total_hours_needed, students_per_room = calculate_room_needs(
                    num_students, credits, room_area
                )

                total_sections += sections_needed
                total_hours += total_hours_needed
                total_square_meters_used += sections_needed * room_area
                assigned_rooms.append(room_name)

                # Break once we have assigned the required sections
                if total_sections >= sections_needed:
                    break

            # Store results
            results_list.append({
                "Cohort": cohort_name,
                "Module Code": module_code,
                "Module Name": module_name,
                "Total Sections Assigned": total_sections,
                "Total Square Meters Used": total_square_meters_used,
                "Total Hours Needed (Term)": total_hours,
                "Assigned Rooms": ', '.join(assigned_rooms[:total_sections])
            })

        # Convert results to DataFrame
        result_df = pd.DataFrame(results_list)

        # Display results
        st.subheader("Room Allocation Report")
        st.write(result_df)

        # Option to download report
        st.download_button(
            label="Download Report as CSV",
            data=result_df.to_csv(index=False),
            file_name="room_allocation_report.csv",
            mime="text/csv"
        )
