import streamlit as st
import pandas as pd
import numpy as np

def create_cohort_template():
    data = {
        "Cohort": ["BsBA 2024"],
        "Total_Students": [49],
        "Module_Code": ["BSA82102"],
        "Module_Name": ["Python for Business Analytics"],
        "Credits": [15]
    }
    df = pd.DataFrame(data)
    df.to_csv("cohort_template.csv", index=False)
    return df

def create_room_template():
    data = {
        "Room_Name": ["Room A"],
        "Square_Meters": [100]
    }
    df = pd.DataFrame(data)
    df.to_csv("room_template.csv", index=False)
    return df

# Load Data
st.title("Classroom Allocation System")

st.subheader("Upload Cohort Data")
cohort_file = st.file_uploader("Upload cohort CSV", type=["csv"])
if cohort_file is not None:
    df_cohort = pd.read_csv(cohort_file)
else:
    df_cohort = create_cohort_template()

st.subheader("Upload Room Data")
room_file = st.file_uploader("Upload room CSV", type=["csv"])
if room_file is not None:
    df_room = pd.read_csv(room_file)
else:
    df_room = create_room_template()

# Classroom Calculation
square_meters_per_student = 1.5
def calculate_allocation(df_cohort, df_room):
    df_cohort["Total_Hours"] = df_cohort["Credits"].apply(lambda x: (6 if x == 15 else (8 if x == 20 else 5)) * 12)
    df_cohort["Hours_per_Week"] = df_cohort["Total_Hours"] // 12
    df_cohort["Sections"] = df_cohort.apply(lambda row: max(1, int(np.ceil(row["Total_Students"] / 
                                            max(df_room["Square_Meters"] // square_meters_per_student)))), axis=1)
    df_cohort["Total_Square_Meters"] = df_cohort["Total_Students"] * square_meters_per_student
    return df_cohort

result_df = calculate_allocation(df_cohort, df_room)

# Display Data
st.subheader("Cohort Data")
st.dataframe(df_cohort)

st.subheader("Room Data")
st.dataframe(df_room)

st.subheader("Classroom Allocation Report")
st.dataframe(result_df)
