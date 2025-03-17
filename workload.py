import pandas as pd 
import streamlit as st
import io

# Streamlit UI
def main():
    st.title("Lecturer Workload Automation")
    
    # File uploader for lecturer and student data
    lecturer_file = st.file_uploader("Upload Lecturer Data (CSV)", type=["csv"])
    student_file = st.file_uploader("Upload Student Data (CSV)", type=["csv"])
    
    if lecturer_file and student_file:
        df_lecturers = pd.read_csv(lecturer_file)
        df_students = pd.read_csv(student_file)
        
        # Define credit-hour mapping (credits: hours per week)
        credit_hours_map = {20: 8, 15: 6, 10: 5}
        
        # Calculate total hours needed per module per term (weekly hours * 12 weeks * number of sections)
        df_students["Total Hours Needed"] = df_students["Credits"].map(credit_hours_map).fillna(0) * 12 * df_students["Sections"]
        
        # Initialize workload tracker
        lecturer_hours = {name: 0 for name in df_lecturers["Teacher's name"]}
        lecturer_workload = []
        unassigned_modules = []
        
        # Assign modules to lecturers based on their available workload
        for _, row in df_students.iterrows():
            module_code = row["Code"]
            module_name = row["Module Name"]
            hours_needed = row["Total Hours Needed"]
            sections_needed = row["Sections"]
            
            remaining_sections = sections_needed  # Sections to be assigned
            
            # Filter lecturers qualified to teach this module
            available_lecturers = df_lecturers[df_lecturers["Module Code"] == module_code].copy()
            available_lecturers["Current Load"] = available_lecturers["Teacher's name"].map(lecturer_hours)
            available_lecturers = available_lecturers.sort_values(by="Current Load")

            # Distribute sections across lecturers
            for _, lecturer in available_lecturers.iterrows():
                lecturer_name = lecturer["Teacher's name"]
                term_workload = lecturer["Term Workload"]
                max_hours_available = term_workload - lecturer_hours[lecturer_name]
                
                if max_hours_available > 0:
                    # Calculate max sections this lecturer can handle
                    max_sections = max_hours_available // (hours_needed / sections_needed)
                    sections_assigned = min(remaining_sections, max_sections)
                    
                    if sections_assigned > 0:
                        # Assign the sections to the lecturer
                        hours_assigned = sections_assigned * (hours_needed / sections_needed)
                        lecturer_workload.append({
                            "Lecturer": lecturer_name,
                            "Module Code": module_code,
                            "Module Name": module_name,
                            "Sections Assigned": sections_assigned,
                            "Hours Assigned": hours_assigned
                        })
                        
                        # Update the lecturer's total assigned hours
                        lecturer_hours[lecturer_name] += hours_assigned
                        remaining_sections -= sections_assigned
                
                # If no more sections are left to assign, break
                if remaining_sections == 0:
                    break

            # If some sections are unassigned, add them to the unassigned list
            if remaining_sections > 0:
                unassigned_modules.append({
                    "Module Code": module_code,
                    "Module Name": module_name,
                    "Sections Remaining": remaining_sections
                })
        
        # Convert results to DataFrames
        workload_df = pd.DataFrame(lecturer_workload)

        # Aggregate total hours and total sections per lecturer
        lecturer_summary = pd.DataFrame(list(lecturer_hours.items()), columns=["Lecturer", "Total Hours Assigned"])

        # Aggregate the total sections assigned to each lecturer
        section_summary = pd.DataFrame(lecturer_workload)
        section_summary = section_summary.groupby("Lecturer")["Sections Assigned"].sum().reset_index()
        section_summary = section_summary.rename(columns={"Sections Assigned": "Total Sections Assigned"})

        # Merge both summaries: total hours and total sections
        lecturer_summary = pd.merge(lecturer_summary, section_summary, on="Lecturer", how="left")

        # Display outputs
        st.write("### Assigned Workload")
        st.dataframe(workload_df)

        st.write("### Lecturer Workload Summary")
        st.dataframe(lecturer_summary)

        # If some sections are unassigned, add them to the unassigned list
        if unassigned_modules:  # Check if
