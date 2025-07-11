
import streamlit as st
import pandas as pd
from collections import defaultdict
import random

st.set_page_config(page_title="Workload Management System", layout="wide")
st.title("📚 Automated Workload Management System")

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
    return 7 if credits == 20 else 5 if credits in [10, 15] else 0

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

if lecturer_file and module_file and room_file:
    lecturers_df = pd.read_csv(lecturer_file) if lecturer_file.name.endswith('.csv') else pd.read_excel(lecturer_file)
    modules_df = pd.read_csv(module_file) if module_file.name.endswith('.csv') else pd.read_excel(module_file)
    room_df = pd.read_csv(room_file) if room_file.name.endswith('.csv') else pd.read_excel(room_file)

    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()
    room_df.columns = room_df.columns.str.strip()

    trimester_options = modules_df["When to Take Place"].dropna().unique()
    selected_trimester = st.selectbox("🗕️ Select When to Take Place (Trimester)", sorted(trimester_options))

    if "reassignments_done" not in st.session_state:
        st.session_state.reassignments_done = {}
    if "all_assignments" not in st.session_state:
        st.session_state.all_assignments = pd.DataFrame()
    if "reassignment_applied" not in st.session_state:
        st.session_state.reassignment_applied = False

    if "current_trimester" in st.session_state and st.session_state.current_trimester != selected_trimester:
        st.session_state.reassignment_applied = False
    st.session_state.current_trimester = selected_trimester

    if st.button(f"🔄 Reset Assignments for Trimester {selected_trimester}"):
        if selected_trimester in st.session_state.reassignments_done:
            del st.session_state.reassignments_done[selected_trimester]
        st.session_state.reassignment_applied = False
        st.experimental_rerun()

    if selected_trimester in st.session_state.reassignments_done:
        st.session_state.assignments = st.session_state.reassignments_done[selected_trimester]["assignments"].copy()
        st.session_state.lecturer_hours = st.session_state.reassignments_done[selected_trimester]["lecturer_hours"].copy()
        st.session_state.lecturer_limits = st.session_state.reassignments_done[selected_trimester]["lecturer_limits"].copy()
        st.session_state.reassignment_applied = True
    else:
        result_df, lecturer_hours, lecturer_limits = generate_workload_assignment(lecturers_df, modules_df, selected_trimester)
        st.session_state.assignments = result_df.copy()
        st.session_state.lecturer_hours = lecturer_hours.copy()
        st.session_state.lecturer_limits = lecturer_limits.copy()

        if "Trimester" in st.session_state.all_assignments.columns:
            st.session_state.all_assignments = pd.concat([
                st.session_state.all_assignments[st.session_state.all_assignments["Trimester"] != selected_trimester],
                result_df
            ], ignore_index=True)
        else:
            st.session_state.all_assignments = result_df.copy()

    st.subheader("📊 Current Workload Assignment Results")
    st.dataframe(st.session_state.assignments, use_container_width=True)

    st.subheader(f"📈 Weekly & Trimester Workload Summary – Trimester {selected_trimester}")
    lecturers = lecturers_df["Teacher's name"].unique()
    weekly_teaching = {name: 0 for name in lecturers}
    weekly_grading = {name: 0 for name in lecturers}

    for _, row in st.session_state.assignments.iterrows():
        lec = row["Lecturer"]
        if lec in weekly_teaching:
            weekly_teaching[lec] += row["Weekly Hours"]
            weekly_grading[lec] += row["Grading Hours"]

    admin = lecturers_df.drop_duplicates("Teacher's name").set_index("Teacher's name").get("Administration Hours", pd.Series(0, index=lecturers_df["Teacher's name"])).to_dict()
    planning = lecturers_df.drop_duplicates("Teacher's name").set_index("Teacher's name").get("Planning Hours", pd.Series(0, index=lecturers_df["Teacher's name"])).to_dict()
    research = lecturers_df.drop_duplicates("Teacher's name").set_index("Teacher's name").get("Research Hours", pd.Series(0, index=lecturers_df["Teacher's name"])).to_dict()

    summary = pd.DataFrame({
        "Lecturer": lecturers,
        "Teaching Hours": [weekly_teaching.get(name, 0) for name in lecturers],
        "Grading Hours": [weekly_grading.get(name, 0) for name in lecturers],
        "Administration Hours": [admin.get(name, 0) for name in lecturers],
        "Planning Hours": [planning.get(name, 0) for name in lecturers],
        "Research Hours": [research.get(name, 0) for name in lecturers],
    })

    summary["Weekly Total"] = summary[
        ["Teaching Hours", "Grading Hours", "Administration Hours", "Planning Hours", "Research Hours"]
    ].sum(axis=1)
    summary["Expected Weekly"] = 35
    summary["Remaining Weekly"] = summary["Expected Weekly"] - summary["Weekly Total"]

    summary["Trimester Total"] = summary["Weekly Total"] * 12
    summary["Expected Trimester"] = 420
    summary["Remaining Trimester"] = summary["Expected Trimester"] - summary["Trimester Total"]
    summary["Trimester Occupancy %"] = (summary["Trimester Total"] / 420 * 100).round(1).astype(str) + " %"

    st.dataframe(summary.sort_values(by="Remaining Weekly"), use_container_width=True)

else:
    st.info("📂 Please upload all three datasets to proceed.")
