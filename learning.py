import requests
from urllib.parse import urlencode

API_TOKEN = "REPLACE_ME"  # rotate your token; don't hardcode in real apps
BASE_URL = "https://kepler.instructure.com/api/v1"

course_id = 3266
student_id = 4511  # MUST be the Canvas user ID

headers = {"Authorization": f"Bearer {API_TOKEN}"}

params = {
    "student_ids[]": student_id,
    "per_page": 100,
    "enrollment_state": "active",
    # Add helpful expansions:
    "include[]": ["submission_history", "assignment", "user"]
}

url = f"{BASE_URL}/courses/{course_id}/students/submissions"

print("REQUEST:", url, "?", urlencode(params, doseq=True))
r = requests.get(url, headers=headers, params=params)
print("STATUS:", r.status_code)

# Always show raw text on unexpected outcomes
try:
    data = r.json()
except Exception:
    print("RAW RESPONSE:", r.text)
    raise

# If it’s a list but empty, tell yourself that explicitly
if isinstance(data, list) and not data:
    print("No submissions found for this student in this course.")
else:
    # Pretty-print key fields; guard against None
    for sub in data:
        a = sub.get("assignment") or {}
        print("-----")
        print("Assignment ID:", sub.get("assignment_id"))
        print("Assignment Name:", a.get("name"))
        print("Graded At:", sub.get("graded_at"))
        print("Score:", sub.get("score"))
        print("Grade:", sub.get("grade"))
        print("Workflow State:", sub.get("workflow_state"))  # submitted/graded/etc.

# OPTIONAL: if you want to verify you have the right student_id:
users_url = f"{BASE_URL}/courses/{course_id}/users"
users_params = {"enrollment_type[]": "student", "per_page": 100}
ru = requests.get(users_url, headers=headers, params=users_params)
print("\nStudents in course (first page):", [u.get("id") for u in ru.json()])
