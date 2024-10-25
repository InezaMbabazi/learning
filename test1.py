import requests

# Replace with your Canvas API URL and token
canvas_url = 'https://kepler.instructure.com'
api_token = 'your_canvas_api_token'  # Replace with your actual API token
course_id = '2624'  # Replace with your actual course ID

# Set the headers for authentication
headers = {
    'Authorization': f'Bearer {api_token}'
}

# 1. Get all assignments for the course
assignments_url = f'{canvas_url}/api/v1/courses/{course_id}/assignments?per_page=100'

response = requests.get(assignments_url, headers=headers)
if response.status_code == 200:
    assignments = response.json()
    if assignments:
        print("Assignments in this course:")
        for idx, assignment in enumerate(assignments, 1):
            print(f"{idx}. {assignment['name']} (ID: {assignment['id']})")
        
        # 2. Allow the user to select an assignment
        assignment_choice = int(input("Enter the number of the assignment you want to view submissions for: ")) - 1
        selected_assignment = assignments[assignment_choice]
        assignment_id = selected_assignment['id']
        print(f"\nYou selected: {selected_assignment['name']}")
        
        # 3. Retrieve submissions for the selected assignment
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
            print(f"\nTotal submissions retrieved for {selected_assignment['name']}: {len(all_submissions)}")
            for submission in all_submissions:
                print(f"Submission ID: {submission['id']}, Submitted by: {submission['user_id']}")
        else:
            print("No submissions found.")
    else:
        print("No assignments found in this course.")
else:
    print(f"Failed to retrieve assignments: {response.status_code}")
