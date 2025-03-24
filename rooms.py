import streamlit as st
import pandas as pd
import math
import io

# Database Initialization (Stored in Session State)
if "cohort_db" not in st.session_state:
    st.session_state.cohort_db = pd.DataFrame(columns=["Cohort", "Students", "Module Code", "Module Name", "Credits"])

if "room_db" not in st.session_state:
    st.session_state.room_db = pd.DataFrame(columns=["Room Name", "Area (m²)"])

# Function to generate CSV template
def generate_csv_template(df, filename):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

# Function to calculate sections, total hours, and square meters used
def calculate_room_needs(number_of_students, credits, room_area, weeks=12):
    students_per_room = room_area // 1.5  # Each student requires 1.5 m²
    sections_needed = math.ceil(number_of_students / students_per_room)

    hours_per_week = (credits // 5) * 2  # 10 credits = 5 hrs/week, 15 credits = 5 hrs/week, 20 credits = 8 hrs/week
    total_hours_needed = hours_per_week * weeks

    return sections_needed, total_hours_needed, students_per_room

# Streamlit UI
st.title("Module Room Allocation System")

# **Download Templates**
st.subheader("Download Data Entry Templates")
col1, col2 = st.columns(2)

# Cohort Template
with col1:
    cohort_template = pd.DataFrame({
        "Cohort": ["Example BsBA 2024"],
        "Students": [50],
        "Module Code": ["BSA82102"],
        "Module Name": ["Python for Business Analytics"],
        "Credits": [15]
    })
    st.download_button(
        label="Download Cohort Template",
        data=generate_csv_template(cohort_template, "cohort_template.csv"),
        file_name="cohort_template.csv",
        mime="text/csv"
    )

# Room Template
with col2:
    room_template = pd.DataFrame({
        "Room Name": ["Room 101"],
        "Area (m²)": [150]
    })
    st.download_button(
        label="Download Room Template",
        data=generate_csv_template(room_template, "room_template.csv"),
        file_name="room_template.csv",
        mime="text/csv"
    )

# **Upload Cohort Data**
st.subheader("Upload Cohort Data")
uploaded_cohort = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded_cohort:
    if uploaded_cohort.name.endswith('.csv'):
        df_cohort = pd.read_csv(uploaded_cohort)
    else:
        df_cohort = pd.read_excel(uploaded_cohort)
    
    st.session_state.cohort_db = df_cohort  # Store in session state
    st.success("✅ Cohort Data Uploaded Successfully!")
    st.write(df_cohort.head())

# **Upload Room Data**
st.subheader("Upload Room Data")
uploaded_room = st.file_uploader("Upload Room Capacity CSV or Excel", type=["csv", "xlsx"])

if uploaded_room:
    if uploaded_room.name.endswith('.csv'):
        df_room = pd.read_csv(uploaded_room)
    else:
        df_room = pd.read_excel(uploaded_room)
    
    st.session_state.room_db = df_room  # Store in session state
    st.success("✅ Room Data Uploaded Successfully!")
    st.write(df_room.head())

# **Generate Report if Data is Available**
if not st.session_state.cohort_db.empty and not st.session_state.room_db.empty:
    st.subheader("Generating Room Allocation Report...")

    results_list = []

    for _, row in st.session_state.cohort_db.iterrows():
        cohort_name = row["Cohort"]
        num_students = row["Students"]
        module_code = row["Module Code"]
        module_name = row["Module Name"]
        credits = row["Credits"]

        # Assign room based on first available room
        assigned_rooms = []
        total_square_meters_used = 0
        total_sections = 0
        total_hours = 0

        for _, room_row in st.session_state.room_db.iterrows():
            room_name = room_row["Room Name"]
            room_area = room_row["Area (m²)"]

            sections_needed, total_hours_needed, students_per_room = calculate_room_needs(
                num_students, credits, room_area
            )

            total_sections += sections_needed
            total_hours += total_hours_needed
            total_square_meters_used += sections_needed * room_area
            assigned_rooms.append(room_name)

            # Stop when enough sections are assigned
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

    # **Download Report**
    st.download_button(
        label="Download Report as CSV",
        data=result_df.to_csv(index=False),
        file_name="room_allocation_report.csv",
        mime="text/csv"
    )
