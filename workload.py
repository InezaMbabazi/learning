import pandas as pd
import streamlit as st

# Streamlit app
st.title("Enhanced Teacher Workload Allocation")

# File upload
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
module_file = st.file_uploader("Upload Modules Database Template", type="csv")

if teacher_file and module_file:
    # Load data
    teachers_df = pd.read_csv(teacher_file)
    modules_df = pd.read_csv(module_file)

    # Initialize columns for tracking
    teachers_df['Weekly Assigned Hours'] = 0
    teachers_df['Assigned Modules'] = 0

    # Preprocess modules data
    modules_df['Teaching Hours per Week'] = modules_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    modules_df['Office Hours per Week'] = modules_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    modules_df['Total Weekly Hours'] = modules_df['Teaching Hours per Week'] + modules_df['Office Hours per Week']
    modules_df['Class Size'] = modules_df['Number of Students'] / modules_df['Sections']  # Assuming 'Sections' exists
    modules_df['Assigned Teacher'] = None

    # Assign modules to teachers ensuring "When to Take Place" is checked and no teacher exceeds 12 hours
    for idx, module in modules_df.iterrows():
        # Step 1: Check if module is scheduled (i.e., "When to Take Place" has a value)
        if pd.notnull(module['When to Take Place']):
            assigned = False

            # Step 2: Find eligible teachers who can teach this module and have less than 12 hours already assigned
            eligible_teachers = teachers_df[
                (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
                (teachers_df['Assigned Modules'] < 3)  # Ensure no teacher teaches more than 3 modules
            ]
            
            # Ensure the teacher is qualified to teach this specific module (optional, depending on your logic)
            eligible_teachers = eligible_teachers[eligible_teachers['Qualifications'].str.contains(module['Module Name'], na=False)]
            
            if not eligible_teachers.empty:
                # Step 3: Assign the module to the first eligible teacher
                teacher = eligible_teachers.iloc[0]
                teachers_df.loc[teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                teachers_df.loc[teacher.name, 'Assigned Modules'] += 1
                modules_df.at[idx, 'Assigned Teacher'] = teacher["Teacher's Name"]
                assigned = True

            if not assigned:
                # Log the module as unassigned if no teacher is eligible
                modules_df.at[idx, 'Assigned Teacher'] = 'Unassigned'

    # Display results
    st.write("Assigned Workload")
    st.dataframe(modules_df[modules_df['Assigned Teacher'] != 'Unassigned'])

    st.write("Unassigned Modules")
    st.dataframe(modules_df[modules_df['Assigned Teacher'] == 'Unassigned'])

    # Download buttons for assigned and unassigned modules
    st.download_button(
        "Download Assigned Workload",
        modules_df[modules_df['Assigned Teacher'] != 'Unassigned'].to_csv(index=False),
        "assigned_workload.csv"
    )
    st.download_button(
        "Download Unassigned Modules",
        modules_df[modules_df['Assigned Teacher'] == 'Unassigned'].to_csv(index=False),
        "unassigned_modules.csv"
    )
