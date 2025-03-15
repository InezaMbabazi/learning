import pandas as pd
import streamlit as st

# Streamlit UI
def main():
    st.title("Lecturer Workload Automation")
    
    # File uploader for lecturer data
    lecturer_file = st.file_uploader("Upload Lecturer Data (CSV)", type=["csv"])
    student_file = st.file_uploader("Upload Student Data (CSV)", type=["csv"])
    
    if lecturer_file and student_file:
        df_lecturers = pd.read_csv(lecturer_file)
        df_students = pd.read_csv(student_file)
        
        # Calculate total hours needed per module
        df_students["Total Hours Needed"] = df_students["Sections"] * 4
        
        # Initialize workload tracker
        lecturer_hours = {name: 0 for name in df_lecturers["Teacher's Name"]}
        lecturer_workload = []
        
        # Assign modules to lecturers
        for _, row in df_students.iterrows():
            module_code = row["Code"]
            hours_needed = row["Total Hours Needed"]
            
            available_lecturers = df_lecturers[df_lecturers["Module Code"] == module_code]
            
            for _, lecturer in available_lecturers.iterrows():
                lecturer_name = lecturer["Teacher's Name"]
                
                # Check if lecturer has capacity
                if lecturer_hours[lecturer_name] + hours_needed <= 12:
                    lecturer_workload.append({
                        "Lecturer": lecturer_name,
                        "Module Code": module_code,
                        "Hours Assigned": hours_needed
                    })
                    lecturer_hours[lecturer_name] += hours_needed
                    break  # Assign to only one lecturer per module
        
        # Convert results to DataFrame
        workload_df = pd.DataFrame(lecturer_workload)
        
        # Display result
        st.write("### Assigned Workload")
        st.dataframe(workload_df)
        
        # Provide download link
        st.download_button(
            label="Download Workload CSV",
            data=workload_df.to_csv(index=False).encode("utf-8"),
            file_name="lecturer_workload.csv",
            mime="text/csv"
        )
        
    # Provide template download buttons
    st.write("### Download Templates")
    lecturer_template = "Teacher's Name,Module Code,Module Name\nElisa Hakizamungu,ETH82102,Business Ethics and Corporate Governance"
    student_template = "Cohort,Number of Students,Code,Sections\n2024,60,ETH82102,3"
    
    st.download_button("Download Lecturer Template", lecturer_template.encode("utf-8"), "lecturer_template.csv", "text/csv")
    st.download_button("Download Student Template", student_template.encode("utf-8"), "student_template.csv", "text/csv")

if __name__ == "__main__":
    main()
