import streamlit as st
import pandas as pd
import io

def create_module_template():
    data = {"Cohort": [], "Total Students": [], "Module Code": [], "Module Name": [], "Credits": []}
    df = pd.DataFrame(data)
    return df

def create_room_template():
    data = {"Room Name": [], "Square Meters": []}
    df = pd.DataFrame(data)
    return df

def download_template(df, filename):
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output

st.title("Classroom Allocation System")

# Download templates
if st.button("Download Cohort Template"):
    st.download_button(
        label="Download Cohort Template",
        data=download_template(create_module_template(), "cohort_template.csv"),
        file_name="cohort_template.csv",
        mime="text/csv"
    )

if st.button("Download Room Template"):
    st.download_button(
        label="Download Room Template",
        data=download_template(create_room_template(), "room_template.csv"),
        file_name="room_template.csv",
        mime="text/csv"
    )

# Upload data
cohort_file = st.file_uploader("Upload Cohort Data", type=["csv"])
room_file = st.file_uploader("Upload Room Data", type=["csv"])

if cohort_file and room_file:
    cohort_df = pd.read_csv(cohort_file)
    room_df = pd.read_csv(room_file)
    
    # Display full tables
    st.write("### Cohort Data")
    st.dataframe(cohort_df)
    st.write("### Room Data")
    st.dataframe(room_df)
    
    # Compute Sections, Hours, and Square Meters
    def calculate_allocation(df, rooms):
        results = []
        for _, row in df.iterrows():
            cohort = row["Cohort"]
            students = row["Total Students"]
            module_code = row["Module Code"]
            module_name = row["Module Name"]
            credits = row["Credits"]
            
            # Calculate hours per week
            hours_per_week = (credits // 3) * 2  # Each 3 credits = 2 hours per week
            total_hours = hours_per_week * 12
            
            # Calculate sections based on room sizes
            total_space_needed = students * 1.5
            sorted_rooms = rooms.sort_values(by="Square Meters", ascending=False)
            sections = 0
            assigned_rooms = []
            for _, room in sorted_rooms.iterrows():
                if total_space_needed <= 0:
                    break
                sections += 1
                assigned_rooms.append(room["Room Name"])
                total_space_needed -= room["Square Meters"]
            
            results.append({
                "Cohort": cohort,
                "Module Code": module_code,
                "Module Name": module_name,
                "Sections": sections,
                "Total Hours": total_hours,
                "Total Square Meters": students * 1.5,
                "Assigned Rooms": ", ".join(assigned_rooms)
            })
        return pd.DataFrame(results)
    
    allocation_df = calculate_allocation(cohort_df, room_df)
    st.write("### Module Allocation Report")
    st.dataframe(allocation_df)
