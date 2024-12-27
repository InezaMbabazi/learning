import pandas as pd
import streamlit as st

# Load templates
teach_module_template = pd.DataFrame({
    "Teacher's Name": ["John Doe", "Jane Smith", "Emily Davis", "Robert Brown"],
    "Module Code": ["M101", "M102", "M103", "M104"],
    "Module Name": ["Math", "Physics", "Chemistry", "Biology"],
    "Teacher Status": ["Main", "Main", "Main", "Assistant"],
})

students_database_template = pd.DataFrame({
    "Cohort": ["2024", "2024", "2024", "2024"],
    "Number of Students": [50, 80, 120, 60],
    "Module Name": ["Math", "Physics", "Chemistry", "Biology"],
    "Code": ["M101", "M102", "M103", "M104"],
    "Term": ["T1", "T1", "T1", "T2"],
    "Sections": [2, 2, 4, 2],
    "Year": ["2024", "2024", "2024", "2024"],
    "Credits": [10, 15, 20, 10],
    "Programme": ["Science", "Science", "Science", "Science"],
    "When to Take Place": ["Trimester 1", "Trimester 1", "Trimester 1", "Trimester 2"],
})

# Teaching and office hours logic
def calculate_hours(row):
    if row["Credits"] == 10:
        return {"Teaching Hours": 4, "Office Hours": 1}
    elif row["Credits"] == 15:
        return {"Teaching Hours": 4, "Office Hours": 2}
    elif row["Credits"] == 20:
        return {"Teaching Hours": 6, "Office Hours": 4}
    else:
        return {"Teaching Hours": 0, "Office Hours": 0}

# Calculate hours for each module
students_database_template = students_database_template.join(
    students_database_template.apply(calculate_hours, axis=1, result_type="expand")
)

# Merge templates
workload_df = pd.merge(
    students_database_template,
    teach_module_template,
    on=["Module Name", "Module Code"],
    how="left"
)

# Assign assistant logic
workload_df["Assistant Teacher"] = workload_df.apply(
    lambda row: "Assistant Assigned" if row["Number of Students"] > 60 else "None",
    axis=1
)

# Calculate weekly totals
workload_df["Teaching Hours (Weekly)"] = workload_df["Teaching Hours"]
workload_df["Office Hours (Weekly)"] = workload_df["Office Hours"]
workload_df["Total Hours (Weekly)"] = workload_df["Teaching Hours (Weekly)"] + workload_df["Office Hours (Weekly)"]

# Display weekly workload
weekly_workload = (
    workload_df.groupby(["Teacher's Name", "When to Take Place"])
    .agg({
        "Teaching Hours (Weekly)": "sum",
        "Office Hours (Weekly)": "sum",
        "Total Hours (Weekly)": "sum",
    })
    .reset_index()
)
st.write("Weekly Workload")
st.dataframe(weekly_workload)

# Download weekly workload
st.download_button(
    "Download Weekly Workload",
    weekly_workload.to_csv(index=False),
    "weekly_workload.csv"
)

# Calculate yearly totals
yearly_workload = (
    workload_df.groupby("Teacher's Name")
    .agg({
        "Teaching Hours (Weekly)": "sum",
        "Office Hours (Weekly)": "sum",
        "Total Hours (Weekly)": "sum",
    })
    .reset_index()
)
yearly_workload["Total Teaching Hours (Yearly)"] = yearly_workload["Teaching Hours (Weekly)"] * 12
yearly_workload["Total Office Hours (Yearly)"] = yearly_workload["Office Hours (Weekly)"] * 12
yearly_workload["Total Hours (Yearly)"] = yearly_workload["Total Hours (Weekly)"] * 12

# Display yearly workload
st.write("Yearly Workload")
st.dataframe(yearly_workload)

# Download yearly workload
st.download_button(
    "Download Yearly Workload",
    yearly_workload.to_csv(index=False),
    "yearly_workload.csv"
)

# Identify teachers exceeding weekly limits
overworked_teachers = weekly_workload[weekly_workload["Total Hours (Weekly)"] > 12]
st.write("Teachers Exceeding Weekly Workload Limit")
st.dataframe(overworked_teachers)
