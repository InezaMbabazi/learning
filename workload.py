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

    # Check the columns of the teachers' dataframe
    st.write("Teachers Database Columns:")
    st.write(teachers_df.columns)

    # Initialize columns for tracking
    teachers_df['Weekly Assigned Hours'] = 0
    teachers_df['Assigned Modules'] = 0

    # Preprocess modules data
    # Calculate class size
    modules_df['Class Size'] = modules_df['Number of Students'] / modules_df['Sections']

    # Check if the module is scheduled (i.e., "When to Take Place")
    modules_df['Scheduled'] = modules_df['When to Take Place'].notnull()

    # Preprocess the hours for each module
    modules_df['Teaching Hours per Week'] = modules_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    modules_df['Office Hours per Week'] = modules_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    modules_df['Total Weekly Hours'] = modules_df['Teaching Hours per Week'] + modules_df['Office Hours per Week']
    modules_df['Assigned Teacher'] = None
    modules_df['Assistant Teacher'] = None

    # Assign modules to teachers ensuring class size and weekly hour limits
    for idx, module in modules_df.iterrows():
        # Step 1: Check if module is scheduled (i.e., "When to Take Place" has a value)
        if module['Scheduled']:
            assigned = False

            # Step 2: Find eligible teachers who can teach this module and have less than 12 hours already assigned
            eligible_teachers = teachers_df[
                (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
                (teachers_df['Assigned Modules'] < 3) &  # Ensure no teacher teaches more than 3 modules
                (teachers_df['Teacher Status'] == 'teacher')  # Ensure only teachers with "teacher status" are eligible
            ]

            # Ensure the teacher is qualified to teach this specific module
            eligible_teachers = eligible_teachers[eligible_teachers['Module Name'].str.contains(module['Module Name'], na=False)]

            if not eligible_teachers.empty:
                # Step 3: Assign the module to the first eligible teacher
                teacher = eligible_teachers.iloc[0]
                teachers_df.loc[teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                teachers_df.loc[teacher.name, 'Assigned Modules'] += 1
                modules_df.at[idx, 'Assigned Teacher'] = teacher["Teacher's Name"]
                assigned = True

                # Step 4: Assign assistant teacher for large classes (if class size > 50)
                if module['Class Size'] > 50:
                    assistant_candidates = teachers_df[
                        (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
                        (teachers_df['Assigned Modules'] < 3) &
                        (teachers_df['Teacher Status'] == 'teacher') &  # Ensure assistant is also under "teacher status"
                        (teachers_df["Teacher's Name"] != teacher["Teacher's Name"])  # Ensure assistant is not the same teacher
                    ]

                    if not assistant_candidates.empty:
                        assistant_teacher = assistant_candidates.iloc[0]
                        modules_df.at[idx, 'Assistant Teacher'] = assistant_teacher["Teacher's Name"]
                        teachers_df.loc[assistant_teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                        teachers_df.loc[assistant_teacher.name, 'Assigned Modules'] += 1

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
