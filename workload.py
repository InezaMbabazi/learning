import pandas as pd
import streamlit as st

# Streamlit UI
def main():
    st.title("Lecturer Workload Automation")
    
    # File uploader for lecturer and student data
    lecturer_file = st.file_uploader("Upload Lecturer Data (CSV)", type=["csv"])
    student_file = st.file_uploader("Upload Student Data (CSV)", type=["csv"])
    
    if lecturer_file and student_file:
        df_lecturers = pd.read_csv(lecturer_file)
        df_students = pd.read_csv(student_file)
        
        # Define credit-hour mapping
        credit_hours_map = {20: 6, 15: 5, 10: 4}
        
        # Calculate total hours needed per module (per term)
        df_students["Total Hours Needed"] = df_students["Credits"].map(credit_hours_map) * 12
        
        # Initialize workload tracker
        lecturer_hours = {name: 0 for name in df_lecturers["Teacher's name"]}
        lecturer_workload = []
        unassigned_modules = []
        
        # Assign modules to lecturers ensuring fair distribution
        for _, row in df_students.iterrows():
            module_code = row["Code"]
            hours_needed = row["Total Hours Needed"]
            
            available_lecturers = df_lecturers[df_lecturers["Module Code"] == module_code]
            
            # Sort lecturers by current workload for fair distribution
            available_lecturers = available_lecturers.sort_values(by=["Teacher's name"], key=lambda x: x.map(lecturer_hours))
            
            assigned = False
            for _, lecturer in available_lecturers.iterrows():
                lecturer_name = lecturer["Teacher's name"]
                term_workload = lecturer["Term Workload"]
                
                # Ensure workload constraints
                if lecturer_hours[lecturer_name] + hours_needed <= term_workload and (hours_needed / 12) <= 12:
                    lecturer_workload.append({
                        "Lecturer": lecturer_name,
                        "Module Code": module_code,
                        "Hours Assigned": hours_needed
                    })
                    lecturer_hours[lecturer_name] += hours_needed
                    assigned = True
                    break  # Assign to only one lecturer per module
            
            if not assigned:
                unassigned_modules.append({
                    "Module Code": module_code,
                    "Hours Needed": hours_needed
                })
        
        # Convert results to DataFrames
        workload_df = pd.DataFrame(lecturer_workload)
        unassigned_df = pd.DataFrame(unassigned_modules)
        
        # Display assigned workload
        st.write("### Assigned Workload")
        st.dataframe(workload_df)
        
        # Display total assigned hours per lecturer
        lecturer_summary = pd.DataFrame(list(lecturer_hours.items()), columns=["Lecturer", "Total Hours Assigned"])
        st.write("### Lecturer Workload Summary")
        st.dataframe(lecturer_summary)
        
        # Display unassigned modules if any
        if not unassigned_df.empty:
            st.write("### Unassigned Modules")
            st.dataframe(unassigned_df)
            st.download_button(
                label="Download Unassigned Modules CSV",
                data=unassigned_df.to_csv(index=False).encode("utf-8"),
                file_name="unassigned_modules.csv",
                mime="text/csv"
            )
        
        # Provide download links
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
        
    # Provide template download buttons
    st.write("### Download Templates")
    lecturer_template = "Teacher's name,Module Code,Module Name,Term Workload\nElisa Hakizamungu,ETH82102,Business Ethics and Corporate Governance,144"
    student_template = "Cohort,Number of Students,Module Name,Code,Sections,Credits\n2024,60,Business Ethics,ETH82102,3,20"
    
    st.download_button("Download Lecturer Template", lecturer_template.encode("utf-8"), "lecturer_template.csv", "text/csv")
    st.download_button("Download Student Template", student_template.encode("utf-8"), "student_template.csv", "text/csv")

if __name__ == "__main__":
    main()
