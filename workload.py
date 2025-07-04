import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Workload Management System", layout="wide")

st.title("📚 Automated Workload Management System")

# Upload datasets
st.sidebar.header("Upload Datasets")
lecturer_file = st.sidebar.file_uploader("Upload Lecturers Dataset", type=["csv", "xlsx"])
module_file = st.sidebar.file_uploader("Upload Modules Dataset", type=["csv", "xlsx"])

if lecturer_file and module_file:
    # Read uploaded files
    if lecturer_file.name.endswith('.csv'):
        lecturers_df = pd.read_csv(lecturer_file)
    else:
        lecturers_df = pd.read_excel(lecturer_file)

    if module_file.name.endswith('.csv'):
        modules_df = pd.read_csv(module_file)
    else:
        modules_df = pd.read_excel(module_file)

    # Clean column names
    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()

    # Trimester selection
    trimester_options = modules_df["When to Take Place"].dropna().unique()
    selected_trimester = st.selectbox("📅 Select When to Take Place (Trimester)", sorted(trimester_options))

    # Filter modules by trimester
    filtered_modules = modules_df[modules_df["When to Take Place"] == selected_trimester].copy()

    # Calculate weekly hours for modules
    def get_weekly_hours(credits):
        return 6 if credits == 20 else 4 if credits in [10, 15] else 0

    filtered_modules["Weekly Hours"] = filtered_modules["Credits"].apply(get_weekly_hours)

    # 🔁 Reset: track assigned hours per lecturer name (not per row)
    lecturer_hours = {}

    assignments = []

    for _, module in filtered_modules.iterrows():
        module_code = module["Code"]
        total_students = int(module["Number of Students"])
        max_students_per_group = 70
        num_groups = math.ceil(total_students / max_students_per_group)
        hours_needed = module["Weekly Hours"]

        for group_index in range(num_groups):
            group_size = (
                max_students_per_group
                if group_index < num_groups - 1
                else total_students - max_students_per_group * (num_groups - 1)
            )

            # Find all lecturers who can teach this module
            matching_lecturers = lecturers_df[lecturers_df["Module Code"] == module_code].copy()

            # Init hours if not already
            for name in matching_lecturers["Teacher's name"].unique():
                if name not in lecturer_hours:
                    lecturer_hours[name] = 0

            # Calculate available hours and sort
            matching_lecturers["Assigned Hours"] = matching_lecturers["Teacher's name"].map(lecturer_hours)
            matching_lecturers["Remaining"] = 18 - matching_lecturers["Assigned Hours"]
            matching_lecturers = matching_lecturers.sort_values(by="Remaining", ascending=False)

            assigned = False
            for _, lecturer in matching_lecturers.iterrows():
                name = lecturer["Teacher's name"]
                if lecturer_hours[name] + hours_needed <= 18:
                    assignments.append({
                        "Lecturer": name,
                        "Module Code": module_code,
                        "Module Name": module["Module Name"],
                        "Credits": module["Credits"],
                        "Cohort": module["Cohort"],
                        "Programme": module["Programme"],
                        "Weekly Hours": hours_needed,
                        "Group Size": group_size,
                        "Group Number": group_index + 1,
                        "Trimester": selected_trimester
                    })
                    lecturer_hours[name] += hours_needed
                    assigned = True
                    break

            if not assigned:
                assignments.append({
                    "Lecturer": "❌ Not Assigned",
                    "Module Code": module_code,
                    "Module Name": module["Module Name"],
                    "Credits": module["Credits"],
                    "Cohort": module["Cohort"],
                    "Programme": module["Programme"],
                    "Weekly Hours": hours_needed,
                    "Group Size": group_size,
                    "Group Number": group_index + 1,
                    "Trimester": selected_trimester
                })

    # Results table
    result_df = pd.DataFrame(assignments)

    st.subheader("✅ Workload Assignment Results")
    st.dataframe(result_df, use_container_width=True)

    # Download
    csv = result_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Assignment Results as CSV", csv, "workload_assignments.csv", "text/csv")

    # Summary
    summary = pd.DataFrame(list(lecturer_hours.items()), columns=["Lecturer", "Total Assigned Hours"])
    summary["Remaining Workload"] = 18 - summary["Total Assigned Hours"]

    st.subheader("📊 Lecturer Remaining Workload Summary")
    st.dataframe(summary.sort_values(by="Remaining Workload", ascending=True), use_container_width=True)

else:
    st.info("👈 Please upload both the lecturers and modules datasets to get started.")
