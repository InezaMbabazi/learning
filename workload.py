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

# Your existing functions here (split_students, get_weekly_hours, generate_workload_assignment, schedule_rooms)
# ...

# At the end of schedule_rooms()
# return timetable_df, unassigned_modules, room_summary_df

def schedule_rooms(assignments, room_df):
    slots = ["08:00–10:00", "10:30–12:30", "14:00–16:00", "16:15–18:15"]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    schedule = {(slot, day): [] for slot in slots for day in weekdays}
    room_usage = defaultdict(lambda: {(slot, day): False for slot in slots for day in weekdays})
    used_slots = defaultdict(list)
    unassigned_modules = []

    assigned = assignments[assignments["Lecturer"] != "❌ Not Assigned"].copy()

    for _, row in assigned.iterrows():
        key_id = f"{row['Module Code']}_G{row['Group Number']}"
        sessions_scheduled = 0
        shuffled_slots = slots.copy()
        shuffled_days = weekdays.copy()
        random.shuffle(shuffled_slots)
        random.shuffle(shuffled_days)

        for slot in shuffled_slots:
            for day in shuffled_days:
                if (slot, day) in used_slots[key_id]:
                    continue
                for _, room in room_df.iterrows():
                    if row['Group Size'] <= room['capacity'] and not room_usage[room['Room Name']][(slot, day)]:
                        entry = f"{row['Module Name']}\nGroup {row['Group Number']}\n{room['Room Name']}\n{row['Lecturer']}\n{row['Group Size']} students"
                        schedule[(slot, day)].append(entry)
                        room_usage[room['Room Name']][(slot, day)] = True
                        used_slots[key_id].append((slot, day))
                        sessions_scheduled += 1
                        break
                if sessions_scheduled >= 2:
                    break
            if sessions_scheduled >= 2:
                break

        if sessions_scheduled < 2:
            unassigned_modules.append({
                "Module": row["Module Name"],
                "Group": row["Group Number"],
                "Lecturer": row["Lecturer"],
                "Students": row["Group Size"]
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
            "Total Slots": len(slots)*len(weekdays)
        })
    room_summary_df = pd.DataFrame(room_summary)
    room_summary_df["Usage %"] = (room_summary_df["Slots Used"] / room_summary_df["Total Slots"] * 100).round(1).astype(str) + "%"

    return timetable_df, unassigned_modules, room_summary_df

# Inside your Streamlit main app logic:
if lecturer_file and module_file and room_file:
    lecturers_df = pd.read_csv(lecturer_file) if lecturer_file.name.endswith('.csv') else pd.read_excel(lecturer_file)
    modules_df = pd.read_csv(module_file) if module_file.name.endswith('.csv') else pd.read_excel(module_file)
    room_df = pd.read_csv(room_file) if room_file.name.endswith('.csv') else pd.read_excel(room_file)

    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()
    room_df.columns = room_df.columns.str.strip()

    timetable_df, unassigned_modules, room_summary_df = schedule_rooms(modules_df, room_df)

    st.subheader("📅 Weekly Room Timetable")
    st.dataframe(timetable_df, use_container_width=True)

    st.subheader("📈 Room Utilization Summary")
    st.dataframe(room_summary_df, use_container_width=True)

    if unassigned_modules:
        st.subheader("⚠️ Some modules/groups could not be fully scheduled due to room constraints:")
        st.dataframe(pd.DataFrame(unassigned_modules), use_container_width=True)
    else:
        st.success("✅ All groups scheduled successfully in available rooms.")
