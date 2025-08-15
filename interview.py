import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import re
import json
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer, util

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(page_title="Competency → Job → Interview Agent", layout="wide")

# -----------------------------
# Utilities & Models
# -----------------------------
@st.cache_resource(show_spinner=False)
def load_embedder():
    # Lightweight, fast model
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

embedder = load_embedder()

def embed(texts: List[str]):
    return embedder.encode(texts, convert_to_tensor=True, normalize_embeddings=True)

# -----------------------------
# Data Structures
# -----------------------------
@dataclass
class Competency:
    id: str
    title: str
    description: str
    tags: List[str]
    level: str  # intro|intermediate|advanced
    bloom: str  # remember|understand|apply|analyze|evaluate|create

@dataclass
class JobProfile:
    id: str
    title: str
    domain: str
    hard_skills: List[str]
    soft_skills: List[str]
    tasks: List[str]
    seniority: str  # junior|mid|senior

# -----------------------------
# Parsing Helpers
# -----------------------------
def parse_list_block(text: str) -> List[str]:
    items = []
    for line in text.splitlines():
        line = line.strip(" -•\t")
        if not line:
            continue
        items.append(line)
    return items

LEVELS = {"intro": 1, "intermediate": 2, "advanced": 3}
BLOOM = {"remember": 1, "understand": 2, "apply": 3, "analyze": 4, "evaluate": 5, "create": 6}

# -----------------------------
# Normalization & Matching
# -----------------------------
def normalize_skills(competencies: List[Competency], job: JobProfile) -> List[Dict[str, Any]]:
    comp_texts = [f"{c.title}. {c.description}. Tags: {', '.join(c.tags)}" for c in competencies]
    job_texts = job.hard_skills + job.soft_skills + job.tasks

    if len(comp_texts) == 0 or len(job_texts) == 0:
        return []

    comp_emb = embed(comp_texts)
    job_emb = embed(job_texts)

    sim_matrix = util.cos_sim(comp_emb, job_emb).cpu().numpy()  # (n_comp, n_job)

    matches = []
    for i, c in enumerate(competencies):
        j_best = int(np.argmax(sim_matrix[i]))
        best_sim = float(sim_matrix[i, j_best])
        # Weighting
        w_level = LEVELS.get(c.level, 1) / 3.0
        w_bloom = BLOOM.get(c.bloom, 1) / 6.0
        # importance: if matched item comes from tasks > hard > soft
        matched_text = job_texts[j_best]
        if matched_text in job.tasks:
            w_importance = 1.0
        elif matched_text in job.hard_skills:
            w_importance = 0.85
        else:
            w_importance = 0.7
        match_score = best_sim * (0.5 * w_level + 0.3 * w_bloom + 0.2 * w_importance)

        matches.append({
            "competency_id": c.id,
            "competency_title": c.title,
            "competency_level": c.level,
            "competency_bloom": c.bloom,
            "job_match": matched_text,
            "similarity": round(best_sim, 3),
            "weighted_score": round(match_score, 3)
        })
    # sort by weighted score descending
    matches.sort(key=lambda x: x["weighted_score"], reverse=True)
    return matches

