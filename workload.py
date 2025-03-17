import pandas as pd
import streamlit as st
import io

# Streamlit UI
def main():
    st.title("Lecturer Workload Automation")

    # Weekly teaching hours input (Dynamic)
    weekly_hours = st.slider("Set Maximum Weekly Teaching Hours", min_value=6, max_value=20, value=12, step=1)
    max_term_workload = weekly_hours * 12  # Adjusted max workload per term

    # File uploader for lecturer and student data
    lecturer_file = st.file_uploader("Upload Lecturer Data (CSV)", type=["csv"])
    student_file = st.file_uploader("Upload Student Data (CSV)", type=["csv"])

    if lecturer_file and student_file:
        df_lecturers = pd.read_csv(lecturer_file)
        df_students = pd.read_csv(student_file)

        # Define credit-hour mapping (credits: hours per week)
        credit_hours_map = {20: 8, 15: 6, 10: 5}  # Example of credits to hours mapping
        # Calculate total hours needed per module per term
        df_students["Total Hours Needed"] = df_students["Credits"].map(credit_hours_map).fillna(0) * 12 * df_students["Sections"]

        # Initialize workload tracker
        lecturer_hours = {name: 0 for name in df_lecturers["Teacher's name"]}
        lecturer_workload = []
        unassigned_modules = []

        # Assign modules to lecturers based on available workload
        for _, row in df_students.iterrows():
            module_code = row["Code"]
            module_name = row["Module Name"]
            hours_needed = row["Total Hours Needed"]
            sections_needed = row["Sections"]

            remaining_sections = sections_needed  # Sections to be assigned

            # Filter lecturers qualified for this module
            available_lecturers = df_lecturers[df_lecturers["Module Code"] == module_code].copy()
            available_lecturers["Current Load"] = available_lecturers["Teacher's name"].map(lecturer_hours)
            available_lecturers = available_lecturers.sort_values(by="Current Load")

            # Calculate the number of sections based on weekly hours and course credits
            for _, lecturer in available_lecturers.iterrows():
                lecturer_name = lecturer["Teacher's name"]
                term_workload = lecturer["Term Workload"]
                total_workload = lecturer["Total Workload"]

                # Calculate how many hours the lecturer can still take
                max_hours_available = total_workload - lecturer_hours[lecturer_name]

                if max_hours_available > 0:
                    # Calculate max sections this lecturer can handle (based on credits and hours)
                    hours_per_section = credit_hours_map.get(row["Credits"], 0)  # Calculate hours per section
                    max_sections = max_hours_available // hours_per_section
                    sections_assigned = min(remaining_sections, max_sections)

                    if sections_assigned > 0:
                        # Assign the sections to the lecturer
                        hours_assigned = sections_assigned * hours_per_section
                        
                        # Prevent exceeding term workload or total workload
                        if lecturer_hours[lecturer_name] + hours_assigned > total_workload:
                            continue  # Skip if it exceeds max total workload

                        lecturer_workload.append({
                            "Lecturer": lecturer_name,
                            "Module Code": module_code,
                            "Module Name": module_name,
                            "Sections Assigned": sections_assigned,
                            "Hours Assigned": hours_assigned
                        })

                        # Update lecturer's total assigned hours
                        lecturer_hours[lecturer_name] += hours_assigned
                        remaining_sections -= sections_assigned

                # If no more sections left to assign, break
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
        lecturer_summary = pd.DataFrame(list(lecturer_hours.items()), columns=["Lecturer", "Total Hours Assigned"])

        # Aggregate sections per lecturer
        section_summary = pd.DataFrame(lecturer_workload)
        section_summary = section_summary.groupby("Lecturer")["Sections Assigned"].sum().reset_index()
        section_summary = section_summary.rename(columns={"Sections Assigned": "Total Sections Assigned"})

        # Merge workload summary
        lecturer_summary = pd.merge(lecturer_summary, section_summary, on="Lecturer", how="left")

        # Display outputs
        st.write("### Assigned Workload")
        st.dataframe(workload_df)

        st.write("### Lecturer Workload Summary")
        st.dataframe(lecturer_summary)

        # Display unassigned modules
        if unassigned_modules:
            unassigned_df = pd.DataFrame(unassigned_modules)
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

    # Lecturer Template
    lecturer_template = io.StringIO()
    lecturer_template_df = pd.DataFrame({
        "Teacher's name": ["Elisa Hakizamungu", "Jean Claude"],
        "Module Code": ["ETH82102", "MGT81201"],
        "Module Name": ["Business Ethics and Corporate Governance", "Strategic Management"],
        "Term Workload": [144, 144],
        "Total Workload": [288, 288]
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
