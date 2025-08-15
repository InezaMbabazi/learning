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
# Generate scenario/project-based interview using ChatGPT API
# -----------------------------

def generate_quiz(competencies: List[str], hard_skills: List[str], soft_skills: List[str], tasks: List[str], num_questions: int) -> List[Dict]:
    if not competencies and not hard_skills and not soft_skills and not tasks:
        return []

    prompt = (
        f"You are an AI career mentor. Based on the following competencies: {competencies},"
        f" job hard skills: {hard_skills}, soft skills: {soft_skills}, and tasks: {tasks},"
        f" generate {num_questions} scenario-based or project-based interview questions that assess if a student can perform in the real job market and fit the job role." 
        f" Focus on practical tasks and competencies to see if the student has all necessary skills for the job." 
        f" For each question, provide grading criteria, hints, knowledge gaps if the student struggles, and actionable recommendations to improve and align with market requirements."
        f" Return as JSON list with keys: question, type, skill, grading_criteria, hints, gaps, recommendations."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        questions = json.loads(content)
    except Exception as e:
        st.error(f"Failed to generate quiz questions: {e}")
        questions = []
    return questions

# -----------------------------
# Grade student response using ChatGPT API
# -----------------------------

def grade_response(question: str, student_answer: str, grading_criteria: str) -> Dict:
    prompt = (
        f"You are an AI grader. The scenario/project question is: '{question}'."
        f" The grading criteria are: '{grading_criteria}'."
        f" The student answered: '{student_answer}'."
        f" Provide a grade (pass/fail), explain gaps if failed, and give recommendations to improve skills and fit the job market." 
        f" Focus on practical application and job readiness."
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
        st.error(f"Failed to grade response: {e}")
        return {"grade": "N/A", "gaps": "N/A", "recommendations": "N/A"}

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="AI Job Skills Scenario Quiz", layout="wide")
st.title("AI Job Skills Scenario/Project-Based Quiz")

# Input Section
st.header("Enter Job and Competencies")
competencies_txt = st.text_area("Module Competencies (one per line)")
hard_skills_txt = st.text_area("Hard Skills (one per line)")
soft_skills_txt = st.text_area("Soft Skills (one per line)")
tasks_txt = st.text_area("Key Tasks (one per line)")
num_questions = st.slider("Number of scenario/project questions", min_value=2, max_value=12, value=5)
job_title = st.text_input("Job Title", value="Junior Data Analyst")

# Use API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

if st.button("Generate Scenario/Project Quiz"):
    competencies = parse_list_block(competencies_txt)
    hard_skills = parse_list_block(hard_skills_txt)
    soft_skills = parse_list_block(soft_skills_txt)
    tasks = parse_list_block(tasks_txt)

    if not openai.api_key:
        st.error("OpenAI API key not found. Please add it to Streamlit secrets.")
    else:
        questions = generate_quiz(competencies, hard_skills, soft_skills, tasks, num_questions)

        if not questions:
            st.warning("No quiz questions generated. Please check your inputs.")
        else:
            st.subheader(f"Generated Scenario/Project Quiz for {job_title}")
            student_responses = []
            for i, q in enumerate(questions, start=1):
                st.markdown(f"**Q{i} ({q.get('type', 'N/A')})**")
                st.markdown(q.get('question'))
                student_answer = st.text_area(f"Your Answer for Q{i}", key=f"answer_{i}")

                if st.button(f"Submit Answer Q{i}", key=f"submit_{i}"):
                    grading_result = grade_response(q.get('question'), student_answer, q.get('grading_criteria'))
                    st.markdown(f"*Grade: {grading_result.get('grade', 'N/A')}*")
                    st.markdown(f"*Knowledge Gaps: {grading_result.get('gaps', 'N/A')}*")
                    st.markdown(f"*Recommendations: {grading_result.get('recommendations', 'N/A')}*")
                    student_responses.append({"question": q.get('question'), "answer": student_answer, **grading_result})

            if student_responses:
                st.download_button(
                    label="Download Graded Responses JSON",
                    data=json.dumps(student_responses, indent=2).encode('utf-8'),
                    file_name="graded_responses.json",
                    mime="application/json"
                )
