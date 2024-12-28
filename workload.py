import pandas as pd
import streamlit as st

# Streamlit app
st.title("Teacher Workload Allocation with Module Sections")

# File upload
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
module_file = st.file_uploader("Upload Modules Database Template", type="csv")

if teacher_file and module_file:
    # Load data
    teachers_df = pd.read_csv(teacher_file)
    modules_df = pd.read_csv(module_file)

    # Ensure necessary columns exist
    required_columns_modules = ['Number of Students', 'Sections', 'When to Take Place', 'Module Name']
    required_columns_teachers = ["Teacher's Name", 'Module Name', 'Teacher Status']

    missing_columns_modules = [col for col in required_columns_modules if col not in modules_df.columns]
    missing_columns_teachers = [col for col in required_columns_teachers if col not in teachers_df.columns]

    if missing_columns_modules or missing_columns_teachers:
        st.error(f"Missing columns:\nModules: {missing_columns_modules}\nTeachers: {missing_columns_teachers}")
    else:
        # Split modules into sections
        expanded_modules = []
        for _, module in modules_df.iterrows():
            class_size = module['Number of Students'] / module['Sections']
            for section in range(1, int(module['Sections']) + 1):
                expanded_modules.append({
                    'Module Name': module['Module Name'],
                    'Section': f"Section {section}",
                    'Class Size': round(class_size),
                    'When to Take Place': module['When to Take Place'],
                    'Teaching Hours per Week': 4 if class_size <= 50 else 6,
                    'Office Hours per Week': 1 if class_size <= 50 else 2,
                })

        # Create expanded modules DataFrame
        modules_df = pd.DataFrame(expanded_modules)
        modules_df['Total Weekly Hours'] = modules_df['Teaching Hours per Week'] + modules_df['Office Hours per Week']
        modules_df['Assigned Teacher'] = None

        # Initialize workload tracking for teachers
        teachers_df['Weekly Assigned Hours'] = 0
        teachers_df['Assigned Modules'] = 0

        # Assign teachers to modules
        for idx, module in modules_df.iterrows():
            if pd.notna(module['When to Take Place']):
                # Find eligible teacher
                eligible_teachers = teachers_df[
                    (teachers_df['Weekly Assigned Hours'] + module['Total Weekly Hours'] <= 12) &
                    (teachers_df['Assigned Modules'] < 3) &
                    (teachers_df['Module Name'].str.contains(module['Module Name'], na=False))
                ]

                if not eligible_teachers.empty:
                    # Assign to the first eligible teacher
                    selected_teacher = eligible_teachers.iloc[0]
                    teachers_df.loc[selected_teacher.name, 'Weekly Assigned Hours'] += module['Total Weekly Hours']
                    teachers_df.loc[selected_teacher.name, 'Assigned Modules'] += 1
                    modules_df.at[idx, 'Assigned Teacher'] = selected_teacher["Teacher's Name"]
                else:
                    modules_df.at[idx, 'Assigned Teacher'] = 'Unassigned'

        # Display results
        st.write("Assigned Workload")
        st.dataframe(modules_df[modules_df['Assigned Teacher'] != 'Unassigned'])

        st.write("Unassigned Modules")
        st.dataframe(modules_df[modules_df['Assigned Teacher'] == 'Unassigned'])

        # Download buttons
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

        st.write("Teacher Workload Summary")
        st.dataframe(teachers_df[['Teacher\'s Name', 'Weekly Assigned Hours', 'Assigned Modules']])
