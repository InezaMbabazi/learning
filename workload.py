import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Workload Management System", layout="wide")

st.title("📚 Automated Workload Management System")

# Upload datasets
st.sidebar.header("Upload Datasets")
lecturer_file = st.sidebar.file_uploader("Upload Lecturers Dataset", type=["csv", "xlsx"])
module_file = st.sidebar.file_uploader("Upload Modules Dataset", type=["csv", "xlsx"])

# FINAL SPLITTING FUNCTION
def split_students(total, min_size=30, max_size=70):
    """
    Split total students into the **minimum number of groups** between min_size and max_size,
    making group sizes as balanced as possible.
    """
    if total <= max_size:
        return [total]

    valid_splits = []

    for group_count in range(1, total + 1):
        base = total // group_count
        remainder = total % group_count

        if base > max_size or base < min_size:
            continue

        group_sizes = [base + 1 if i < remainder else base for i in range(group_count)]

        if all(min_size <= g <= max_size for g in group_sizes):
            valid_splits.append(group_sizes)

    # Return the one with the fewest groups (and most balanced if tie)
    if valid_splits:
        valid_splits.sort(key=lambda g: (len(g), max(g) - min(g)))
        return valid_splits[0]

    # Fallback
    return [total]

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

    # Reset tracking of hours assigned
    lecturer_hours = {}

    assignments = []

    for _, module in filtered_modules.iterrows():
        module_code = module["Code"]
        total_students = int(module["Number of Students"])
        hours_needed = module["Weekly Hours"]
        group_sizes = split_students(total_students)

        for group_index, group_size in enumerate(group_sizes):
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
