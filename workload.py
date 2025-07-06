import streamlit as st
import pandas as pd

st.set_page_config(page_title="Workload Management System", layout="wide")
st.title("📚 Automated Workload Management System")

# Upload files
st.sidebar.header("Upload Datasets")
lecturer_file = st.sidebar.file_uploader("Upload Lecturers Dataset", type=["csv", "xlsx"])
module_file = st.sidebar.file_uploader("Upload Modules Dataset", type=["csv", "xlsx"])

# Split logic
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

if lecturer_file and module_file:
    lecturers_df = pd.read_csv(lecturer_file) if lecturer_file.name.endswith('.csv') else pd.read_excel(lecturer_file)
    modules_df = pd.read_csv(module_file) if module_file.name.endswith('.csv') else pd.read_excel(module_file)

    # Clean columns
    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()

    trimester_options = modules_df["When to Take Place"].dropna().unique()
    selected_trimester = st.selectbox("📅 Select When to Take Place (Trimester)", sorted(trimester_options))
    filtered_modules = modules_df[modules_df["When to Take Place"] == selected_trimester].copy()

    def get_weekly_hours(credits):
        return 6 if credits == 20 else 4 if credits in [10, 15] else 0

    filtered_modules["Weekly Hours"] = filtered_modules["Credits"].apply(get_weekly_hours)

    lecturer_hours = {}
    assignments = []

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
            matching_lecturers["Remaining"] = 18 - matching_lecturers["Assigned Hours"]
            matching_lecturers = matching_lecturers.sort_values(by="Remaining", ascending=False)

            assigned = False
            for _, lecturer in matching_lecturers.iterrows():
                name = lecturer["Teacher's name"]
                if lecturer_hours[name] + hours_needed <= 18:
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

    result_df = pd.DataFrame(assignments)

    st.subheader("✅ Initial Workload Assignment")
    st.dataframe(result_df, use_container_width=True)

    # Manual reassignment
    st.subheader("✏️ Reassign Lecturers (Optional)")
    new_lecturers = []
    updated_lecturer_hours = lecturer_hours.copy()

    for i, row in result_df.iterrows():
        module_code = row["Module Code"]
        current = row["Lecturer"]
        hours = row["Weekly Hours"]
        label = f"{row['Module Name']} (Group {row['Group Number']})"

        eligible = lecturers_df[lecturers_df["Module Code"] == module_code]["Teacher's name"].unique().tolist()
        if current not in eligible and current != "❌ Not Assigned":
            eligible.append(current)

        selected = st.selectbox(
            f"➡️ {label} | Current: {current}",
            options=["❌ Not Assigned"] + sorted(eligible),
            index=(["❌ Not Assigned"] + sorted(eligible)).index(current) if current in eligible else 0,
            key=f"reassign_{i}"
        )
        new_lecturers.append(selected)

    if st.button("🔁 Apply Reassignments"):
        for i in range(len(result_df)):
            old = result_df.loc[i, "Lecturer"]
            new = new_lecturers[i]
            hours = result_df.loc[i, "Weekly Hours"]

            if old != "❌ Not Assigned":
                updated_lecturer_hours[old] -= hours
            if new != "❌ Not Assigned":
                if updated_lecturer_hours.get(new, 0) + hours <= 18:
                    updated_lecturer_hours[new] = updated_lecturer_hours.get(new, 0) + hours
                    result_df.loc[i, "Lecturer"] = new
                else:
                    st.warning(f"⚠️ {new} would exceed 18h — can't assign {result_df.loc[i, 'Module Name']} (Group {result_df.loc[i, 'Group Number']})")

        st.success("✅ Reassignments applied.")

        # 🔄 Show updated results
        st.subheader("📊 Updated Workload Assignment Results")
        st.dataframe(result_df, use_container_width=True)

        final_hours = {name: 0 for name in lecturers_df["Teacher's name"].unique()}
        for _, row in result_df.iterrows():
            if row["Lecturer"] != "❌ Not Assigned":
                final_hours[row["Lecturer"]] += row["Weekly Hours"]

        summary = pd.DataFrame(list(final_hours.items()), columns=["Lecturer", "Total Assigned Hours"])
        summary["Remaining Workload"] = 18 - summary["Total Assigned Hours"]

        st.subheader("📈 Updated Lecturer Remaining Workload Summary")
        st.dataframe(summary.sort_values(by="Remaining Workload"), use_container_width=True)

        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Updated Assignment CSV", csv, "updated_workload.csv", "text/csv")

    else:
        # Show initial summary if no reassignment done yet
        summary = pd.DataFrame(list(lecturer_hours.items()), columns=["Lecturer", "Total Assigned Hours"])
        summary["Remaining Workload"] = 18 - summary["Total Assigned Hours"]
        st.subheader("📈 Lecturer Remaining Workload Summary")
        st.dataframe(summary.sort_values(by="Remaining Workload"), use_container_width=True)

        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Initial Assignment CSV", csv, "initial_workload.csv", "text/csv")

else:
    st.info("👈 Please upload both the lecturers and modules datasets to begin.")
