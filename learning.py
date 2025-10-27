import requests
import json

BASE_URL = "https://kepler.instructure.com/api/v1"
API_TOKEN = "1941~9PvtMZ2M7xDtUhCWFv7yM7xYUeRT9tKvhGeM9Y6XHzaYDW7rtV9fZwyTemYTHYzM"   # use env/secrets in real apps
course_id = 3266
assignment_id = 58846
student_id = 4511

headers = {"Authorization": f"Bearer {API_TOKEN}"}
params = {
    "include[]": ["assignment", "user", "submission_history", "rubric_assessment"]
}

url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}"
r = requests.get(url, headers=headers, params=params)

print("URL:", r.url)
print("STATUS:", r.status_code)

try:
    sub = r.json()
except Exception:
    print("RAW:", r.text)
    raise

print("\nRAW JSON:")
print(json.dumps(sub, indent=2))

# Safely read keys
assignment = (sub or {}).get("assignment") or {}
user = (sub or {}).get("user") or {}

summary = {
    "assignment_id": sub.get("assignment_id"),
    "assignment_name": assignment.get("name"),
    "user_id": sub.get("user_id"),
    "user_name": user.get("name"),
    "workflow_state": sub.get("workflow_state"),   # 'unsubmitted'|'submitted'|'graded' etc.
    "submitted_at": sub.get("submitted_at"),
    "graded_at": sub.get("graded_at"),
    "posted_at": sub.get("posted_at"),
    "score": sub.get("score"),
    "grade": sub.get("grade"),
    "entered_grade": sub.get("entered_grade"),
    "posted_grade": sub.get("posted_grade"),
}
print("\nSUMMARY:")
print(json.dumps(summary, indent=2))
