import itertools
from collections import defaultdict
import random

def schedule_rooms(assignments_df, room_df):
    # Define time slots and weekdays
    slots = ["08:00–10:00", "10:30–12:30", "14:00–16:00", "16:15–18:15"]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Initialize timetable dict and room usage tracker
    schedule = {(slot, day): [] for slot in slots for day in weekdays}
    room_usage = defaultdict(lambda: {(slot, day): False for slot in slots for day in weekdays})
    used_slots = defaultdict(list)  # To track module group scheduled slots
    unassigned_modules = []

    # Filter only assigned modules (lecturer assigned)
    assigned = assignments_df[assignments_df["Lecturer"] != "❌ Not Assigned"].copy()

    for _, row in assigned.iterrows():
        key_id = f"{row['Module Code']}_G{row['Group Number']}"
        sessions_scheduled = 0

        # Determine sessions per week by credits
        if row["Credits"] == 20:
            session_target = 3
        elif row["Credits"] in [10, 15]:
            session_target = 2
        else:
            session_target = 1

        # Shuffle slots and weekdays to spread schedule
        random.shuffle(slots)
        random.shuffle(weekdays)

        # Schedule sessions up to session_target
        for slot in slots:
            for day in weekdays:
                # Avoid duplicate scheduling of same session slot for the same module group
                if (slot, day) in used_slots[key_id]:
                    continue

                # Try to find a suitable room
                for _, room in room_df.iterrows():
                    if row['Group Size'] <= room['capacity'] and not room_usage[room['Room Name']][(slot, day)]:
                        entry = (
                            f"{row['Module Name']}\n"
                            f"Group {row['Group Number']}\n"
                            f"Room: {room['Room Name']}\n"
                            f"Lecturer: {row['Lecturer']}\n"
                            f"Students: {row['Group Size']}"
                        )
                        schedule[(slot, day)].append(entry)
                        room_usage[room['Room Name']][(slot, day)] = True
                        used_slots[key_id].append((slot, day))
                        sessions_scheduled += 1
                        break  # Break after assigning a room

                if sessions_scheduled >= session_target:
                    break
            if sessions_scheduled >= session_target:
                break

        # If unable to schedule all required sessions
        if sessions_scheduled < session_target:
            unassigned_modules.append({
                "Module": row["Module Name"],
                "Group": row["Group Number"],
                "Lecturer": row["Lecturer"],
                "Students": row["Group Size"],
                "Sessions Scheduled": sessions_scheduled,
                "Sessions Needed": session_target
            })

    # Convert schedule dict to DataFrame for display
    timetable_df = pd.DataFrame(index=slots, columns=weekdays)
    for (slot, day), entries in schedule.items():
        timetable_df.loc[slot, day] = "\n\n".join(entries) if entries else ""

    # Calculate room utilization summary
    room_summary = []
    total_slots = len(slots) * len(weekdays)
    for room, usage in room_usage.items():
        used_count = sum(1 for v in usage.values() if v)
        room_capacity = room_df.loc[room_df['Room Name'] == room, 'capacity'].values[0]
        room_summary.append({
            "Room": room,
            "Capacity": room_capacity,
            "Slots Used": used_count,
            "Total Slots": total_slots,
            "Usage %": f"{(used_count / total_slots * 100):.1f} %"
        })
    room_summary_df = pd.DataFrame(room_summary)

    return timetable_df, unassigned_modules, room_summary_df
