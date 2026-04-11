import time
import json
import os
from logic.utils import clean_input

# --- Configuration & Assets ---

CAREER_ALIASES = {
    "ai": "ai engineer", "ml": "machine learning engineer", "web": "web developer",
    "frontend": "frontend developer", "backend": "backend developer", "fullstack": "full stack developer",
    "mobile": "mobile app developer", "game": "game developer", "cyber": "cybersecurity analyst",
    "devops": "devops engineer", "cloud": "cloud engineer", "ui": "ui/ux designer",
    "ux": "ui/ux designer", "ds": "data scientist", "da": "data analyst", "ba": "business analyst",
    "blockchain": "blockchain developer", "qa": "software tester (qa)", "sysadmin": "system administrator",
    "ar": "ar/vr developer", "pm": "product manager",
}

ROADMAP_SKILL_MAP = {
    "python": "python", "javascript": "javascript", "js": "javascript", "sql": "sql",
    "database": "sql", "html": "html", "css": "css", "git": "git", "statistics": "statistics",
    "math": "math", "react": "react", "node": "node.js", "machine learning": "machine learning",
    "tensorflow": "tensorflow", "figma": "figma", "docker": "docker", "linux": "linux", "networking": "networking",
}

SKILL_REASONS = {
    "python": "Versatile back-end core.", "sql": "Essential for data persistence.",
    "javascript": "Powering the modern web.", "css": "Crucial for user interface.",
    "machine learning": "Driving predictive intelligence.", "networking": "Foundation of infrastructure.",
}

# --- Internal Engine Components ---

def load_career_data(filepath="data/careers.json"):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, filepath)
    try:
        with open(full_path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def _match_career(goal, career_data):
    goal_key = goal.lower()
    if goal_key in career_data: return goal_key, career_data[goal_key], True
    for key, data in career_data.items():
        if goal_key in data.get("title", "").lower() or goal_key in key:
            return key, data, False
    return None, None, False

def _promote_skills(user_skills, completed_steps, original_roadmap):
    new_skills, learned = set(user_skills), []
    roadmap_map = {i+1: text for i, text in enumerate(original_roadmap)}
    for step_key in completed_steps:
        parts = step_key.split("_")
        if len(parts) >= 3:
            try:
                text = roadmap_map.get(int(parts[-1]), "").lower()
                for kw, skill in ROADMAP_SKILL_MAP.items():
                    if kw in text and skill not in new_skills:
                        new_skills.add(skill); learned.append(skill)
            except Exception: continue
    return list(new_skills), learned

def _promote_experience(current_exp, progress_pct):
    if current_exp == "beginner" and progress_pct >= 0.7: return "intermediate", "Foundational mastery."
    if current_exp == "intermediate" and progress_pct >= 0.8: return "advanced", "Expertise demonstrated."
    return current_exp, None

def _detect_pivots(current_skills, current_key, current_score, career_data):
    best, user_set = None, set(s.lower() for s in current_skills)
    for key, data in career_data.items():
        if key == current_key: continue
        req = set(s.lower() for s in data.get("skills", []))
        if not req: continue
        match_pct = int((len(user_set & req) / len(req)) * 100)
        if match_pct > current_score + 15:
            best = {"title": data.get("title", key), "key": key, "match_percentage": match_pct, "advantage": match_pct - current_score}
    return best

# --- Public API / Orchestrator ---

def process_career_data(goal, user_skills_raw, exp_level, agent_state=None):
    t_start = time.perf_counter()
    agent_state = agent_state or {}
    completed = agent_state.get("completed_steps", [])
    
    # 1. Observe
    goal_norm = CAREER_ALIASES.get(goal.lower().strip(), goal.lower().strip())
    skills = clean_input(user_skills_raw)
    
    # 2. Analyze
    career_data = load_career_data()
    m_key, m_career, is_exact = _match_career(goal_norm, career_data)
    if not m_career: return {"status": "error", "message": "Career not found."}

    # Autonomous Learning & Level Promotion
    skills, learned = _promote_skills(skills, completed, m_career.get("roadmap", []))
    roadmap_len = len(m_career.get("roadmap", []))
    local_progress = len(completed) / max(roadmap_len, 1)
    updated_exp, promo_reason = _promote_experience(exp_level.lower(), local_progress)
    
    # Skill Gaps
    req_set = set(s.lower() for s in m_career.get("skills", []))
    missing = sorted(req_set - set(skills))
    match_pct = int((len(req_set - set(missing)) / max(len(req_set), 1)) * 100)
    
    pivot = _detect_pivots(skills, m_key, match_pct, career_data)
    
    # 3. Decide & Build Roadmap
    # Simplify decision logic
    readiness = "Master" if match_pct >= 90 else "Ready" if match_pct >= 75 else "Learning"
    next_action = f"Focus on {missing[0].title()}" if missing else "Apply for roles!"
    
    roadmap_steps = []
    for i, step in enumerate(m_career.get("roadmap", []), 1):
        step_is_done = f"step_{m_career.get('title', m_key)}_{i}" in completed
        roadmap_steps.append({"index": i, "text": step, "completed": step_is_done})

    # 4. Final Response
    obs = f"✦ **Learning Detected**: Added {', '.join(learned)}" if learned else None
    if promo_reason: obs = (obs + " | " if obs else "") + f"✦ **Rank-up**: {updated_exp.title()}"

    return {
        "status": "success",
        "title": m_career.get("title", m_key),
        "match_percentage": match_pct,
        "recommendation": m_career.get("title", m_key),
        "reasoning": f"Alignment: {match_pct}%",
        "readiness_summary": readiness,
        "expert_guidance": f"Keep going toward {m_key}!",
        "focus_area": "Upskilling",
        "next_action": next_action,
        "pivot_summary": f"Pivot to {pivot['title']} suggested" if pivot else None,
        "pivot_justification": f"Your skills match {pivot['title']} better (+{pivot['advantage']}%)" if pivot else None,
        "missing_skills": missing,
        "learned_skills": learned,
        "updated_skills": skills,
        "updated_experience_level": updated_exp,
        "agent_observation": obs,
        "roadmap_labeled": roadmap_steps,
        "total_steps": roadmap_len,
        "resources": m_career.get("resources", []),
        "thinking_trail": [{"name": "Agent Intelligence", "detail": f"Processed {m_key}", "duration_ms": round((time.perf_counter()-t_start)*1000, 1)}]
    }

def get_all_careers():
    data = load_career_data()
    return sorted([d.get("title", k) for k, d in data.items()])

def get_career_by_title(title):
    data = load_career_data()
    for _, d in data.items():
        if d.get("title") == title: return d
    return None

def compare_careers(title_a, title_b, skills_raw):
    c_a, c_b = get_career_by_title(title_a), get_career_by_title(title_b)
    if not c_a or not c_b: return None
    u_skills = set(clean_input(skills_raw))
    s_a, s_b = set(s.lower() for s in c_a["skills"]), set(s.lower() for s in c_b["skills"])
    m_a, m_b = len(u_skills & s_a) / len(s_a), len(u_skills & s_b) / len(s_b)
    rec = title_a if m_a >= m_b else title_b
    return {
        "recommended": rec,
        "justification": f"Better fit with {int(max(m_a, m_b)*100)}% alignment.",
        "match_a": m_a, "match_b": m_b,
        "effort_a": len(s_a - u_skills), "effort_b": len(s_b - u_skills),
        "strength": "strong" if abs(m_a - m_b) > 0.1 else "moderate"
    }
