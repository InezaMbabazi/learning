import streamlit as st
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="Workload Management System", layout="wide")
st.title("📚 Automated Workload Management System")

# Upload files
st.sidebar.header("Upload Datasets")
lecturer_file = st.sidebar.file_uploader("Upload Lecturers Dataset", type=["csv", "xlsx"])
module_file = st.sidebar.file_uploader("Upload Modules Dataset", type=["csv", "xlsx"])
room_file = st.sidebar.file_uploader("Upload Rooms Dataset", type=["csv", "xlsx"])

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
    # Define time slots and durations
    slots = [
        ("08:00–10:00", 2), ("10:15–12:15", 2),
        ("14:00–16:00", 2), ("16:15–18:15", 2),
        ("08:00–11:00", 3), ("14:00–17:00", 3)
    ]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Track room usage: room -> day -> slot -> occupied?
    room_usage = defaultdict(lambda: {day: {slot[0]: False for slot in slots} for day in weekdays})

    schedule_output = []
    for _, row in assignments.iterrows():
        module = row['Module Name']
        size = row['Group Size']
        credits = row['Credits']
        group = row['Group Number']
        lecturer = row['Lecturer']

        needed_sessions = 2
        duration = 3 if credits == 20 else 2
        suitable_slots = [slot for slot in slots if slot[1] == duration]

        days_assigned = []

        for day in weekdays:
            for slot_time, slot_duration in suitable_slots:
                # Find a room that fits and is free
                for _, room in room_df.iterrows():
                    if room['capacity'] >= size and not room_usage[room['Room Name']][day][slot_time]:
                        # Assign this slot and room
                        room_usage[room['Room Name']][day][slot_time] = True
                        days_assigned.append((day, slot_time, room['Room Name']))
                        break
                if len(days_assigned) == needed_sessions:
                    break
            if len(days_assigned) == needed_sessions:
                break

        # Add scheduled sessions info
        for day, time, roomname in days_assigned:
            info_text = (
                f"{row['Module Code']}\n"
                f"{module}\n"
                f"Section {row['Group Number']}\n"
                f"{lecturer}\n"
                f"{roomname}\n"
                f"{size} students"
            )
            schedule_output.append({
                "Day": day,
                "Time Slot": time,
                "Details": info_text
            })

    schedule_df = pd.DataFrame(schedule_output)

    # Pivot table: index = Time Slot, columns = Day, values = Details
    pivot = schedule_df.pivot_table(
        index="Time Slot",
        columns="Day",
        values="Details",
        aggfunc=lambda x: '\n\n'.join(x)
    ).fillna("")

    # Sort time slots in desired order (optional)
    time_order = [slot[0] for slot in slots]
    pivot = pivot.reindex(time_order)

    return schedule_df, pivot

