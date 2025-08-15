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
# Generate full AI-managed interview projects with embedded scenarios
# -----------------------------

def generate_interview(competencies: List[str], hard_skills: List[str], soft_skills: List[str], job_title: str, num_questions: int) -> List[Dict]:
    prompt = (
        f"You are an AI hiring manager. Create a full practical interview for a '{job_title}' position based on these competencies: {competencies},"
        f" job hard skills: {hard_skills}, and soft skills: {soft_skills}."
        f" Generate {num_questions} scenario-based questions where all necessary data is embedded within the question itself (datasets, tables, or examples)."
        f" For each question, include: 'question', 'embedded_data', 'expected_skills', 'grading_criteria', and 'recommendations if failed'."
        f" Return as JSON list."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        # Ensure valid JSON parsing
        interview_questions = json.loads(content)
    except json.JSONDecodeError:
        st.error("Failed to parse JSON from AI. Please check the generated content.")
        interview_questions = []
    except Exception as e:
        st.error(f"Failed to generate interview: {e}")
        interview_questions = []

    return interview_questions

# -----------------------------
# Grade student answers
# -----------------------------

def grade_answer(question: str, student_answer: str, grading_criteria: str) -> Dict:
    prompt = (
        f"You are an AI grader. The interview question is: '{question}'."
        f" The grading criteria are: '{grading_criteria}'."
        f" The candidate answered: '{student_answer}'."
        f" Provide a JSON object with keys: 'grade', 'gaps', 'recommendations'."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        result_text = response.choices[0].message.content.strip()
        # Some responses may include extra text, extract JSON portion
        first_brace = result_text.find('{')
        last_brace = result_text.rfind('}')
        if first_brace != -1 and last_brace != -1:
            json_text = result_text[first_brace:last_brace+1]
            return json.loads(json_text)
        else:
            st.warning("AI response did not contain valid JSON.")
            return {"grade": "N/A", "gaps": "N/A", "recommendations": "N/A"}
    except Exception as e:
        st.error(f"Failed to grade answer: {e}")
        return {"grade": "N/A", "gaps": "N/A", "recommendations": "N/A"}

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="AI Full Interview Generator", layout="wide")
st.title("AI Full Interview Generator")

st.header("Job and Competencies Input")
competencies_txt = st.text_area("Module Competencies (one per line)")
hard_skills_txt = st.text_area("Hard Skills (one per line)")
soft_skills_txt = st.text_area("Soft Skills (one per line)")
job_title = st.text_input("Job Title", value="Junior Data Analyst")
num_questions = st.slider("Number of Interview Questions", min_value=1, max_value=10, value=5)

# Use API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

# Persist interview and responses in session state
if "interview" not in st.session_state:
    st.session_state["interview"] = []
if "responses" not in st.session_state:
    st.session_state["responses"] = {}

if st.button("Generate Full AI Interview"):
    competencies = parse_list_block(competencies_txt)
    hard_skills = parse_list_block(hard_skills_txt)
    soft_skills = parse_list_block(soft_skills_txt)

    if not openai.api_key:
        st.error("OpenAI API key not found. Please add it to Streamlit secrets.")
    else:
        st.session_state["interview"] = generate_interview(competencies, hard_skills, soft_skills, job_title, num_questions)
        st.session_state["responses"] = {}

if st.session_state["interview"]:
    st.subheader(f"Generated AI Interview for {job_title}")
    for i, q in enumerate(st.session_state["interview"], start=1):
        st.markdown(f"**Question {i}:** {q.get('question', 'N/A')}")
        if q.get('embedded_data'):
            st.markdown(f"*Embedded Data: {q.get('embedded_data')}*")
        answer_key = f"answer_{i}"
        st.session_state["responses"][answer_key] = st.text_area(
            f"Your Answer for Question {i}",
            value=st.session_state["responses"].get(answer_key, ""),
            key=answer_key
        )

    if st.button("Submit All Answers"):
        graded_results = []
        for i, q in enumerate(st.session_state["interview"], start=1):
            answer_key = f"answer_{i}"
            student_answer = st.session_state["responses"].get(answer_key, "")
            grading_result = grade_answer(q.get('question'), student_answer, q.get('grading_criteria'))
            st.markdown(f"**Question {i}:** {q.get('question')}\n*Grade: {grading_result.get('grade', 'N/A')}*")
            st.markdown(f"*Skill Gaps: {grading_result.get('gaps', 'N/A')}*")
            st.markdown(f"*Recommendations: {grading_result.get('recommendations', 'N/A')}*")
            graded_results.append({"question": q.get('question'), "answer": student_answer, **grading_result})

        st.download_button(
            label="Download Graded Interview JSON",
            data=json.dumps(graded_results, indent=2).encode('utf-8'),
            file_name="graded_ai_interview.json",
            mime="application/json"
        )
