import streamlit as st
import pandas as pd
from collections import defaultdict
import random

st.set_page_config(page_title="Workload Management System", layout="wide")
st.title("📚 Automated Workload Management System")

# Upload files
st.sidebar.header("Upload Datasets")
lecturer_file = st.sidebar.file_uploader("Upload Lecturers Dataset", type=["csv", "xlsx"])
module_file = st.sidebar.file_uploader("Upload Modules Dataset", type=["csv", "xlsx"])
room_file = st.sidebar.file_uploader("Upload Room Dataset", type=["csv", "xlsx"])

def split_students(total, min_size=30, max_size=50):
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
    if valid_splits:
        valid_splits.sort(key=lambda g: (len(g), max(g) - min(g)))
        return valid_splits[0]
    return [total]

def get_weekly_hours(credits):
    if credits == 20:
        return 7
    elif credits in [10, 15]:
        return 5
    else:
        return 0

def generate_workload_assignment(lecturers_df, modules_df, selected_trimester):
    lecturer_hours = {}
    assignments = []

    lecturer_limits_df = lecturers_df.drop_duplicates(subset=["Teacher's name"])[["Teacher's name", "Weekly Workload"]]
    lecturer_limits_df = lecturer_limits_df.set_index("Teacher's name")
    lecturer_limits = lecturer_limits_df["Weekly Workload"].to_dict()

    filtered_modules = modules_df[modules_df["When to Take Place"] == selected_trimester].copy()
    filtered_modules["Weekly Hours"] = filtered_modules["Credits"].apply(get_weekly_hours)

    for _, module in filtered_modules.iterrows():
        module_code = module["Code"]
        total_students = int(module["Number of Students"])
        hours_needed = module["Weekly Hours"]
        group_sizes = split_students(total_students)

        for group_index, group_size in enumerate(group_sizes):
            matching_lecturers = lecturers_df[lecturers_df["Module Code"] == module_code].copy()
            for name in matching_lecturers["Teacher's name"].unique():
                if name not in lecturer_hours:
                    lecturer_hours[name] = 0

            matching_lecturers["Assigned Hours"] = matching_lecturers["Teacher's name"].map(lecturer_hours)
            matching_lecturers["Max Workload"] = matching_lecturers["Teacher's name"].map(lecturer_limits)
            matching_lecturers["Remaining"] = matching_lecturers["Max Workload"] - matching_lecturers["Assigned Hours"]
            matching_lecturers = matching_lecturers.sort_values(by="Remaining", ascending=False)

            assigned = False
            for _, lecturer in matching_lecturers.iterrows():
                name = lecturer["Teacher's name"]
                max_allowed = lecturer_limits.get(name, 18)
                if lecturer_hours[name] + hours_needed <= max_allowed:
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
                        "Trimester": selected_trimester,
                        "Grading Hours": round(group_size * 0.08, 2)
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
                    "Trimester": selected_trimester,
                    "Grading Hours": round(group_size * 0.08, 2)
                })

    return pd.DataFrame(assignments), lecturer_hours, lecturer_limits

# Room scheduling and all other previous unchanged code...
# (Leave your `schedule_rooms()` and Streamlit interface untouched)

# === AFTER st.session_state.assignments is ready ===
    st.subheader("📊 Current Workload Assignment Results")
    st.dataframe(st.session_state.assignments, use_container_width=True)

# === NEW Weekly Summary ===
    all_lecturers = lecturers_df["Teacher's name"].unique()
    final_teaching = {name: 0 for name in all_lecturers}
    final_grading = {name: 0 for name in all_lecturers}

    for _, row in st.session_state.assignments.iterrows():
        lecturer = row["Lecturer"]
        if lecturer in final_teaching:
            final_teaching[lecturer] += row["Weekly Hours"]
            final_grading[lecturer] += row["Grading Hours"]

    # Get admin/planning/research from lecturer file
    admin_hours = lecturers_df.drop_duplicates("Teacher's name").set_index("Teacher's name")["Administration Hours"].to_dict()
    planning_hours = lecturers_df.drop_duplicates("Teacher's name").set_index("Teacher's name")["Planning Hours"].to_dict()
    research_hours = lecturers_df.drop_duplicates("Teacher's name").set_index("Teacher's name")["Research Hours"].to_dict()

    summary = pd.DataFrame({
        "Lecturer": list(final_teaching.keys()),
        "Teaching Hours": list(final_teaching.values()),
        "Grading Hours": [final_grading.get(name, 0) for name in final_teaching.keys()],
        "Administration Hours": [admin_hours.get(name, 0) for name in final_teaching.keys()],
        "Planning Hours": [planning_hours.get(name, 0) for name in final_teaching.keys()],
        "Research Hours": [research_hours.get(name, 0) for name in final_teaching.keys()]
    })

    summary["Total Workload"] = summary[
        ["Teaching Hours", "Grading Hours", "Administration Hours", "Planning Hours", "Research Hours"]
    ].sum(axis=1)

    summary["Expected Weekly Workload"] = 35
    summary["Remaining Workload"] = summary["Expected Weekly Workload"] - summary["Total Workload"]
    summary["Occupancy %"] = (summary["Total Workload"] / 35 * 100).round(1).astype(str) + " %"

    st.subheader(f"📈 Expanded Weekly Workload Summary – Trimester {selected_trimester}")
    st.dataframe(summary.sort_values(by="Remaining Workload"), use_container_width=True)

# === UPDATED CUMULATIVE SECTION ===
    if st.button("📊 Generate Cumulative Workload Statistics"):
        weekly_teaching = st.session_state.all_assignments.groupby(["Lecturer", "Trimester"])["Weekly Hours"].sum().unstack(fill_value=0) * 12
        grading_teaching = st.session_state.all_assignments.groupby(["Lecturer", "Trimester"])["Grading Hours"].sum().unstack(fill_value=0) * 12

        cumulative = weekly_teaching.add(grading_teaching, fill_value=0)

        # Add Admin, Planning, Research × 3 trimesters
        cumulative["Admin"] = cumulative.index.map(lambda x: admin_hours.get(x, 0) * 12 * 3)
        cumulative["Planning"] = cumulative.index.map(lambda x: planning_hours.get(x, 0) * 12 * 3)
        cumulative["Research"] = cumulative.index.map(lambda x: research_hours.get(x, 0) * 12 * 3)

        cumulative["Total"] = cumulative.sum(axis=1)
        cumulative["Max Workload (Annual)"] = 35 * 12 * 3
        cumulative["Occupancy %"] = (cumulative["Total"] / cumulative["Max Workload (Annual)"] * 100).round(1).astype(str) + " %"

        st.subheader("📊 Cumulative Lecturer Workload (All Trimester + Grading + Admin)")
        st.dataframe(cumulative, use_container_width=True)
