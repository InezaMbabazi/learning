import streamlit as st
import json
from typing import List, Dict
import openai

# -----------------------------
# Parse input lists
# -----------------------------
def parse_list_block(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]

# -----------------------------
# Generate real project assignments with practical datasets
# -----------------------------

def generate_project(competencies: List[str], hard_skills: List[str], soft_skills: List[str], tasks: List[str], num_projects: int) -> List[Dict]:
    if not competencies and not hard_skills and not soft_skills and not tasks:
        return []

    prompt = (
        f"You are an AI career mentor. Based on the following competencies: {competencies},"
        f" job hard skills: {hard_skills}, soft skills: {soft_skills}, and tasks: {tasks},"
        f" generate {num_projects} real-world project assignments with example datasets, such as CSV or database examples," 
        f" that students can work on to demonstrate job readiness. For instance, a medical student may get a dataset of patients to find patients with HIV or high blood pressure."
        f" Each project should include: the project description, dataset details, grading criteria, hints, potential gaps, and recommendations for improvement."
        f" Return as JSON list with keys: project, type, skill, dataset_example, grading_criteria, hints, gaps, recommendations."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        projects = json.loads(content)
    except Exception as e:
        st.error(f"Failed to generate project assignments: {e}")
        projects = []
    return projects

# -----------------------------
# Grade student project response using ChatGPT API
# -----------------------------

def grade_project(project: str, student_answer: str, grading_criteria: str) -> Dict:
    prompt = (
        f"You are an AI grader. The project assignment is: '{project}'."
        f" The grading criteria are: '{grading_criteria}'."
        f" The student submitted: '{student_answer}'."
        f" Provide a grade (pass/fail), explain gaps if failed, and give recommendations to improve skills and fit the job market." 
        f" Focus on practical application, problem-solving, and job readiness."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        result = response.choices[0].message.content
        return json.loads(result)
    except Exception as e:
        st.error(f"Failed to grade project: {e}")
        return {"grade": "N/A", "gaps": "N/A", "recommendations": "N/A"}

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="AI Job Skills Real Project Assessment", layout="wide")
st.title("AI Job Skills Real Project Assessment")

# Input Section
st.header("Enter Job and Competencies")
competencies_txt = st.text_area("Module Competencies (one per line)")
hard_skills_txt = st.text_area("Hard Skills (one per line)")
soft_skills_txt = st.text_area("Soft Skills (one per line)")
tasks_txt = st.text_area("Key Tasks (one per line)")
num_projects = st.slider("Number of real project assignments", min_value=1, max_value=5, value=2)
job_title = st.text_input("Job Title", value="Junior Data Analyst")

# Use API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

if st.button("Generate Real Project Assessment"):
    competencies = parse_list_block(competencies_txt)
    hard_skills = parse_list_block(hard_skills_txt)
    soft_skills = parse_list_block(soft_skills_txt)
    tasks = parse_list_block(tasks_txt)

    if not openai.api_key:
        st.error("OpenAI API key not found. Please add it to Streamlit secrets.")
    else:
        projects = generate_project(competencies, hard_skills, soft_skills, tasks, num_projects)

        if not projects:
            st.warning("No project assignments generated. Please check your inputs.")
        else:
            st.subheader(f"Generated Real Project Assessment for {job_title}")
            student_responses = []
            for i, p in enumerate(projects, start=1):
                st.markdown(f"**Project {i} ({p.get('type', 'N/A')})**")
                st.markdown(p.get('project'))
                st.markdown(f"*Dataset Example: {p.get('dataset_example', 'N/A')}*")
                student_answer = st.text_area(f"Your Submission for Project {i}", key=f"answer_{i}")

                if st.button(f"Submit Project {i}", key=f"submit_{i}"):
                    grading_result = grade_project(p.get('project'), student_answer, p.get('grading_criteria'))
                    st.markdown(f"*Grade: {grading_result.get('grade', 'N/A')}*")
                    st.markdown(f"*Knowledge Gaps: {grading_result.get('gaps', 'N/A')}*")
                    st.markdown(f"*Recommendations: {grading_result.get('recommendations', 'N/A')}*")
                    student_responses.append({"project": p.get('project'), "answer": student_answer, **grading_result})

            if student_responses:
                st.download_button(
                    label="Download Graded Projects JSON",
                    data=json.dumps(student_responses, indent=2).encode('utf-8'),
                    file_name="graded_projects.json",
                    mime="application/json"
                )
