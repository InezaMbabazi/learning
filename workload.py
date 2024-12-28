import pandas as pd
import streamlit as st

# Streamlit app
st.title("Teacher Workload Allocation")

# File upload
module_file = st.file_uploader("Upload Modules Database Template", type="csv")
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")

if module_file and teacher_file:
    # Load data
    modules_df = pd.read_csv(module_file)
    teachers_df = pd.read_csv(teacher_file)

    # Initialize tracking columns in teachers_df
    teachers_df['Weekly Assigned Hours'] = 0
    teachers_df['Assigned Modules'] = 0

    # Preprocess Modules Database Template
    modules_df['Class Size'] = (modules_df['Number of Students'] / modules_df['Sections']).apply(lambda x: round(x))
    modules_df['Scheduled'] = modules_df['When to Take Place'].notnull()
    modules_df['Teaching Hours per Week'] = modules_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    modules_df['Office Hours per Week'] = modules_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    modules_df['Total Weekly Hours'] = modules_df['Teaching Hours per Week'] + modules_df['Office Hours per Week']
    modules_df['Assigned Teacher'] = None
    modules_df['Assistant Teacher'] = None

    # Iterate over each section of each module
    for idx, module in modules_df.iterrows():
        if module['Scheduled']:
            # Create unique classes for each section
            for section in range(1, module['Sections'] + 1):
                assigned = False

                # Filter eligible "Main Teachers"
                main_teachers = teachers_df[
                    (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
                    (teachers_df['Assigned Modules'] < 3) &
                    (teachers_df['Teacher Status'] == 'Main Teacher') &
                    (teachers_df['Module Name'].str.contains(module['Module Name'], na=False))
                ]

                if not main_teachers.empty:
                    # Assign the module to the first eligible main teacher
                    main_teacher = main_teachers.iloc[0]
                    teachers_df.loc[main_teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                    teachers_df.loc[main_teacher.name, 'Assigned Modules'] += 1
                    assigned = True

                    # Assign assistant teacher for large classes
                    if module['Class Size'] > 50:
                        assistant_teachers = teachers_df[
                            (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
                            (teachers_df['Assigned Modules'] < 3) &
                            (teachers_df['Teacher Status'] == 'Assistant') &
                            (teachers_df["Teacher's Name"] != main_teacher["Teacher's Name"])
                        ]

                        if not assistant_teachers.empty:
                            assistant_teacher = assistant_teachers.iloc[0]
                            teachers_df.loc[assistant_teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                            teachers_df.loc[assistant_teacher.name, 'Assigned Modules'] += 1

                            modules_df.at[idx, 'Assistant Teacher'] = assistant_teacher["Teacher's Name"]

                    # Assign the main teacher
                    modules_df.at[idx, 'Assigned Teacher'] = main_teacher["Teacher's Name"]

                if not assigned:
                    # Log the module as unassigned if no main teacher is eligible
                    modules_df.at[idx, 'Assigned Teacher'] = 'Unassigned'

    # Display results
    st.write("Assigned Modules")
    st.dataframe(modules_df[modules_df['Assigned Teacher'] != 'Unassigned'])

    st.write("Unassigned Modules")
    st.dataframe(modules_df[modules_df['Assigned Teacher'] == 'Unassigned'])

    # Download buttons
    st.download_button(
        "Download Assigned Modules",
        modules_df[modules_df['Assigned Teacher'] != 'Unassigned'].to_csv(index=False),
        "assigned_modules.csv"
    )
    st.download_button(
        "Download Unassigned Modules",
        modules_df[modules_df['Assigned Teacher'] == 'Unassigned'].to_csv(index=False),
        "unassigned_modules.csv"
    )
