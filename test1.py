import requests

# Replace with your Canvas API URL and token
canvas_url = 'https://kepler.instructure.com/api/v1'
api_token = '1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'  # Replace with your actual API token
course_id = '2624'  # Course ID from the link you provided

# Set the headers for authentication
headers = {
    'Authorization': f'Bearer {api_token}'
}

# Endpoint to get course details
course_url = f'{canvas_url}/courses/{course_id}'

print(f"Fetching course details from: {course_url}")

response = requests.get(course_url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    course_data = response.json()
    print(f"Course Name: {course_data['name']}")  # Display the course name
    print(f"Course ID: {course_data['id']}")  # Display the course ID for reference
else:
    print(f"Failed to retrieve course details. Status code: {response.status_code}")
    print("Error response:", response.text)  # Print the full error message for debugging
import requests

# Replace with your Canvas API URL and token
canvas_url = 'https://kepler.instructure.com/api/v1'
api_token = 'y1941~tNNratnXzJzMM9N6KDmxV9XMC6rUtBHY2w2K7c299HkkHXGxtWEYWUQVkwch9CAH'  # Replace with your actual API token
course_id = '2624'  # Course ID from the link you provided

# Set the headers for authentication
headers = {
    'Authorization': f'Bearer {api_token}'
}

# 1. Get all assignments for the course
assignments_url = f'{canvas_url}/courses/{course_id}/assignments?per_page=100'

print(f"Fetching assignments from: {assignments_url}")

response = requests.get(assignments_url, headers=headers)

# Check status code for successful request
print(f"Status code: {response.status_code}")  # This will show if the request was successful
if response.status_code == 200:
    assignments = response.json()
    
    print(f"Response JSON: {assignments}")  # Print the raw response JSON
    
    if assignments:
        print("Assignments in this course:")
        for idx, assignment in enumerate(assignments, 1):
            print(f"{idx}. {assignment['name']} (ID: {assignment['id']})")
        
        # 2. Allow the user to select an assignment
        assignment_choice = int(input("Enter the number of the assignment you want to view submissions for: ")) - 1
        selected_assignment = assignments[assignment_choice]
        assignment_id = selected_assignment['id']
        print(f"\nYou selected: {selected_assignment['name']} (ID: {assignment_id})")
        
        # 3. Retrieve submissions for the selected assignment
        submission_url = f'{canvas_url}/courses/{course_id}/assignments/{assignment_id}/submissions?per_page=100'
        print(f"Fetching submissions from: {submission_url}")
        
        # Initialize an empty list to hold all submissions
        all_submissions = []
        
        # Make requests and handle pagination
        while submission_url:
            response = requests.get(submission_url, headers=headers)
            print(f"Fetching page: {submission_url}")  # Show the URL being fetched
            print(f"Status code for submissions: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                all_submissions.extend(data)  # Add the submissions to our list
                
                # Check if there are more pages
                if 'next' in response.links:
                    submission_url = response.links['next']['url']  # Move to the next page
                    print("Moving to next page...")
                else:
                    submission_url = None  # No more pages
            else:
                print(f"Failed to retrieve submissions: {response.status_code}")
                print("Error response:", response.text)  # Print error details
                break

        # Display or download submissions (this example just prints the submission IDs and users)
        if all_submissions:
            print(f"\nTotal submissions retrieved for {selected_assignment['name']}: {len(all_submissions)}")
            for submission in all_submissions:
                print(f"Submission ID: {submission['id']}, Submitted by User ID: {submission['user_id']}")
        else:
            print("No submissions found.")
    else:
        print("No assignments found in this course.")
else:
    print(f"Failed to retrieve assignments. Status code: {response.status_code}")
    print("Response details:", response.text)  # Print the full response details if needed
