import streamlit as st
import requests
import json


# Replace with your actual Canvas details
API_TOKEN = "1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH"
BASE_URL = "https://kepler.instructure.com/api/v1"
course_id = "2906"  # Example course ID
assignment_id = "47134"  # Example assignment ID
user_id = "4794"  # Example user ID

# Comment text you want to post
feedback_text = "Great job on your assignment! Keep up the good work."

# Setup headers with API token
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Setup the payload for the comment
payload = {
    "comment": {
        "text_comment": feedback_text
    }
}

# Make a POST request to submit the comment
response = requests.post(
    f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}/comments",
    headers=headers,
    data=json.dumps(payload)
)

# Check if the request was successful
if response.status_code in [200, 201]:
    print("Comment posted successfully.")
else:
    print(f"Failed to post comment. Status Code: {response.status_code}")
    print("Response:", response.text)
