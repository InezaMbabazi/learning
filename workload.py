import pandas as pd
import streamlit as st

# Streamlit app
st.title("Lecturer Workload Allocation with Editing Capability")

# Upload files
teacher_file = st.file_uploader("Upload Teachers Database Template", type="csv")
student_file = st.file_uploader("Upload Students Database Template", type="csv")

if teacher_file and student_file:
    # Load the data
    teachers_df = pd.read_csv(teacher_file)
    students_df = pd.read_csv(student_file)

    # Process and calculate workload
    students_df['Teaching Hours per Week'] = students_df['Credits'].apply(lambda x: 4 if x in [10, 15] else 6)
    students_df['Office Hours per Week'] = students_df['Credits'].apply(lambda x: 1 if x == 10 else (2 if x == 15 else 4))
    students_df['Total Weekly Hours'] = students_df['Teaching Hours per Week'] + students_df['Office Hours per Week']

    workload = []
    for _, module in students_df.iterrows():
        workload.append({
            "Teacher's Name": "Unassigned",
            "Assistant Teacher": "None",
            "Module Name": module["Module Name"],
            "Teaching Hours (Weekly)": module["Teaching Hours per Week"],
            "Office Hours (Weekly)": module["Office Hours per Week"],
            "Total Hours (Weekly)": module["Total Weekly Hours"],
            "When to Take Place": module["When to Take Place"]
        })

    # Convert workload to DataFrame
    workload_df = pd.DataFrame(workload)

    # Display workload with editing option
    st.write("### Workload Table")
    edited_workload = st.experimental_data_editor(workload_df, num_rows="dynamic", use_container_width=True)

    # Save updates to the workload
    if st.button("Save Updates"):
        workload_df = edited_workload
        st.success("Workload updated successfully!")

    # Calculate yearly workload
    yearly_workload = (
        workload_df.groupby("Teacher's Name")
        .agg({"Total Hours (Weekly)": "sum"})
        .reset_index()
    )
    yearly_workload["Yearly Hours"] = yearly_workload["Total Hours (Weekly)"] * 12

    # Display yearly workload
    st.write("### Yearly Workload Table")
    st.dataframe(yearly_workload)

    # Form to update workload
    st.write("### Update Specific Workload Entry")
    with st.form("update_workload_form"):
        teacher_name = st.selectbox("Select Teacher's Name", workload_df["Teacher's Name"].unique())
        module_name = st.selectbox("Select Module Name", workload_df["Module Name"].unique())
        assistant_teacher = st.text_input("Assistant Teacher (Optional)", "None")
        when_to_take_place = st.selectbox("When to Take Place", workload_df["When to Take Place"].unique())
        submit_button = st.form_submit_button(label="Update Workload")

        if submit_button:
            workload_df.loc[
                (workload_df["Teacher's Name"] == teacher_name) &
                (workload_df["Module Name"] == module_name),
                ["Assistant Teacher", "When to Take Place"]
            ] = [assistant_teacher, when_to_take_place]
            st.success("Workload updated successfully!")

    # Display updated workload
    st.write("### Updated Workload Table")
    st.dataframe(workload_df)

    # Download buttons
    st.download_button(
        "Download Updated Workload",
        workload_df.to_csv(index=False),
        "updated_workload.csv"
    )
    st.download_button(
        "Download Yearly Workload",
        yearly_workload.to_csv(index=False),
        "yearly_workload.csv"
    )
