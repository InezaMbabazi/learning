import requests

# Replace with your Canvas API URL, token, and course/assignment ID
canvas_url = 'https://kepler.instructure.com'
api_token = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'  # Replace with your actual API token
course_id = '2624'  # Replace with your actual course ID
assignment_id = '41195'  # Replace with your actual assignment ID

# Set the headers for authentication
headers = {
    'Authorization': f'Bearer {api_token}'
}

# Endpoint to get submissions for the assignment
submission_url = f'{canvas_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions?per_page=100'

# Initialize an empty list to hold all submissions
all_submissions = []

# Make requests and handle pagination
while submission_url:
    response = requests.get(submission_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        all_submissions.extend(data)  # Add the submissions to our list

        # Check if there are more pages
        if 'next' in response.links:
            submission_url = response.links['next']['url']  # Move to the next page
        else:
            submission_url = None  # No more pages
    else:
        print(f"Failed to retrieve submissions: {response.status_code}")
        break

# Save or process submissions (this example just prints the submission IDs)
if all_submissions:
    print(f"Total submissions retrieved: {len(all_submissions)}")
    for submission in all_submissions:
        print(submission['id'])  # Or process the submission data as needed
else:
    print("No submissions found.")
