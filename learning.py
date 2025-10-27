import requests

# Canvas API Token and base URL
API_TOKEN = "1941~9PvtMZ2M7xDtUhCWFv7yM7xYUeRT9tKvhGeM9Y6XHzaYDW7rtV9fZwyTemYTHYzM"
BASE_URL = "https://kepler.instructure.com/api/v1"

# Example IDs
course_id = 3266  # replace with actual course ID

# Define headers
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# API endpoint to get submissions (grades)
url = f"{BASE_URL}/courses/{course_id}/students/submissions?student_ids[]={student_id}"

# Make the request
response = requests.get(url, headers=headers)

# Show the results
if response.status_code == 200:
    data = response.json()
    for submission in data:
        print(f"Assignment: {submission['assignment_id']}")
        print(f"Grade: {submission['grade']}")
        print(f"Score: {submission['score']}")
        print("---")
else:
    print("Error:", response.status_code, response.text)
