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
def schedule_rooms(assignments, room_df):
    slots = ["08:00–10:00", "10:30–12:30", "14:00–16:00", "16:15–18:15"]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    schedule = {(slot, day): [] for slot in slots for day in weekdays}
    room_usage = defaultdict(lambda: {(slot, day): False for slot in slots for day in weekdays})
    used_slots = defaultdict(list)
    unassigned_modules = []

    assigned = assignments[assignments["Lecturer"] != "❌ Not Assigned"].copy()

    lecturer_sessions_scheduled = defaultdict(int)
    lecturer_sessions_required = defaultdict(int)

    for _, row in assigned.iterrows():
        key_id = f"{row['Module Code']}_G{row['Group Number']}"

        credits = row["Credits"]
        if credits == 20:
            sessions_required = 3
        elif credits in [10, 15]:
            sessions_required = 2
        else:
            sessions_required = 1

        sessions_scheduled = 0
        available_slots = [(slot, day) for day in weekdays for slot in slots]
        random.shuffle(available_slots)

        lecturer_sessions_required[row["Lecturer"]] += sessions_required

        for slot, day in available_slots:
            if (slot, day) in used_slots[key_id]:
                continue

            for _, room in room_df.iterrows():
                if row['Group Size'] <= room['capacity'] and not room_usage[room['Room Name']][(slot, day)]:
                    entry = f"{row['Module Name']}\nGroup {row['Group Number']}\n{room['Room Name']}\n{row['Lecturer']}\n{row['Group Size']} students"
                    schedule[(slot, day)].append(entry)
                    room_usage[room['Room Name']][(slot, day)] = True
                    used_slots[key_id].append((slot, day))
                    sessions_scheduled += 1
                    lecturer_sessions_scheduled[row["Lecturer"]] += 1
                    break
            if sessions_scheduled >= sessions_required:
                break

        if sessions_scheduled < sessions_required:
            unassigned_modules.append({
                "Module": row["Module Name"],
                "Group": row["Group Number"],
                "Lecturer": row["Lecturer"],
                "Students": row["Group Size"],
                "Sessions Scheduled": sessions_scheduled,
                "Sessions Required": sessions_required,
                "Missing Sessions": sessions_required - sessions_scheduled
            })

    timetable_df = pd.DataFrame(index=slots, columns=weekdays)
    for (slot, day), entries in schedule.items():
        timetable_df.loc[slot, day] = "\n\n".join(entries) if entries else ""

    room_summary = []
    for room, usage in room_usage.items():
        used_count = sum(1 for v in usage.values() if v)
        room_summary.append({
            "Room": room,
            "Capacity": room_df.loc[room_df['Room Name'] == room, 'capacity'].values[0],
            "Slots Used": used_count,
            "Total Slots": len(slots) * len(weekdays)
        })
    room_summary_df = pd.DataFrame(room_summary)
    room_summary_df["Usage %"] = (room_summary_df["Slots Used"] / room_summary_df["Total Slots"] * 100).round(1).astype(str) + "%"

    lecturers_with_missing_sessions = []
    for lecturer, required in lecturer_sessions_required.items():
        scheduled = lecturer_sessions_scheduled.get(lecturer, 0)
        if scheduled < required:
            lecturers_with_missing_sessions.append({
                "Lecturer": lecturer,
                "Sessions Required": required,
                "Sessions Scheduled": scheduled,
                "Sessions Missing": required - scheduled
            })
    lecturer_sessions_report_df = pd.DataFrame(lecturers_with_missing_sessions)

    return timetable_df, unassigned_modules, room_summary_df, lecturer_sessions_report_df
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

    show_reassign = st.checkbox("✏️ Show Reassign Lecturers (Optional)")
    if show_reassign:
        st.subheader("✏️ Reassign Lecturers")
        new_lecturers = []

        for i, row in st.session_state.assignments.iterrows():
            module_code = row["Module Code"]
            current = row["Lecturer"]
            label = f"{row['Module Name']} (Group {row['Group Number']})"

            eligible = lecturers_df[lecturers_df["Module Code"] == module_code]["Teacher's name"].unique().tolist()
            if current not in eligible and current != "❌ Not Assigned":
                eligible.append(current)

            options = ["❌ Not Assigned"] + sorted(eligible)
            selected = st.selectbox(
                f"➡️ {label} | Current: {current}",
                options=options,
                index=options.index(current) if current in options else 0,
                key=f"reassign_{i}"
            )
            new_lecturers.append(selected)

        if st.button("🔁 Apply Reassignments"):
            for i in range(len(st.session_state.assignments)):
                st.session_state.assignments.loc[i, "Lecturer"] = new_lecturers[i]

            updated_lecturer_hours = {}
            for name in st.session_state.lecturer_limits.keys():
                updated_lecturer_hours[name] = 0
            for _, row in st.session_state.assignments.iterrows():
                lecturer = row["Lecturer"]
                if lecturer != "❌ Not Assigned":
                    updated_lecturer_hours[lecturer] = updated_lecturer_hours.get(lecturer, 0) + row["Weekly Hours"]
            st.session_state.lecturer_hours = updated_lecturer_hours.copy()

            st.session_state.reassignments_done[selected_trimester] = {
                "assignments": st.session_state.assignments.copy(),
                "lecturer_hours": updated_lecturer_hours.copy(),
                "lecturer_limits": st.session_state.lecturer_limits.copy()
            }

            st.session_state.all_assignments = pd.concat([
                st.session_state.all_assignments[st.session_state.all_assignments["Trimester"] != selected_trimester],
                st.session_state.assignments
            ], ignore_index=True)

            st.success("✅ Reassignments applied and saved.")

    all_lecturers = lecturers_df["Teacher's name"].unique()
    final_teaching = {name: 0 for name in all_lecturers}
    final_grading = {name: 0 for name in all_lecturers}
    for _, row in st.session_state.assignments.iterrows():
        if row["Lecturer"] in final_teaching:
            final_teaching[row["Lecturer"]] += row["Weekly Hours"]
            final_grading[row["Lecturer"]] += row["Grading Hours"]

    admin = lecturers_df.drop_duplicates("Teacher's name").set_index("Teacher's name")["Administration Hours"].to_dict()
    planning = lecturers_df.drop_duplicates("Teacher's name").set_index("Teacher's name")["Planning Hours"].to_dict()
    research = lecturers_df.drop_duplicates("Teacher's name").set_index("Teacher's name")["Research Hours"].to_dict()

    summary = pd.DataFrame({
        "Lecturer": list(final_teaching.keys()),
        "Teaching Hours": list(final_teaching.values()),
        "Grading Hours": list(final_grading.values()),
        "Administration Hours": [admin.get(name, 0) for name in final_teaching.keys()],
        "Planning Hours": [planning.get(name, 0) for name in final_teaching.keys()],
        "Research Hours": [research.get(name, 0) for name in final_teaching.keys()]
    })

    summary["Total Weekly Hours"] = summary[["Teaching Hours", "Grading Hours", "Administration Hours", "Planning Hours", "Research Hours"]].sum(axis=1)
    summary["Expected Weekly Load"] = 35
    summary["Weekly Occupancy %"] = (summary["Total Weekly Hours"] / summary["Expected Weekly Load"] * 100).round(1).astype(str) + " %"
    summary["Trimester Total"] = summary["Total Weekly Hours"] * 12
    summary = summary.sort_values(by="Total Weekly Hours", ascending=False)

    st.subheader(f"📈 Weekly Workload Summary – Trimester {selected_trimester}")
    st.dataframe(summary, use_container_width=True)
 if st.button("📊 Generate Cumulative Workload Statistics"):
    cumulative_weekly = st.session_state.all_assignments.groupby(["Lecturer", "Trimester"])["Weekly Hours"].sum().unstack(fill_value=0)
    
    # Calculate trimester total hours per trimester (weekly hours * 12)
    cumulative_trimester = cumulative_weekly * 12

    # Reindex to keep all lecturers
    cumulative_trimester = cumulative_trimester.reindex(index=all_lecturers, fill_value=0)
    
    # Add total trimester hours sum
    cumulative_trimester["Total"] = cumulative_trimester.sum(axis=1)

    # Expected hours per trimester (35 * 12 weeks)
    expected_trimester_load = 35 * 12

    # Calculate occupancy % per trimester column
    for col in cumulative_trimester.columns[:-1]:  # all trimester cols except 'Total'
        cumulative_trimester[col + " Occupancy %"] = (cumulative_trimester[col] / expected_trimester_load * 100).round(1).astype(str) + " %"

    # Overall occupancy based on total
    cumulative_trimester["Expected Total"] = expected_trimester_load * len(trimester_options)
    cumulative_trimester["Total Occupancy %"] = (cumulative_trimester["Total"] / cumulative_trimester["Expected Total"] * 100).round(1).astype(str) + " %"

    st.subheader("📊 Cumulative Lecturer Workload with Expected Trimester Load and Occupancy")
    st.dataframe(cumulative_trimester, use_container_width=True)


    # Room scheduling and timetable
    timetable_df, unassigned_modules, room_summary_df, lecturer_sessions_report_df = schedule_rooms(st.session_state.assignments, room_df)

    st.subheader("🏫 Weekly Room Timetable")
    st.dataframe(timetable_df, use_container_width=True)

    if unassigned_modules:
        st.warning(f"⚠️ Some modules/groups could not be fully scheduled due to room constraints:")
        for item in unassigned_modules:
            st.write(f"Module: {item['Module']}, Group: {item['Group']}, Lecturer: {item['Lecturer']}, Students: {item['Students']}, Sessions Scheduled: {item['Sessions Scheduled']}, Sessions Required: {item['Sessions Required']}")

    st.subheader("🏫 Room Usage Summary")
    st.dataframe(room_summary_df, use_container_width=True)

    st.subheader("📝 Lecturer Session Scheduling Report")
    if lecturer_sessions_report_df.empty:
        st.success("All lecturers have their required sessions scheduled.")
    else:
        st.warning("Some lecturers have fewer scheduled sessions than required (2 sessions per module group):")
    st.dataframe(
        lecturer_sessions_report_df if not lecturer_sessions_report_df.empty
        else pd.DataFrame(columns=["Lecturer", "Sessions Required", "Sessions Scheduled", "Sessions Missing"]),
        use_container_width=True
    )

else:
    st.info("Please upload all three datasets to proceed.")

