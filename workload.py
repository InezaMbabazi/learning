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
            grading = round(group_size * 0.08, 2)
            planning = 2
            research = 3
            admin = 2

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
                        "Grading Hours": grading,
                        "Planning Hours": planning,
                        "Research Hours": research,
                        "Admin Hours": admin
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
                    "Grading Hours": grading,
                    "Planning Hours": planning,
                    "Research Hours": research,
                    "Admin Hours": admin
                })

    return pd.DataFrame(assignments), lecturer_hours, lecturer_limits

# Main app logic
if lecturer_file and module_file and room_file:
    lecturers_df = pd.read_csv(lecturer_file) if lecturer_file.name.endswith('.csv') else pd.read_excel(lecturer_file)
    modules_df = pd.read_csv(module_file) if module_file.name.endswith('.csv') else pd.read_excel(module_file)
    room_df = pd.read_csv(room_file) if room_file.name.endswith('.csv') else pd.read_excel(room_file)

    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()
    room_df.columns = room_df.columns.str.strip()

    trimester_options = modules_df["When to Take Place"].dropna().unique()
    selected_trimester = st.selectbox("🗕️ Select When to Take Place (Trimester)", sorted(trimester_options))

    assignments_df, lecturer_hours, lecturer_limits = generate_workload_assignment(lecturers_df, modules_df, selected_trimester)

    st.subheader("📊 Current Workload Assignment Results")
    st.dataframe(assignments_df, use_container_width=True)

    st.subheader(f"📈 Weekly Workload Summary – Trimester {selected_trimester}")
    summary_df = assignments_df[assignments_df["Lecturer"] != "❌ Not Assigned"]
    summary = summary_df.groupby("Lecturer")[["Weekly Hours", "Grading Hours", "Planning Hours", "Research Hours", "Admin Hours"]].sum().reset_index()
    summary["Extra Time (Weekly)"] = summary[["Grading Hours", "Planning Hours", "Research Hours", "Admin Hours"]].sum(axis=1)
    summary["Extra Time (Trimester)"] = summary["Extra Time (Weekly)"] * 12
    summary["Teaching Time (Trimester)"] = summary["Weekly Hours"] * 12
    summary["Total Time (Trimester)"] = summary["Teaching Time (Trimester)"] + summary["Extra Time (Trimester)"]
    summary["Max Time (Trimester)"] = summary["Lecturer"].map(lambda x: lecturer_limits.get(x, 18) * 12)
    summary["Occupancy %"] = (summary["Total Time (Trimester)"] / summary["Max Time (Trimester)"] * 100).round(1).astype(str) + " %"
    st.dataframe(summary, use_container_width=True)

    if st.button("📊 Generate Cumulative Workload Statistics"):
        cumulative = assignments_df[assignments_df["Lecturer"] != "❌ Not Assigned"]
        cumulative = cumulative.groupby("Lecturer")[["Weekly Hours", "Grading Hours", "Planning Hours", "Research Hours", "Admin Hours"]].sum()
        cumulative["Teaching Time (Year)"] = cumulative["Weekly Hours"] * 12 * 3
        cumulative["Extra Time (Year)"] = (cumulative["Grading Hours"] + cumulative["Planning Hours"] + cumulative["Research Hours"] + cumulative["Admin Hours"]) * 12 * 3
        cumulative["Total Time (Year)"] = cumulative["Teaching Time (Year)"] + cumulative["Extra Time (Year)"]
        cumulative["Max Annual Workload"] = cumulative.index.map(lambda x: lecturer_limits.get(x, 18) * 12 * 3)
        cumulative["Occupancy %"] = (cumulative["Total Time (Year)"] / cumulative["Max Annual Workload"] * 100).round(1).astype(str) + " %"
        st.subheader("📊 Cumulative Lecturer Workload")
        st.dataframe(cumulative[[
            "Teaching Time (Year)",
            "Extra Time (Year)",
            "Total Time (Year)",
            "Max Annual Workload",
            "Occupancy %"
        ]], use_container_width=True)

else:
    st.info("Please upload all three datasets to proceed.")
