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
        
        # Assign modules to lecturers
        for _, row in df_students.iterrows():
            module_code = row["Code"]
            module_name = row["Module Name"]
            hours_needed = row["Total Hours Needed"]
            sections_remaining = row["Sections"]
            
            # Filter lecturers qualified to teach this module
            available_lecturers = df_lecturers[df_lecturers["Module Code"] == module_code].copy()
            available_lecturers["Current Load"] = available_lecturers["Teacher's name"].map(lecturer_hours)
            available_lecturers = available_lecturers.sort_values(by="Current Load")
            
            assigned = False
            for _, lecturer in available_lecturers.iterrows():
                lecturer_name = lecturer["Teacher's name"]
                term_workload = lecturer["Term Workload"]
                available_hours = term_workload - lecturer_hours[lecturer_name]
                
                if available_hours > 0:
                    hours_to_assign = min(hours_needed, available_hours)
                    sections_to_assign = min(sections_remaining, hours_to_assign // (credit_hours_map[row["Credits"]] * 12))
                    
                    if sections_to_assign > 0:
                        lecturer_workload.append({
                            "Lecturer": lecturer_name,
                            "Module Code": module_code,
                            "Module Name": module_name,
                            "Hours Assigned": hours_to_assign,
                            "Sections Assigned": sections_to_assign
                        })
                        lecturer_hours[lecturer_name] += hours_to_assign
                        hours_needed -= hours_to_assign
                        sections_remaining -= sections_to_assign
                        
                    if hours_needed <= 0:
                        assigned = True
                        break
            
            if not assigned:
                unassigned_modules.append({
                    "Module Code": module_code,
                    "Module Name": module_name,
                    "Hours Needed": hours_needed
                })
        
        # Convert results to DataFrames
        workload_df = pd.DataFrame(lecturer_workload)
        unassigned_df = pd.DataFrame(unassigned_modules)
        
        # Create Lecturer Summary with Total Workload
        lecturer_summary = df_lecturers[["Teacher's name", "Term Workload"]].copy()
        lecturer_summary = lecturer_summary.rename(columns={"Term Workload": "Total Workload"})
        lecturer_summary["Total Hours Assigned"] = lecturer_summary["Teacher's name"].map(lecturer_hours).fillna(0)
        
        # Display outputs
        st.write("### Assigned Workload")
        st.dataframe(workload_df)
        
        st.write("### Lecturer Workload Summary")
        st.dataframe(lecturer_summary)
        
        if not unassigned_df.empty:
            st.write("### Unassigned Modules")
            st.dataframe(unassigned_df)
            st.download_button(
                label="Download Unassigned Modules CSV",
                data=unassigned_df.to_csv(index=False).encode("utf-8"),
                file_name="unassigned_modules.csv",
                mime="text/csv"
            )
        
        # Provide CSV download buttons
        st.download_button(
            label="Download Workload CSV",
            data=workload_df.to_csv(index=False).encode("utf-8"),
            file_name="lecturer_workload.csv",
            mime="text/csv"
        )
        
        st.download_button(
            label="Download Lecturer Summary CSV",
            data=lecturer_summary.to_csv(index=False).encode("utf-8"),
            file_name="lecturer_summary.csv",
            mime="text/csv"
        )
    
    # Provide templates for users
    st.write("### Download Templates")
    
    # Updated Lecturer Template with Total Workload
    lecturer_template = io.StringIO()
    lecturer_template_df = pd.DataFrame({
        "Teacher's name": ["Elisa Hakizamungu", "Jean Claude"],
        "Module Code": ["ETH82102", "MGT81201"],
        "Module Name": ["Business Ethics and Corporate Governance", "Strategic Management"],
        "Term Workload": [144, 144],
        "Total Workload": [288, 288]  # Example total workload per year (or for two terms)
    })
    lecturer_template_df.to_csv(lecturer_template, index=False)
    st.download_button(
        "Download Lecturer Template",
        data=lecturer_template.getvalue().encode("utf-8"),
        file_name="lecturer_template.csv",
        mime="text/csv"
    )
    
    # Student Template
    student_template = io.StringIO()
    student_template_df = pd.DataFrame({
        "Cohort": [2024],
        "Number of Students": [60],
        "Module Name": ["Business Ethics"],
        "Code": ["ETH82102"],
        "Sections": [3],
        "Credits": [20]
    })
    student_template_df.to_csv(student_template, index=False)
    st.download_button(
        "Download Student Template",
        data=student_template.getvalue().encode("utf-8"),
        file_name="student_template.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
