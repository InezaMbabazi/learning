import pandas as pd
import streamlit as st

# Streamlit app
st.title("Simplified Teacher Workload Allocation")

# File upload
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
module_file = st.file_uploader("Upload Modules Database Template", type="csv")

if teacher_file and module_file:
    # Load data
    teachers_df = pd.read_csv(teacher_file)
    modules_df = pd.read_csv(module_file)

    # Initialize teacher tracking columns
    teachers_df['Weekly Assigned Hours'] = 0
    teachers_df['Assigned Modules'] = 0

    # Preprocess modules data
    modules_df['Teaching Hours per Week'] = modules_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    modules_df['Office Hours per Week'] = modules_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    modules_df['Total Weekly Hours'] = modules_df['Teaching Hours per Week'] + modules_df['Office Hours per Week']
    
    modules_df['Assigned Teacher'] = None

    # Function to check if a teacher can be assigned a module without exceeding 12 hours
    def can_assign_teacher(teacher_name, module_hours):
        current_hours = teachers_df.loc[teachers_df["Teacher's Name"] == teacher_name, "Weekly Assigned Hours"].values[0]
        return (current_hours + module_hours) <= 12

    # Assign modules to teachers based on "When to Take Place"
    for idx, module in modules_df.iterrows():
        assigned = False
        # Check if module is scheduled to take place
        if pd.notnull(module['When to Take Place']):
            # Find the teacher that can handle the module
            eligible_teachers = teachers_df[
                (teachers_df['Assigned Modules'] < 3)  # Ensure no teacher is assigned more than 3 modules
            ]

            for teacher_name, teacher_data in eligible_teachers.iterrows():
                # Check if the teacher can take the module without exceeding 12 hours
                if can_assign_teacher(teacher_name, module['Total Weekly Hours']):
                    # Assign the module to this teacher
                    modules_df.at[idx, 'Assigned Teacher'] = teacher_data["Teacher's Name"]
                    teachers_df.loc[teacher_data.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                    teachers_df.loc[teacher_data.name, 'Assigned Modules'] += 1
                    assigned = True
                    break
        
        if not assigned:
            # Log module as unassigned if no teacher can be found
            modules_df.at[idx, 'Assigned Teacher'] = 'Unassigned'

    # Generate outputs
    unassigned_modules = modules_df[modules_df['Assigned Teacher'] == 'Unassigned']
    workload_df = modules_df[modules_df['Assigned Teacher'] != 'Unassigned']

    # Calculate yearly workload
    yearly_workload = (
        workload_df.groupby("Assigned Teacher")
        .agg({"Total Weekly Hours": "sum"})
        .reset_index()
    )
    yearly_workload["Yearly Hours"] = yearly_workload["Total Weekly Hours"] * 12

    # Display results
    st.write("Assigned Workload")
    st.dataframe(workload_df)

    st.write("Yearly Workload")
    st.dataframe(yearly_workload)

    st.write("Unassigned Modules")
    st.dataframe(unassigned_modules)

    # Download buttons
    st.download_button(
        "Download Assigned Workload",
        workload_df.to_csv(index=False),
        "assigned_workload.csv"
    )
    st.download_button(
        "Download Yearly Workload",
        yearly_workload.to_csv(index=False),
        "yearly_workload.csv"
    )
    st.download_button(
        "Download Unassigned Modules",
        unassigned_modules.to_csv(index=False),
        "unassigned_modules.csv"
    )