# -----------------------------
# Interview Planning
# -----------------------------
def plan_interview(matches: List[Dict[str, Any]], quota: int = 8) -> List[Dict[str, Any]]:
    # diversify by types and difficulty
    types_cycle = ["technical", "scenario", "behavioral", "ethics", "debug"]
    plan: List[Dict[str, Any]] = []
    if not matches:
        return plan

    # difficulty mix for junior/mid; heuristic by rank
    for idx, m in enumerate(matches[: quota]):
        qtype = types_cycle[idx % len(types_cycle)]
        # higher rank → slightly higher difficulty
        base_diff = 2 + (idx // max(1, quota // 4))  # 2..5 roughly
        difficulty = int(np.clip(base_diff, 1, 5))
        plan.append({
            "competency_title": m["competency_title"],
            "job_match": m["job_match"],
            "type": qtype,
            "difficulty": difficulty,
            "similarity": m["similarity"],
            "weighted_score": m["weighted_score"],
        })
    return plan

# -----------------------------
# Question Generation (Template-based)
# -----------------------------
STAR_HINT = "Use the STAR method: Situation, Task, Action, Result."

def generate_question(skill: str, qtype: str, difficulty: int) -> Dict[str, Any]:
    difficulty_note = {
        1: "basic recall",
        2: "apply fundamentals",
        3: "analyze trade-offs",
        4: "optimize under constraints",
        5: "design and defend approach"
    }[difficulty]

    if qtype == "technical":
        prompt = (
            f"[{difficulty_note}] You are assigned a task involving '{skill}'. "
            "Describe, step-by-step, how you would implement a solution. Include assumptions, edge cases, and how you would validate correctness."
        )
        exemplar = (
            f"Break problem into steps; state assumptions; apply core '{skill}' methods; consider edge cases; verify with tests/metrics; discuss trade-offs."
        )
    elif qtype == "scenario":
        prompt = (
            f"[{difficulty_note}] A stakeholder reports an anomaly related to '{skill}'. "
            "Outline your investigation plan, hypotheses, required data, tools, and success criteria."
        )
        exemplar = (
            f"Form hypotheses; gather relevant data; prioritize checks; use appropriate tools for '{skill}'; define success metrics; communicate updates."
        )
    elif qtype == "behavioral":
        prompt = (
            f"[{difficulty_note}] Describe a real or hypothetical situation where you used '{skill}' in a team setting. {STAR_HINT} Focus on your decisions and outcomes."
        )
        exemplar = (
            f"Clear situation; task; concrete actions applying '{skill}'; measurable results; reflection on learning and collaboration."
        )
    elif qtype == "ethics":
        prompt = (
            f"[{difficulty_note}] You must apply '{skill}' involving sensitive data or users. Identify ethical risks (bias, privacy, transparency) and propose policy and technical mitigations."
        )
        exemplar = (
            f"Identify privacy/bias risks; consent and minimization; governance; testing for bias; documentation; stakeholder communication."
        )
    else:  # debug
        prompt = (
            f"[{difficulty_note}] Something using '{skill}' is failing (incorrect results or performance). Provide a debugging plan, diagnostics, and fixes."
        )
        exemplar = (
            f"Reproduce issue; isolate components; log/trace; test hypotheses; measure; implement fix; add regression tests; post-mortem."
        )

    rubric = {
        "criteria": [
            {"name": "Correctness", "weight": 0.4, "indicators": ["accuracy", "logic", "assumptions stated"]},
            {"name": "Depth", "weight": 0.3, "indicators": ["trade-offs", "edge cases", "metrics"]},
            {"name": "Clarity", "weight": 0.2, "indicators": ["structure", "conciseness"]},
            {"name": "Ethics/Safety", "weight": 0.1, "indicators": ["privacy", "bias", "risk mitigation"]},
        ],
        "scale": "0..100",
    }

    return {
        "prompt": prompt,
        "type": qtype,
        "difficulty": difficulty,
        "skill": skill,
        "exemplar": exemplar,
        "rubric": rubric,
        "time_limit_sec": 240,
    }

# -----------------------------
# Evaluation (Heuristic + Embedding)
# -----------------------------
def criterion_scores(response: str, exemplar: str) -> Dict[str, float]:
    # Similarity-based correctness/depth
    r = response.strip()
    if not r:
        return {"Correctness": 0.0, "Depth": 0.0, "Clarity": 0.0, "Ethics/Safety": 0.0}

    sim = float(util.cos_sim(embed([r])[0], embed([exemplar])[0]).cpu().item())

    # Depth: length and presence of advanced cues
    length_bonus = min(len(r.split()) / 200.0, 1.0)  # up to +1
    advanced_terms = len(re.findall(r"(trade[- ]?offs|edge cases|metrics|complexity|assumption|hypotheses)", r, re.I))
    depth_raw = 0.5 * sim + 0.5 * min(advanced_terms / 4.0 + length_bonus * 0.5, 1.0)

    # Clarity: bulleting/numbering/STAR hints
    clarity_cues = 0
    if re.search(r"\n- |\n\d+\. ", r):
        clarity_cues += 1
    if re.search(r"Situation|Task|Action|Result", r, re.I):
        clarity_cues += 1
    if re.search(r"First|Next|Finally|Step", r, re.I):
        clarity_cues += 1
    clarity_raw = min(0.4 + 0.3 * clarity_cues, 1.0)

    # Ethics: keywords
    ethics_hits = len(re.findall(r"(privacy|consent|bias|fairness|governance|security|transparen|mitigat)", r, re.I))
    ethics_raw = min(0.2 + 0.2 * ethics_hits, 1.0)

    return {
        "Correctness": max(sim, 0.0),
        "Depth": max(depth_raw, 0.0),
        "Clarity": max(clarity_raw, 0.0),
        "Ethics/Safety": max(ethics_raw, 0.0),
    }


def evaluate_response(resp: str, exemplar: str, rubric: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    cs = criterion_scores(resp, exemplar)
    total = 0.0
    for c in rubric["criteria"]:
        name = c["name"]
        w = c["weight"]
        total += 100.0 * cs.get(name, 0.0) * w
    return total, cs

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🎯 Competency → Job → Interview Agent (MVP)")
st.caption("Upload module competencies and a job profile to auto-generate a tailored interview, evaluate answers, and get feedback.")

with st.sidebar:
    st.header("Inputs")
    st.markdown("**Module Competencies** (paste or upload CSV)")
    comp_txt = st.text_area("One item per line. You can also add pipes for metadata: Title | Description | tags=a,b | level=intro | bloom=apply", height=180, placeholder="SQL Joins | Combine orders and customers | tags=SQL,JOIN | level=intermediate | bloom=apply\nData Privacy | Handle PII and consent | tags=privacy,ethics | level=intro | bloom=analyze")
    comp_csv = st.file_uploader("Or upload CSV with columns: title, description, tags, level, bloom", type=["csv"])

    st.markdown("---")
    st.markdown("**Job Profile** (paste or upload CSV)")
    job_title = st.text_input("Job Title", value="Junior Data Analyst")
    job_domain = st.text_input("Domain", value="Data & Analytics")
    hard_txt = st.text_area("Hard skills (one per line)", height=100, placeholder="SQL\nETL\nDashboards")
    soft_txt = st.text_area("Soft skills (one per line)", height=80, placeholder="Communication\nTeamwork")
    task_txt = st.text_area("Key tasks (one per line)", height=100, placeholder="Build weekly performance dashboards\nClean and join datasets from CRM and orders")
    seniority = st.selectbox("Seniority", ["junior", "mid", "senior"], index=0)

    st.markdown("---")
    quota = st.slider("Questions to generate", min_value=4, max_value=12, value=8)
    generate_btn = st.button("🚀 Generate Interview Plan")

# -----------------------------
# Build Competency Objects
# -----------------------------
def read_competencies_from_text(text: str) -> List[Competency]:
    comps: List[Competency] = []
    for idx, line in enumerate([l for l in text.splitlines() if l.strip()]):
        parts = [p.strip() for p in line.split("|")]
        title = parts[0] if len(parts) > 0 else f"Comp {idx+1}"
        desc = parts[1] if len(parts) > 1 else ""
        tags = []
        level = "intro"
        bloom = "understand"
        # parse metadata
        for p in parts[2:]:
            if "tags=" in p:
                tags = [t.strip() for t in p.split("=",1)[1].split(",") if t.strip()]
            elif "level=" in p:
                level = p.split("=",1)[1].strip().lower()
            elif "bloom=" in p:
                bloom = p.split("=",1)[1].strip().lower()
        comps.append(Competency(id=f"C{idx+1}", title=title, description=desc, tags=tags, level=level, bloom=bloom))
    return comps


def read_competencies_from_csv(file) -> List[Competency]:
    df = pd.read_csv(file)
    req = ["title", "description", "tags", "level", "bloom"]
    for r in req:
        if r not in df.columns:
            st.warning(f"CSV missing column: {r}")
    comps: List[Competency] = []
    for i, row in df.iterrows():
        tags = [] if pd.isna(row.get("tags", "")) else [t.strip() for t in str(row.get("tags", "")).split(",") if t.strip()]
        comps.append(Competency(
            id=f"C{i+1}",
            title=str(row.get("title", f"Comp {i+1}")),
            description=str(row.get("description", "")),
            tags=tags,
            level=str(row.get("level", "intro")).lower(),
            bloom=str(row.get("bloom", "understand")).lower(),
        ))
    return comps

# Build job profile

def build_job_profile(title: str, domain: str, hard: str, soft: str, tasks: str, seniority: str) -> JobProfile:
    return JobProfile(
        id="J1",
        title=title,
        domain=domain,
        hard_skills=parse_list_block(hard),
        soft_skills=parse_list_block(soft),
        tasks=parse_list_block(tasks),
        seniority=seniority,
    )

# Session state containers
if "questions" not in st.session_state:
    st.session_state.questions = []
if "plan" not in st.session_state:
    st.session_state.plan = []
if "matches" not in st.session_state:
    st.session_state.matches = []

# -----------------------------
# Generate plan & questions
# -----------------------------
if generate_btn:
    # competencies
    competencies: List[Competency] = []
    if comp_csv is not None:
        competencies = read_competencies_from_csv(comp_csv)
    else:
        competencies = read_competencies_from_text(comp_txt)

    job = build_job_profile(job_title, job_domain, hard_txt, soft_txt, task_txt, seniority)

    matches = normalize_skills(competencies, job)
    plan = plan_interview(matches, quota=quota)

    questions = []
    for item in plan:
        q = generate_question(skill=item["competency_title"], qtype=item["type"], difficulty=item["difficulty"])
        q.update({"similarity": item["similarity"], "weighted_score": item["weighted_score"], "job_match": item["job_match"]})
        questions.append(q)

    st.session_state.matches = matches
    st.session_state.plan = plan
    st.session_state.questions = questions

# -----------------------------
# Display Matches & Plan
# -----------------------------
col1, col2 = st.columns([1,1])

with col1:
    st.subheader("🔗 Competency ↔ Job Matching")
    if st.session_state.matches:
        dfm = pd.DataFrame(st.session_state.matches)
        st.dataframe(dfm, use_container_width=True)
    else:
        st.info("Generate a plan to see matches.")

with col2:
    st.subheader("🧭 Interview Plan")
    if st.session_state.plan:
        dfp = pd.DataFrame(st.session_state.plan)
        st.dataframe(dfp, use_container_width=True)
    else:
        st.info("Generate a plan to see interview blueprint.")

# -----------------------------
# Interview & Responses
# -----------------------------
st.subheader("📝 Interview – Answer the Questions")
if st.session_state.questions:
    responses = []
    with st.form("responses_form"):
        for i, q in enumerate(st.session_state.questions, start=1):
            with st.expander(f"Q{i} ({q['type']} • diff {q['difficulty']} • skill: {q['skill']})"):
                st.markdown(q["prompt"]) 
                resp = st.text_area(f"Your answer to Q{i}", key=f"resp_{i}", height=200)
                st.caption("Hint: organize with bullets or STAR; mention assumptions, trade-offs, metrics, and risks if relevant.")
            responses.append(resp)
        submitted = st.form_submit_button("🔍 Evaluate All Answers")

    if submitted:
        results = []
        for i, (q, r) in enumerate(zip(st.session_state.questions, responses), start=1):
            score, per = evaluate_response(r, q["exemplar"], q["rubric"])
            strengths = []
            gaps = []
            # Simple feedback based on thresholds
            if per["Correctness"] < 0.5:
                gaps.append("Strengthen core logic/accuracy; state assumptions explicitly.")
            else:
                strengths.append("Solid core logic and alignment with the task.")

            if per["Depth"] < 0.5:
                gaps.append("Add trade-offs, edge cases, and measurable success metrics.")
            else:
                strengths.append("Good depth with trade-offs and metrics.")

            if per["Clarity"] < 0.5:
                gaps.append("Improve structure (bullets/steps) and concise phrasing.")
            else:
                strengths.append("Clear structure and flow.")

            if per["Ethics/Safety"] < 0.5:
                gaps.append("Address privacy, bias, and governance risks with mitigations.")
            else:
                strengths.append("Considers ethics and risk mitigations.")

            results.append({
                "Question": f"Q{i}",
                "Type": q["type"],
                "Skill": q["skill"],
                "Difficulty": q["difficulty"],
                "Score": round(score, 1),
                "Correctness": round(per["Correctness"]*100, 0),
                "Depth": round(per["Depth"]*100, 0),
                "Clarity": round(per["Clarity"]*100, 0),
                "Ethics": round(per["Ethics/Safety"]*100, 0),
                "Strengths": "; ".join(strengths),
                "Gaps": "; ".join(gaps),
            })

        dfr = pd.DataFrame(results)
        st.subheader("📊 Results & Feedback")
        st.dataframe(dfr, use_container_width=True)

        overall = float(np.mean(dfr["Score"])) if not dfr.empty else 0.0
        st.metric("Overall Score", f"{overall:.1f} / 100")

        # Gap analysis by simple aggregation
        st.markdown("### 🔍 Gap Analysis")
        gap_notes = []
        if (dfr["Correctness"] < 60).any():
            gap_notes.append("Reinforce fundamentals; practice small targeted exercises.")
        if (dfr["Depth"] < 60).any():
            gap_notes.append("Add trade-offs, edge cases, and metric-driven thinking.")
        if (dfr["Clarity"] < 60).any():
            gap_notes.append("Use bullets, numbered steps, and concise sentences.")
        if (dfr["Ethics"] < 60).any():
            gap_notes.append("Incorporate privacy/bias risk assessments and mitigations.")
        if gap_notes:
            st.write("\n".join([f"- {n}" for n in gap_notes]))
        else:
            st.success("No major gaps detected across criteria.")

        # Download buttons
        st.markdown("### ⬇️ Export")
        st.download_button(
            label="Download detailed results (CSV)",
            data=dfr.to_csv(index=False).encode("utf-8"),
            file_name="interview_results.csv",
            mime="text/csv",
        )

        # Save plan and matches as JSON
        export_payload = {
            "matches": st.session_state.matches,
            "plan": st.session_state.plan,
            "questions": st.session_state.questions,
            "results": results,
            "overall": overall,
        }
        st.download_button(
            label="Download session bundle (JSON)",
            data=json.dumps(export_payload, indent=2).encode("utf-8"),
            file_name="session_bundle.json",
            mime="application/json",
        )
else:
    st.info("Use the sidebar to generate the interview.")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("MVP: template-based generation + embedding scoring. Add an LLM later for richer questions and grading.")
