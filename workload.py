import streamlit as st
import pandas as pd

st.set_page_config(page_title="Workload Management System", layout="wide")

st.title("📚 Automated Workload Management System")

# Upload datasets
st.sidebar.header("Upload Datasets")
lecturer_file = st.sidebar.file_uploader("Upload Lecturers Dataset", type=["csv", "xlsx"])
module_file = st.sidebar.file_uploader("Upload Modules Dataset", type=["csv", "xlsx"])

if lecturer_file and module_file:
    # Read data
    if lecturer_file.name.endswith('.csv'):
        lecturers_df = pd.read_csv(lecturer_file)
    else:
        lecturers_df = pd.read_excel(lecturer_file)

    if module_file.name.endswith('.csv'):
        modules_df = pd.read_csv(module_file)
    else:
        modules_df = pd.read_excel(module_file)

    # Standardize column names
    lecturers_df.columns = lecturers_df.columns.str.strip()
    modules_df.columns = modules_df.columns.str.strip()

    # Trimester selection
    trimester_options = modules_df["When to Take Place"].dropna().unique()
    selected_trimester = st.selectbox("📅 Select When to Take Place (Trimester)", sorted(trimester_options))

    # Filter modules
    filtered_modules = modules_df[modules_df["When to Take Place"] == selected_trimester].copy()

    # Calculate weekly hours
    def get_weekly_hours(credits):
        return 6 if credits == 20 else 4 if credits in [10, 15] else 0

    filtered_modules["Weekly Hours"] = filtered_modules["Credits"].apply(get_weekly_hours)

    # Prepare lecturer assignments
    lecturers_df["Remaining Workload"] = lecturers_df["Weekly Workload"]

    assignments = []

    for _, module in filtered_modules.iterrows():
        module_code = module["Code"]
        hours_needed = module["Weekly Hours"]

        # Find matching lecturers by module code
        matching_lecturers = lecturers_df[lecturers_df["Module Code"] == module_code].sort_values(by="Remaining Workload", ascending=False)

        assigned = False
        for i, lecturer in matching_lecturers.iterrows():
            if lecturer["Remaining Workload"] >= hours_needed:
                # Assign module to this lecturer
                assignments.append({
                    "Lecturer": lecturer["Teacher's name"],
                    "Module Code": module_code,
                    "Module Name": module["Module Name"],
                    "Credits": module["Credits"],
                    "Cohort": module["Cohort"],
                    "Programme": module["Programme"],
                    "Weekly Hours": hours_needed,
                    "Trimester": selected_trimester
                })
                # Update remaining workload
                lecturers_df.at[i, "Remaining Workload"] -= hours_needed
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
                "Trimester": selected_trimester
            })

    result_df = pd.DataFrame(assignments)

    st.subheader("✅ Workload Assignment Results")
    st.dataframe(result_df, use_container_width=True)

    # Download
    csv = result_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Assignment Results as CSV", csv, "workload_assignments.csv", "text/csv")

    st.subheader("📊 Lecturer Remaining Workload")
    st.dataframe(lecturers_df[["Teacher's name", "Module Code", "Remaining Workload"]], use_container_width=True)

else:
    st.info("👈 Please upload both the lecturers and modules datasets to get started.")
