import streamlit as st
import pandas as pd

st.set_page_config(page_title="Workload Management System", layout="wide")
st.title("📚 Automated Workload Management System")

# Upload files
st.sidebar.header("Upload Datasets")
lecturer_file = st.sidebar.file_uploader("Upload Lecturers Dataset", type=["csv", "xlsx"])
module_file = st.sidebar.file_uploader("Upload Modules Dataset", type=["csv", "xlsx"])
room_file = st.sidebar.file_uploader("Upload Room Dataset", type=["csv", "xlsx"])

def split_students(total, min_size=30, max_size=70):
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

    return pd.DataFrame(assignments), lecturer_hours, lecturer_limits

def schedule_rooms(assignments, room_df):
    # Define time slots and durations (2h and 3h)
    slots = [
        ("08:00–10:00", 2), ("10:15–12:15", 2),
        ("14:00–16:00", 2), ("16:15–18:15", 2),
        ("08:00–11:00", 3), ("14:00–17:00", 3)
    ]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Track room usage: room -> day -> slot -> occupied?
    room_usage = {room: {day: {slot[0]: False for slot in slots} for day in weekdays} for room in room_df['Room Name']}

    # Track slot usage globally to ensure only one module per day+slot
    slot_usage = {day: {slot[0]: False for slot in slots} for day in weekdays}

    schedule_output = []

    for _, row in assignments.iterrows():
        module = row['Module Name']
        size = row['Group Size']
        credits = row['Credits']
        group = row['Group Number']
        lecturer = row['Lecturer']
        module_code = row['Module Code']

        needed_sessions = 2
        duration = 3 if credits == 20 else 2
        suitable_slots = [slot for slot in slots if slot[1] == duration]

        sessions_found = 0
        for day in weekdays:
            if sessions_found >= needed_sessions:
                break
            for slot_time, slot_duration in suitable_slots:
                if slot_usage[day][slot_time]:
                    continue
                for room_name in room_df['Room Name']:
                    room_capacity = room_df.loc[room_df['Room Name'] == room_name, 'capacity'].values[0]
                    if room_capacity >= size and not room_usage[room_name][day][slot_time]:
                        room_usage[room_name][day][slot_time] = True
                        slot_usage[day][slot_time] = True
                        info_text = (
                            f"{module_code}\n"
                            f"{module}\n"
                            f"Group {group}\n"
                            f"{lecturer}\n"
                            f"Room: {room_name}\n"
                            f"{size} students"
                        )
                        schedule_output.append({
                            "Day": day,
                            "Time Slot": slot_time,
                            "Details": info_text
                        })
                        sessions_found += 1
                        break
                if sessions_found >= needed_sessions:
                    break

    schedule_df = pd.DataFrame(schedule_output)

    pivot = schedule_df.pivot_table(
        index="Time Slot",
        columns="Day",
        values="Details",
        aggfunc=lambda x: x.iloc[0]
    ).fillna("")

    time_order = [slot[0] for slot in slots]
    pivot = pivot.reindex(time_order)

    return schedule_df, pivot

if lecturer_file and module_file and room_file:
    lecturers_df = pd.read_csv(lecturer_file) if lecturer_file.name.endswith('.csv') else pd.read_excel(lecturer_file)
    modules_df = pd.read_csv(module_file) if module_file.name.endswith('.csv') else pd.read_excel(module_file)
    room_df = pd.read_csv(room_file) if room_file.name.endswith('.csv') else pd.read_excel(room_file)

    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()
    room_df.columns = room_df.columns.str.strip()

    trimester_options = modules_df["When to Take Place"].dropna().unique()
    selected_trimester = st.selectbox("🗕️ Select When to Take Place (Trimester)", sorted(trimester_options))

    # Initialize session state variables
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
        st.session_state.assignments = st.session_state.reassignments_done[selected_trimester]["assignments"]
        st.session_state.lecturer_hours = st.session_state.reassignments_done[selected_trimester]["lecturer_hours"]
        st.session_state.lecturer_limits = st.session_state.reassignments_done[selected_trimester]["lecturer_limits"]
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
        updated_lecturer_hours = st.session_state.lecturer_hours.copy()

        for i, row in st.session_state.assignments.iterrows():
            module_code = row["Module Code"]
            current = row["Lecturer"]
            hours = row["Weekly Hours"]
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
                old = st.session_state.assignments.loc[i, "Lecturer"]
                new = new_lecturers[i]
                hours = st.session_state.assignments.loc[i, "Weekly Hours"]

                if old != "❌ Not Assigned":
                    updated_lecturer_hours[old] -= hours

                if new != "❌ Not Assigned":
                    max_allowed = st.session_state.lecturer_limits.get(new, 18)
                    if updated_lecturer_hours.get(new, 0) + hours <= max_allowed:
                        updated_lecturer_hours[new] = updated_lecturer_hours.get(new, 0) + hours
                        st.session_state.assignments.loc[i, "Lecturer"] = new
                    else:
                        st.warning(f"⚠️ {new} would exceed {max_allowed}h")
                else:
                    st.session_state.assignments.loc[i, "Lecturer"] = "❌ Not Assigned"

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

    # Weekly summary for selected trimester
    all_lecturers = lecturers_df["Teacher's name"].unique()
    final_hours = {name: 0 for name in all_lecturers}
    for _, row in st.session_state.assignments.iterrows():
        if row["Lecturer"] in final_hours:
            final_hours[row["Lecturer"]] += row["Weekly Hours"]

    summary = pd.DataFrame({
        "Lecturer": list(final_hours.keys()),
        "Total Assigned Weekly Hours": list(final_hours.values()),
        "Max Weekly Workload": [st.session_state.lecturer_limits.get(name, 18) for name in final_hours.keys()]
    })
    summary["Remaining Weekly Workload"] = summary["Max Weekly Workload"] - summary["Total Assigned Weekly Hours"]
    summary["Occupancy %"] = (summary["Total Assigned Weekly Hours"] / summary["Max Weekly Workload"] * 100).round(1).astype(str) + " %"

    st.subheader(f"📈 Weekly Workload Summary – Trimester {