if lecturer_file and module_file and room_file:
    # Load datasets
    lecturers_df = pd.read_csv(lecturer_file) if lecturer_file.name.endswith('.csv') else pd.read_excel(lecturer_file)
    modules_df = pd.read_csv(module_file) if module_file.name.endswith('.csv') else pd.read_excel(module_file)
    room_df = pd.read_csv(room_file) if room_file.name.endswith('.csv') else pd.read_excel(room_file)

    # Strip columns
    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()
    room_df.columns = room_df.columns.str.strip()

    trimester_options = modules_df["When to Take Place"].dropna().unique()
    selected_trimester = st.selectbox("🗕️ Select When to Take Place (Trimester)", sorted(trimester_options))

    # Initialize session state containers
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

        # Update all_assignments with this trimester's results
        if "Trimester" in st.session_state.all_assignments.columns:
            st.session_state.all_assignments = pd.concat([
                st.session_state.all_assignments[st.session_state.all_assignments["Trimester"] != selected_trimester],
                result_df
            ], ignore_index=True)
        else:
            st.session_state.all_assignments = result_df.copy()

    st.subheader("📊 Current Workload Assignment Results")
    st.dataframe(st.session_state.assignments, use_container_width=True)

    # Reassignment interface
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
            # Update all_assignments after reassignment
            st.session_state.all_assignments = pd.concat([
                st.session_state.all_assignments[st.session_state.all_assignments["Trimester"] != selected_trimester],
                st.session_state.assignments
            ], ignore_index=True)
            st.success("✅ Reassignments applied and saved.")

    # Weekly workload summary for selected trimester
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

    st.subheader(f"📈 Weekly Workload Summary – Trimester {selected_trimester}")
    st.dataframe(summary.sort_values(by="Remaining Weekly Workload"), use_container_width=True)

    # Cumulative workload button and display
    if st.button("📊 Generate Cumulative Workload Statistics"):
        cumulative = st.session_state.all_assignments.groupby(["Lecturer", "Trimester"])["Weekly Hours"].sum().unstack()
        cumulative = cumulative.reindex(index=all_lecturers, fill_value=0).fillna(0)
        cumulative = cumulative * 12  # Assuming 12 weeks per trimester
        cumulative["Total"] = cumulative.sum(axis=1)
        cumulative["Max Workload (Annual)"] = cumulative.index.map(lambda x: st.session_state.lecturer_limits.get(x, 18) * 12 * 3)
        cumulative["Occupancy %"] = (cumulative["Total"] / cumulative["Max Workload (Annual)"] * 100).round(1).astype(str) + " %"

        st.subheader("📊 Cumulative Lecturer Workload (Trimester 1, 2, 3, Total, Occupancy)")
        st.dataframe(cumulative, use_container_width=True)

    # Generate and display weekly timetable with rooms
    schedule_df, pivot_timetable = schedule_rooms(st.session_state.assignments, room_df)
    st.subheader("📅 Weekly Timetable by Room Allocation")
    st.write(
        pivot_timetable.style
        .set_properties(**{'white-space': 'pre-wrap', 'text-align': 'left'})
        .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
    )

    # Download CSV
    csv = st.session_state.assignments.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Assignment CSV", csv, "workload_assignment.csv", "text/csv")

else:
    st.info("📈 Please upload all three datasets: lecturers, modules, and rooms.")
import streamlit as st
import pandas as pd
import itertools
from collections import defaultdict

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
    slots = [
        ("08:00–10:00", 2), ("10:15–12:15", 2),
        ("14:00–16:00", 2), ("16:15–18:15", 2),
        ("08:00–11:00", 3), ("14:00–17:00", 3)
    ]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    timetable = {day: {slot[0]: None for slot in slots} for day in weekdays}
    room_usage = defaultdict(lambda: {day: {slot[0]: False for slot in slots} for day in weekdays})

    schedule_output = []
    for _, row in assignments.iterrows():
        module = row['Module Name']
        size = row['Group Size']
        credits = row['Credits']
        group = row['Group Number']

        needed = 2  # 2 sessions
        duration = 3 if credits == 20 else 2
        suitable_slots = [slot for slot in slots if slot[1] == duration]

        days_assigned = []

        for day in weekdays:
            for slot_time, slot_duration in suitable_slots:
                for _, room in room_df.iterrows():
                    if room['capacity'] >= size and not room_usage[room['Room Name']][day][slot_time]:
                        room_usage[room['Room Name']][day][slot_time] = True
                        days_assigned.append((day, slot_time, room['Room Name']))
                        break
                if len(days_assigned) == needed:
                    break
            if len(days_assigned) == needed:
                break

        for day, time, roomname in days_assigned:
            key = f"{day} | {time}"
            schedule_output.append({
                "Day": day,
                "Time": time,
                "Module": module,
                "Group": f"Group {group}",
                "Room": roomname,
                "Size": size
            })

    schedule_df = pd.DataFrame(schedule_output)
    pivot = schedule_df.pivot_table(index="Time", columns="Day", values=["Module", "Group", "Room"], aggfunc=lambda x: '\n'.join(x)).fillna("")
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

    result_df, lecturer_hours, lecturer_limits = generate_workload_assignment(lecturers_df, modules_df, selected_trimester)

    st.subheader("📊 Current Workload Assignment Results")
    st.dataframe(result_df)

    st.subheader("📊 Weekly Timetable by Room Allocation")
    schedule_df, pivot_timetable = schedule_rooms(result_df, room_df)
    st.dataframe(pivot_timetable)

else:
    st.info("📈 Please upload all three datasets: lecturers, modules, and rooms.")

