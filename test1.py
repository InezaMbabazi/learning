import requests

# Replace with your Canvas API URL, token, and course/assignment ID
canvas_url = 'https://kepler.instructure.com'
api_token = 'your_canvas_api_token'
course_id = '2624'
assignment_id = '41195'

# Set the headers for authentication
headers = {
    'Authorization': f'Bearer {api_token}'
}

# Endpoint to get submissions for the assignment
submission_url = f'{canvas_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions'

# Make the request to download submissions
response = requests.get(submission_url, headers=headers)

if response.status_code == 200:
    submissions = response.json()
    # Process and save submissions as needed
    print(submissions)
else:
    print(f"Failed to download submissions: {response.status_code}")
