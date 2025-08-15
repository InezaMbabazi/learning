import streamlit as st
import pandas as pd
import json
import openai
from typing import List, Dict

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="AI Interview Agent (ChatGPT API)", layout="wide")

# -----------------------------
# OpenAI API Key
# -----------------------------
openai.api_key = st.secrets.get('OPENAI_API_KEY', '')

# -----------------------------
# Data Structures
# -----------------------------
def parse_list_block(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]

# -----------------------------
# Streamlit Sidebar Inputs
# -----------------------------
with st.sidebar:
    st.header("Inputs")
    st.markdown("**Module Competencies** (one per line)")
    comp_txt = st.text_area("Paste competencies here", height=200)

    st.markdown("---")
    st.markdown("**Job Profile**")
    job_title = st.text_input("Job Title", value="Junior Data Analyst")
    hard_txt = st.text_area("Hard skills (one per line)")
    soft_txt = st.text_area("Soft skills (one per line)")
    task_txt = st.text_area("Key tasks (one per line)")

    st.markdown("---")
    quota = st.slider("Number of interview questions", min_value=4, max_value=12, value=6)
    generate_btn = st.button("🚀 Generate Interview")

# -----------------------------
# ChatGPT Helper with Error Handling
# -----------------------------

def generate_interview(competencies: List[str], hard_skills: List[str], soft_skills: List[str], tasks: List[str], num_questions: int) -> List[Dict]:
    if not competencies and not hard_skills and not soft_skills and not tasks:
        return []

    prompt = (
        f"You are an expert interviewer. Based on the following competencies: {competencies},"
        f" job hard skills: {hard_skills}, soft skills: {soft_skills}, and tasks: {tasks},"
        f" generate {num_questions} interview questions with types (technical, scenario, behavioral, ethics) and difficulty 1-5."
        f" Return as JSON list with keys: question, type, difficulty, skill, and hints."
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
        st.warning(f"Failed to generate JSON from API response. Fallback applied. Error: {e}")
        questions = [{"question": content if 'content' in locals() else 'API error occurred',
                      "type": "general", "difficulty": 3, "skill": "N/A", "hints": "N/A"}]
    return questions

# -----------------------------
# Main Logic with Session State
# -----------------------------
if 'questions' not in st.session_state:
    st.session_state.questions = []

if generate_btn:
    competencies = parse_list_block(comp_txt)
    hard_skills = parse_list_block(hard_txt)
    soft_skills = parse_list_block(soft_txt)
    tasks = parse_list_block(task_txt)

    if not openai.api_key:
        st.error("OpenAI API key not found. Add it to Streamlit secrets.")
    elif not (competencies or hard_skills or soft_skills or tasks):
        st.error("Please enter at least one competency, skill, or task.")
    else:
        with st.spinner("Generating interview questions..."):
            st.session_state.questions = generate_interview(competencies, hard_skills, soft_skills, tasks, quota)

if st.session_state.questions:
    st.subheader("🧭 Generated Interview Questions")
    for i, q in enumerate(st.session_state.questions, start=1):
        st.markdown(f"**Q{i} ({q.get('type', 'N/A')} • difficulty {q.get('difficulty', '-')})**")
        st.markdown(f"{q.get('question')}")
        st.markdown(f"*Hints: {q.get('hints', '')}*")

    st.markdown("---")
    st.download_button(
        label="Download Questions JSON",
        data=json.dumps(st.session_state.questions, indent=2).encode('utf-8'),
        file_name="interview_questions.json",
        mime="application/json"
    )
