import requests
import streamlit as st

# Canvas API key - Insert here temporarily
API_TOKEN = "1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH"
BASE_URL = "https://kepler.instructure.com/api/v1"
course_id = 2906  # Your course ID
assignment_id = 47134  # Your assignment ID
user_id = 4794  # The user ID for the comment

# Headers with authorization
headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}

# URL construction for posting a comment
url = f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}/comments"
payload = {
    "comment": {
        "text_comment": "Great job on the submission!"  # Replace with your comment
    }
}

# Attempt the API request with enhanced error logging
try:
    response = requests.post(url, headers=headers, json=payload)

    # Check if request was successful
    if response.status_code == 201:
        st.success("Comment posted successfully.")
        st.json(response.json())  # Display response JSON for verification
    else:
        # Display the error details
        st.error(f"Failed to post comment. Status Code: {response.status_code}")
        st.write("URL:", url)  # Display the URL used in the request
        st.write("Response Headers:", response.headers)
        st.write("Response Text:", response.text)  # Display the full response text for debugging

except requests.exceptions.RequestException as e:
    st.error("An error occurred while trying to post the comment.")
    st.write("Exception Details:", e)
