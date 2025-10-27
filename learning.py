import streamlit as st
import requests

BASE_URL = "https://kepler.instructure.com/api/v1"
API_TOKEN = "1941~9PvtMZ2M7xDtUhCWFv7yM7xYUeRT9tKvhGeM9Y6XHzaYDW7rtV9fZwyTemYTHYzM"
course_id, assignment_id, student_id = 3266, 58846, 4511

headers = {"Authorization": f"Bearer {API_TOKEN}"}
params = {"include[]": ["assignment", "user", "submission_history", "rubric_assessment"]}

url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}"
r = requests.get(url, headers=headers, params=params)

st.write("Status:", r.status_code)
try:
    sub = r.json()
except Exception:
    st.code(r.text)
    st.stop()

if isinstance(sub, dict) and sub:
    st.write({
        "assignment_name": (sub.get("assignment") or {}).get("name"),
        "score": sub.get("score"),
        "grade": sub.get("grade"),
        "entered_grade": sub.get("entered_grade"),
        "graded_at": sub.get("graded_at"),
        "posted_at": sub.get("posted_at"),
        "workflow_state": sub.get("workflow_state"),
    })
else:
    st.info("No submission returned for this student/assignment.")
