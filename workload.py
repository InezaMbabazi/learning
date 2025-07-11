# Your original imports and setup
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

# Helper functions
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

# Add grading, planning, research, admin columns
def calculate_extra_hours(row):
    grading = round(row["Group Size"] * 0.08, 2)
    return pd.Series({
        "Grading Hours": grading,
        "Planning Hours": 2,
        "Research Hours": 3,
        "Admin Hours": 2
    })

# Main logic
if lecturer_file and module_file and room_file:
    lecturers_df = pd.read_csv(lecturer_file) if lecturer_file.name.endswith(".csv") else pd.read_excel(lecturer_file)
    modules_df = pd.read_csv(module_file) if module_file.name.endswith(".csv") else pd.read_excel(module_file)
    room_df = pd.read_csv(room_file) if room_file.name.endswith(".csv") else pd.read_excel(room_file)

    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()
    room_df.columns = room_df.columns.str.strip()

    trimester_options = modules_df["When to Take Place"].dropna().unique()
    selected_trimester = st.selectbox("🗕️ Select When to Take Place (Trimester)", sorted(trimester_options))

    assignments = []
    lecturer_hours = defaultdict(float)
    lecturer_limits = lecturers_df.drop_duplicates(subset=["Teacher's name"]).set_index("Teacher's name")["Weekly Workload"].to_dict()

    filtered_modules = modules_df[modules_df["When to Take Place"] == selected_trimester].copy()
    filtered_modules["Weekly Hours"] = filtered_modules["Credits"].apply(get_weekly_hours)

    for _, mod in filtered_modules.iterrows():
        group_sizes = split_students(mod["Number of Students"])
        for group_index, size in enumerate(group_sizes):
            matched_lecturers = lecturers_df[lecturers_df["Module Code"] == mod["Code"]]
            for name in matched_lecturers["Teacher's name"].unique():
                if lecturer_hours[name] + mod["Weekly Hours"] <= lecturer_limits.get(name, 18):
                    base = {
                        "Lecturer": name,
                        "Module Code": mod["Code"],
                        "Module Name": mod["Module Name"],
                        "Credits": mod["Credits"],
                        "Cohort": mod["Cohort"],
                        "Programme": mod["Programme"],
                        "Weekly Hours": mod["Weekly Hours"],
                        "Group Size": size,
                        "Group Number": group_index + 1,
                        "Trimester": selected_trimester
                    }
                    base.update(calculate_extra_hours({"Group Size": size}))
                    assignments.append(base)
                    lecturer_hours[name] += mod["Weekly Hours"]
                    break
            else:
                # Not assigned
                base = {
                    "Lecturer": "❌ Not Assigned",
                    "Module Code": mod["Code"],
                    "Module Name": mod["Module Name"],
                    "Credits": mod["Credits"],
                    "Cohort": mod["Cohort"],
                    "Programme": mod["Programme"],
                    "Weekly Hours": mod["Weekly Hours"],
                    "Group Size": size,
                    "Group Number": group_index + 1,
                    "Trimester": selected_trimester
                }
                base.update(calculate_extra_hours({"Group Size": size}))
                assignments.append(base)

    assignments_df = pd.DataFrame(assignments)
    st.subheader("📊 Current Workload Assignment Results")
    st.dataframe(assignments_df, use_container_width=True)

    # Weekly Workload Summary
    st.subheader(f"📈 Weekly Workload Summary – Trimester {selected_trimester}")
    summary_df = assignments_df.groupby("Lecturer")[["Weekly Hours", "Grading Hours", "Planning Hours", "Research Hours", "Admin Hours"]].sum().reset_index()
    summary_df["Total Weekly Extra Time"] = summary_df[["Grading Hours", "Planning Hours", "Research Hours", "Admin Hours"]].sum(axis=1)
    summary_df["Extra Time (Trimester)"] = summary_df["Total Weekly Extra Time"] * 12
    summary_df["Teaching Time (Trimester)"] = summary_df["Weekly Hours"] * 12
    summary_df["Total (Trimester)"] = summary_df["Teaching Time (Trimester)"] + summary_df["Extra Time (Trimester)"]
    summary_df["Max Trimester Time"] = summary_df["Lecturer"].map(lambda x: lecturer_limits.get(x, 18) * 12)
    summary_df["Occupancy %"] = (summary_df["Total (Trimester)"] / summary_df["Max Trimester Time"] * 100).round(1).astype(str) + " %"

    st.dataframe(summary_df, use_container_width=True)

    # Cumulative Workload Summary
    if st.button("📊 Generate Cumulative Workload Statistics"):
        cumulative = assignments_df.groupby(["Lecturer", "Trimester"])[["Weekly Hours", "Grading Hours", "Planning Hours", "Research Hours", "Admin Hours"]].sum()
        cumulative = cumulative.groupby("Lecturer").sum()
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
