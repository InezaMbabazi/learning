import streamlit as st
import pandas as pd
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
        "08:00–10:00", "10:30–12:30", "14:00–16:00", "16:15–18:15"
    ]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    timetable = {day: {slot: None for slot in slots} for day in weekdays}
    room_usage = defaultdict(lambda: {day: {slot: False for slot in slots} for day in weekdays})

    schedule_output = []
    current_index = 0
    for _, row in assignments.iterrows():
        module = row['Module Name']
        size = row['Group Size']
        group = row['Group Number']
        lecturer = row['Lecturer']

        assigned = False
        for day in weekdays:
            for slot in slots:
                for _, room in room_df.iterrows():
                    if room['capacity'] >= size and not room_usage[room['Room Name']][day][slot]:
                        room_usage[room['Room Name']][day][slot] = True
                        schedule_output.append({
                            "Day": day,
                            "Time": slot,
                            "Module": module,
                            "Group": f"Group {group}",
                            "Room": room['Room Name'],
                            "Lecturer": lecturer,
                            "Size": size
                        })
                        assigned = True
                        break
                if assigned:
                    break
            if assigned:
                break

    schedule_df = pd.DataFrame(schedule_output)
    pivot = schedule_df.pivot_table(
        index="Time", columns="Day",
        values=["Module", "Group", "Lecturer", "Room", "Size"],
        aggfunc=lambda x: '\n'.join(str(i) for i in x)
    ).fillna("")
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

    schedule_df, pivot_timetable = schedule_rooms(result_df, room_df)
    st.subheader("🗓️ Weekly Timetable by Room Allocation")
    st.dataframe(pivot_timetable)

    # Weekly summary
    all_lecturers = lecturers_df["Teacher's name"].unique()
    final_hours = {name: 0 for name in all_lecturers}
    for _, row in result_df.iterrows():
        if row["Lecturer"] in final_hours:
            final_hours[row["Lecturer"]] += row["Weekly Hours"]

    summary = pd.DataFrame({
        "Lecturer": list(final_hours.keys()),
        "Total Assigned Weekly Hours": list(final_hours.values()),
        "Max Weekly Workload": [lecturer_limits.get(name, 18) for name in final_hours.keys()]
    })
    summary["Remaining Weekly Workload"] = summary["Max Weekly Workload"] - summary["Total Assigned Weekly Hours"]
    summary["Occupancy %"] = (summary["Total Assigned Weekly Hours"] / summary["Max Weekly Workload"] * 100).round(1).astype(str) + " %"

    st.subheader(f"📈 Weekly Workload Summary – Trimester {selected_trimester}")
    st.dataframe(summary.sort_values(by="Remaining Weekly Workload"))

    # Cumulative Summary Button
    if st.button("📊 Generate Cumulative Workload Statistics"):
        cumulative = result_df.groupby(["Lecturer", "Trimester"])["Weekly Hours"].sum().unstack().fillna(0)
        cumulative = cumulative.reindex(index=all_lecturers, fill_value=0)
        cumulative = cumulative * 12
        cumulative["Total"] = cumulative.sum(axis=1)
        cumulative["Max Workload (Annual)"] = cumulative.index.map(lambda x: lecturer_limits.get(x, 18) * 12 * 3)
        cumulative["Occupancy %"] = (cumulative["Total"] / cumulative["Max Workload (Annual)"] * 100).round(1).astype(str) + " %"

        st.subheader("📊 Cumulative Lecturer Workload")
        st.dataframe(cumulative)

else:
    st.info("📈 Please upload lecturers, modules, and rooms datasets to begin.")
