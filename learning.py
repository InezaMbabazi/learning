import requests
from urllib.parse import urlencode

API_TOKEN = "1941~9PvtMZ2M7xDtUhCWFv7yM7xYUeRT9tKvhGeM9Y6XHzaYDW7rtV9fZwyTemYTHYzM"  # revoke the old token you posted, then put the new one here
BASE_URL = "https://kepler.instructure.com/api/v1"

course_id = 3266
student_id = 4511  # must be the Canvas internal user ID

headers = {"Authorization": f"Bearer {API_TOKEN}"}
params = {
    "student_ids[]": student_id,
    "per_page": 100,
    "enrollment_state": "active",
    "include[]": ["submission_history", "assignment", "user"],
}

url = f"{BASE_URL}/courses/{course_id}/students/submissions"
print("REQUEST:", url, "?", urlencode(params, doseq=True))

r = requests.get(url, headers=headers, params=params)
print("STATUS:", r.status_code)

# Try to decode JSON, otherwise show raw error text
try:
    data = r.json()
except Exception:
    print("RAW RESPONSE:", r.text)
    raise

# Normalize: submissions can come back as a list, or errors as a dict
submissions = []
if isinstance(data, list):
    submissions = data
elif isinstance(data, dict):
    if "errors" in data:
        print("API Errors:", data["errors"])
    elif "submissions" in data and isinstance(data["submissions"], list):
        submissions = data["submissions"]
    else:
        # Unexpected shape—show it so you can diagnose
        print("Unexpected JSON shape:", data)
else:
    print("Unknown response type:", type(data))

if not submissions:
    print("No submissions found for this student in this course.")
else:
    for sub in submissions:
        if not isinstance(sub, dict):
            # Skip anything that isn't a dict
            print("Skipping non-dict item:", type(sub))
            continue
        assignment = sub.get("assignment") or {}
        print("-----")
        print("Assignment ID:", sub.get("assignment_id"))
        print("Assignment Name:", assignment.get("name"))
        print("Graded At:", sub.get("graded_at"))
        print("Score:", sub.get("score"))
        print("Grade:", sub.get("grade"))
        print("Workflow State:", sub.get("workflow_state"))
