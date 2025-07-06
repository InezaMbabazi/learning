import streamlit as st
import pandas as pd

st.set_page_config(page_title="Workload Management System", layout="wide")
st.title("📚 Automated Workload Management System")

# Initialize session state for cumulative results
if "all_results_df" not in st.session_state:
    st.session_state.all_results_df = pd.DataFrame()

# Upload files
st.sidebar.header("Upload Datasets")
lecturer_file = st.sidebar.file_uploader("Upload Lecturers Dataset", type=["csv", "xlsx"])
module_file = st.sidebar.file_uploader("Upload Modules Dataset", type=["csv", "xlsx"])

# Helper to split students into fair groups
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

# Pivot table summary across all trimesters
def show_trimester_summary(result_df, lecturers_df, all_trimesters):
    if not result_df.empty:
        pivot = pd.pivot_table(
            result_df[result_df["Lecturer"] != "❌ Not Assigned"],
            index="Lecturer",
            columns="Trimester",
            values="Weekly Hours",
            aggfunc='sum',
            fill_value=0
        )

        for t in all_trimesters:
            if t not in pivot.columns:
                pivot[t] = 0

        pivot = pivot[[t for t in sorted(all_trimesters)]]
        pivot["Total Hours"] = pivot.sum(axis=1)

        st.subheader("📊 Lecturer Workload Summary by Trimester")
        st.dataframe(pivot.style.format("{:.1f}"), use_container_width=True)

# App begins
if lecturer_file and module_file:
    lecturers_df = pd.read_csv(lecturer_file) if lecturer_file.name.endswith('.csv') else pd.read_excel(lecturer_file)
    modules_df = pd.read_csv(module_file) if module_file.name.endswith('.csv') else pd.read_excel(module_file)

    # Clean column names
    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()

    all_trimesters = sorted(modules_df["When to Take Place"].dropna().unique())
    selected_trimester = st.selectbox("🗕️ Select When to Take Place (Trimester)", all_trimesters)
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
    st.session_state.all_results_df = pd.concat([st.session_state.all_results_df, result_df], ignore_index=True)

    st.subheader("✅ Workload Assignment for Selected Trimester")
    st.dataframe(result_df, use_container_width=True)

    # Reassign Section
    if st.checkbox("✏️ Show Reassign Lecturers (Optional)"):
        new_lecturers = []
        st.subheader("🔁 Reassign Modules")
        for i, row in result_df.iterrows():
            module_code = row["Module Code"]
            current_lecturer = row["Lecturer"]
            eligible_lecturers = lecturers_df[lecturers_df["Module Code"] == module_code]["Teacher's name"].unique().tolist()
            if current_lecturer not in eligible_lecturers and current_lecturer != "❌ Not Assigned":
                eligible_lecturers.append(current_lecturer)
            selected = st.selectbox(
                f"Module: {row['Module Name']} (Group {row['Group Number']}) - Current: {current_lecturer}",
                options=["❌ Not Assigned"] + sorted(eligible_lecturers),
                index=( ["❌ Not Assigned"] + sorted(eligible_lecturers) ).index(current_lecturer),
                key=f"reassign_{i}"
            )
            new_lecturers.append(selected)

        if st.button("Apply Reassignments"):
            for i in range(len(result_df)):
                result_df.at[i, "Lecturer"] = new_lecturers[i]
            st.success("✅ Reassignments applied.")

    # Summary (all trimesters)
    show_trimester_summary(st.session_state.all_results_df, lecturers_df, all_trimesters)

    csv = st.session_state.all_results_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Full Assignment CSV", csv, "full_workload_summary.csv", "text/csv")

else:
    st.info("👈 Please upload both the lecturers and modules datasets to begin.")
