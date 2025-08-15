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
# Generate practical quiz using ChatGPT API
# -----------------------------

def generate_quiz(competencies: List[str], hard_skills: List[str], soft_skills: List[str], tasks: List[str], num_questions: int) -> List[Dict]:
    if not competencies and not hard_skills and not soft_skills and not tasks:
        return []

    prompt = (
        f"You are an AI career mentor. Based on the following competencies: {competencies},"
        f" job hard skills: {hard_skills}, soft skills: {soft_skills}, and tasks: {tasks},"
        f" generate {num_questions} practical quiz questions that assess actual job-related skills for a student."
        f" For each question, provide grading criteria, hints, knowledge gaps if the student fails, and recommendations to improve and fit the label market."
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
# Streamlit App
# -----------------------------
st.set_page_config(page_title="AI Practical Quiz Agent", layout="wide")
st.title("AI Practical Quiz Agent")

# Input Section
st.header("Enter Job and Competencies")
competencies_txt = st.text_area("Module Competencies (one per line)")
hard_skills_txt = st.text_area("Hard Skills (one per line)")
soft_skills_txt = st.text_area("Soft Skills (one per line)")
tasks_txt = st.text_area("Key Tasks (one per line)")
num_questions = st.slider("Number of practical questions", min_value=2, max_value=12, value=5)
job_title = st.text_input("Job Title", value="Junior Data Analyst")

# Use API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

if st.button("Generate Practical Quiz"):
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
            st.subheader(f"Generated Practical Quiz for {job_title}")
            for i, q in enumerate(questions, start=1):
                st.markdown(f"**Q{i} ({q.get('type', 'N/A')})**")
                st.markdown(q.get('question'))
                st.markdown(f"*Grading Criteria: {q.get('grading_criteria', '')}*")
                st.markdown(f"*Hints: {q.get('hints', '')}*")
                st.markdown(f"*Knowledge Gaps: {q.get('gaps', 'N/A')}*")
                st.markdown(f"*Recommendations: {q.get('recommendations', 'N/A')}*")

            # Allow downloading as JSON
            st.download_button(
                label="Download Quiz JSON",
                data=json.dumps(questions, indent=2).encode('utf-8'),
                file_name="practical_quiz.json",
                mime="application/json"
            )
