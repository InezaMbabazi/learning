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

# ------- Utility functions (same as before) -------
# [split_students, get_weekly_hours, generate_workload_assignment, schedule_rooms] stay unchanged

# ------- Load and Prepare Data -------
if lecturer_file and module_file and room_file:
    lecturers_df = pd.read_csv(lecturer_file) if lecturer_file.name.endswith(".csv") else pd.read_excel(lecturer_file)
    modules_df = pd.read_csv(module_file) if module_file.name.endswith(".csv") else pd.read_excel(module_file)
    room_df = pd.read_csv(room_file) if room_file.name.endswith(".csv") else pd.read_excel(room_file)

    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()
    room_df.columns = room_df.columns.str.strip()

    trimester_options = modules_df["When to Take Place"].dropna().unique()
    selected_trimester = st.selectbox("🗕️ Select When to Take Place (Trimester)", sorted(trimester_options))

    if "assignments_by_trimester" not in st.session_state:
        st.session_state.assignments_by_trimester = {}

    if selected_trimester not in st.session_state.assignments_by_trimester:
        result_df, lecturer_hours, lecturer_limits = generate_workload_assignment(lecturers_df, modules_df, selected_trimester)
        st.session_state.assignments_by_trimester[selected_trimester] = {
            "assignments": result_df.copy(),
            "lecturer_hours": lecturer_hours,
            "lecturer_limits": lecturer_limits
        }

    assignments = st.session_state.assignments_by_trimester[selected_trimester]["assignments"]
    lecturer_limits = st.session_state.assignments_by_trimester[selected_trimester]["lecturer_limits"]

    st.subheader("📊 Current Workload Assignment Results")
    st.dataframe(assignments, use_container_width=True)

    # ------- Manual Reassignments -------
    st.subheader("✏️ Reassign Lecturers")
    updated_lecturers = []
    for i, row in assignments.iterrows():
        module_code = row["Module Code"]
        current_lecturer = row["Lecturer"]
        eligible = lecturers_df[lecturers_df["Module Code"] == module_code]["Teacher's name"].unique().tolist()
        if current_lecturer not in eligible and current_lecturer != "❌ Not Assigned":
            eligible.append(current_lecturer)
        options = ["❌ Not Assigned"] + sorted(eligible)
        new_lecturer = st.selectbox(f"{row['Module Name']} (Group {row['Group Number']})", options, index=options.index(current_lecturer), key=f"reassign_{i}")
        updated_lecturers.append(new_lecturer)

    if st.button("🔁 Apply Reassignments"):
        for i in range(len(assignments)):
            assignments.loc[i, "Lecturer"] = updated_lecturers[i]

        lecturer_hours_updated = {name: 0 for name in lecturers_df["Teacher's name"].unique()}
        for _, row in assignments.iterrows():
            if row["Lecturer"] != "❌ Not Assigned":
                lecturer_hours_updated[row["Lecturer"]] += row["Weekly Hours"]

        st.session_state.assignments_by_trimester[selected_trimester] = {
            "assignments": assignments.copy(),
            "lecturer_hours": lecturer_hours_updated,
            "lecturer_limits": lecturer_limits
        }
        st.success("✅ Reassignments applied.")

    # ------- Summary -------
    st.subheader(f"📈 Weekly Workload Summary – Trimester {selected_trimester}")
    lecturers = lecturers_df["Teacher's name"].unique()
    hours_summary = {name: 0 for name in lecturers}
    for _, row in assignments.iterrows():
        if row["Lecturer"] in hours_summary:
            hours_summary[row["Lecturer"]] += row["Weekly Hours"]
    summary_df = pd.DataFrame({
        "Lecturer": list(hours_summary.keys()),
        "Assigned Hours": list(hours_summary.values()),
        "Max Hours": [lecturer_limits.get(name, 18) for name in hours_summary.keys()]
    })
    summary_df["Remaining"] = summary_df["Max Hours"] - summary_df["Assigned Hours"]
    summary_df["Occupancy %"] = (summary_df["Assigned Hours"] / summary_df["Max Hours"] * 100).round(1).astype(str) + "%"
    st.dataframe(summary_df, use_container_width=True)

    # ------- Timetable and Room Usage -------
    timetable_df, unassigned_modules, room_summary_df = schedule_rooms(assignments, room_df)
    st.subheader("🏫 Weekly Room Timetable")
    st.dataframe(timetable_df, use_container_width=True)

    if unassigned_modules:
        st.subheader("⚠️ Unscheduled Sessions")
        st.dataframe(pd.DataFrame(unassigned_modules))

    st.subheader("🏫 Room Usage Summary")
    st.dataframe(room_summary_df, use_container_width=True)

    # ------- Cumulative Summary Across All Trimesters -------
    if st.button("📊 Generate Cumulative Workload Summary"):
        combined = pd.concat([info["assignments"] for info in st.session_state.assignments_by_trimester.values()], ignore_index=True)
        cumulative = combined.groupby(["Lecturer", "Trimester"])["Weekly Hours"].sum().unstack(fill_value=0)
        cumulative = cumulative * 12  # assuming 12 weeks
        cumulative["Total"] = cumulative.sum(axis=1)
        cumulative["Max Annual Workload"] = cumulative.index.map(lambda x: lecturer_limits.get(x, 18) * 12 * 3)
        cumulative["Occupancy %"] = (cumulative["Total"] / cumulative["Max Annual Workload"] * 100).round(1).astype(str) + "%"
        st.subheader("📊 Cumulative Workload Summary")
        st.dataframe(cumulative, use_container_width=True)

else:
    st.info("📥 Please upload all required datasets to begin.")
