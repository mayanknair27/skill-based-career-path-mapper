import re
import time
import math
import json
import os
import hashlib
from functools import lru_cache
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

from logic.db import db_get_all_careers, db_get_career_by_title, db_save_career, db_get_completed_milestones
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

# --- Utility ---

def clean_input(user_input):
    """Cleans user input by lowercasing and splitting skills."""
    if not user_input:
        return []
    if isinstance(user_input, list):
        user_input = ",".join(user_input)
    return [s.strip().lower() for s in re.split(r'[,\n]+', user_input) if s.strip()]

# --- Internal Engine Components ---

def generate_career_data(goal: str):
    """
    Uses Gemini AI to generate a structured career roadmap.
    """
    if not api_key:
        return None

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Generate a highly professional, industry-standard career roadmap for the role: "{goal}".
    
    Return the result STRICTLY as a raw JSON object with this exact structure:
    {{
      "title": "Clean Professional Title",
      "avg_salary": "$X - $Y (USD)",
      "market_demand": 1-100 (integer),
      "difficulty": "Beginner/Intermediate/Advanced/Hard",
      "skills": ["skill1", "skill2", "skill3", "skill4", "skill5", "skill6", "skill7"],
      "roadmap": [
        "Step 1 text (Actionable)",
        "Step 2 text (Detailed)",
        "Step 3 text (Strategic)",
        "Step 4 text",
        "Step 5 text",
        "Step 6 text",
        "Step 7 text",
        "Step 8 text",
        "Step 9 text",
        "Step 10 text (Completion)"
      ],
      "resources": [
        {{"name": "Resource Name", "url": "https://..."}},
        {{"name": "Secondary Resource", "url": "https://..."}}
      ]
    }}

    Rules:
    1. Only return the JSON. No conversational text.
    2. Ensure the roadmap has exactly 10 logical, progressive steps.
    3. Skills should include both technical and soft skills (7 total).
    4. Market demand should reflect 2024-2025 industry trends.
    """

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up possible markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()
            
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"AI Generation Error: {{e}}")
        return None

def load_career_data():
    return db_get_all_careers()

def _match_career(goal):
    goal_key = goal.lower()
    # Try exact match in DB
    m_career = db_get_career_by_title(goal_key)
    if m_career:
        return m_career["key"], m_career, True
    
    # Try fuzzy match in DB
    career_data = db_get_all_careers()
    for key, data in career_data.items():
        if goal_key in data.get("title", "").lower() or goal_key in key:
            return key, data, False
    return None, None, False

def _promote_skills(user_skills, completed_steps, original_roadmap):
    new_skills, learned = set(user_skills), []
    roadmap_map = {i + 1: text for i, text in enumerate(original_roadmap)}
    for step_key in completed_steps:
        parts = step_key.split("_")
        if len(parts) >= 3:
            try:
                text = roadmap_map.get(int(parts[-1]), "").lower()
                for kw, skill in ROADMAP_SKILL_MAP.items():
                    if kw in text and skill not in new_skills:
                        new_skills.add(skill)
                        learned.append(skill)
            except Exception:
                continue
    return list(new_skills), learned

def _promote_experience(current_exp, progress_pct):
    if current_exp == "beginner" and progress_pct >= 0.7:
        return "intermediate", "Foundational mastery."
    if current_exp == "intermediate" and progress_pct >= 0.8:
        return "advanced", "Expertise demonstrated."
    return current_exp, None

def _detect_pivots(current_skills, current_key, current_score, career_data):
    best, user_set = None, set(s.lower() for s in current_skills)
    for key, data in career_data.items():
        if key == current_key:
            continue
        req = set(s.lower() for s in data.get("skills", []))
        if not req:
            continue
        match_pct = int((len(user_set & req) / len(req)) * 100)
        if match_pct > current_score + 15:
            best = {"title": data.get("title", key), "key": key, "match_percentage": match_pct, "advantage": match_pct - current_score}
    return best

# --- Public API / Orchestrator ---

def process_career_data(goal, user_skills_raw, exp_level, username="anon", agent_state=None):
    t_start = time.perf_counter()
    agent_state = agent_state or {}
    # 1. Observe
    goal_norm = CAREER_ALIASES.get(goal.lower().strip(), goal.lower().strip())
    skills = clean_input(user_skills_raw)

    # 2. Analyze
    m_key, m_career, is_exact = _match_career(goal_norm)
    
    if not m_career:
        # AUTOMATION: Trigger AI Generation
        print(f"Goal '{goal_norm}' not found. Generating via AI...")
        generated = generate_career_data(goal_norm)
        if generated:
            m_key = goal_norm.replace(" ", "_")
            db_save_career(m_key, generated, is_ai=True)
            m_career = generated
        else:
            return {"status": "error", "message": "Could not identify or generate this career path."}

    # Fetch Isolated Progress
    completed = db_get_completed_milestones(username, m_key)

    # Autonomous Learning & Level Promotion
    skills, learned = _promote_skills(skills, completed, m_career.get("roadmap", []))
    roadmap_len = len(m_career.get("roadmap", []))
    local_progress = len(completed) / max(roadmap_len, 1)
    updated_exp, promo_reason = _promote_experience(exp_level.lower(), local_progress)

    # Skill Gaps
    req_set = set(s.lower() for s in m_career.get("skills", []))
    missing = sorted(req_set - set(skills))
    match_pct = int((len(req_set - set(missing)) / max(len(req_set), 1)) * 100)

    career_data = load_career_data()
    pivot = _detect_pivots(skills, m_key, match_pct, career_data)

    # 3. Decide & Build Roadmap
    readiness = "Master" if match_pct >= 90 else "Ready" if match_pct >= 75 else "Learning"

    # Rank-Aware Strategic Guidance
    guidance_map = {
        "beginner": f"Status: Foundational mission. Your priority is mastering the core syntax and basic principles of the {m_career.get('title', m_key)} sector to ensure long-term orbital survival.",
        "intermediate": f"Status: Practitioner mission. You have established launch capabilities; focus on system integration and building a diverse portfolio of {m_career.get('title', m_key)} projects.",
        "advanced": f"Status: Architectural mission. Strategic oversight is required. Focus on high-scale resilience, industrial deployment, and lead-engineering the {m_career.get('title', m_key)} ecosystem."
    }
    expert_guidance = guidance_map.get(exp_level.lower(), f"Continue toward the {m_key} sector.")
    next_action = f"Focus on {missing[0].title()}" if missing else "Mission Ready: Initiate deployment!"

    # Industrial Slicing: Skip fundamentals for higher experience levels
    original_steps = m_career.get("roadmap", [])
    if exp_level.lower() == "advanced":
        active_steps = original_steps[3:]
    elif exp_level.lower() == "intermediate":
        active_steps = original_steps[1:]
    else:
        active_steps = original_steps

    roadmap_steps = []
    for i, step in enumerate(active_steps, 1):
        m_hash = hashlib.md5(step.lower().strip().encode()).hexdigest()[:8]
        m_id = f"ms_{username}_{m_career.get('title', m_key)}_{m_hash}"
        step_is_done = m_id in completed
        roadmap_steps.append({"index": i, "text": step, "completed": step_is_done, "id": m_id})

    # 4. Final Response
    obs = f"System Update: Added {', '.join(learned)}" if learned else None
    if promo_reason:
        obs = (obs + " | " if obs else "") + f"Rank-up: {updated_exp.title()}"

    return {
        "status": "success",
        "key": m_key,
        "title": m_career.get("title", m_key),
        "match_percentage": match_pct,
        "recommendation": m_career.get("title", m_key),
        "reasoning": f"Alignment: {match_pct}%",
        "readiness_summary": readiness,
        "expert_guidance": expert_guidance,
        "focus_area": "Upskilling",
        "next_action": next_action,
        "pivot_summary": f"Pivot suggestion: {pivot['title']}" if pivot else None,
        "pivot_justification": f"Skills match {pivot['title']} better (+{pivot['advantage']}%)" if pivot else None,
        "missing_skills": missing,
        "learned_skills": learned,
        "updated_skills": skills,
        "updated_experience_level": updated_exp,
        "agent_observation": obs,
        "roadmap_labeled": roadmap_steps,
        "total_steps": roadmap_len,
        "resources": m_career.get("resources", []),
        "career_skills": list(req_set),
        "thinking_trail": [{"name": "Agent Intelligence", "detail": f"Processed {m_key}", "duration_ms": round((time.perf_counter() - t_start) * 1000, 1)}]
    }

def get_network_data(user_skills_raw, exp_level="Beginner"):
    career_data = load_career_data()
    user_skills = set(clean_input(user_skills_raw))

    # Seniority Multiplier (Advanced users have stronger 'pull')
    gravity_mult = 0.7 if exp_level.lower() == "advanced" else 0.85 if exp_level.lower() == "intermediate" else 1.0

    careers = list(career_data.items())
    num_careers = len(careers)
    results = []

    for i, (key, data) in enumerate(careers):
        req_set = set(s.lower() for s in data.get("skills", []))
        if not req_set:
            continue

        match_pct = int((len(user_skills & req_set) / max(len(req_set), 1)) * 100)
        base_r = 100 - match_pct
        radius = 15 + (base_r * 0.8 * gravity_mult)
        angle = (i / num_careers) * 360

        # Difficulty is relative to rank
        adj_match = match_pct + (30 if exp_level.lower() == "advanced" else 15 if exp_level.lower() == "intermediate" else 0)
        difficulty = "Safe" if adj_match > 80 else "Challenging" if adj_match > 45 else "Hostile"

        results.append({
            "title": data.get("title", key),
            "match": match_pct,
            "r": radius,
            "theta": angle,
            "difficulty": data.get("difficulty", difficulty),
            "salary": data.get("avg_salary", "Unknown"),
            "demand": data.get("market_demand", 0),
            "missing": list(req_set - user_skills)[:5]
        })
    return results

def get_all_careers():
    data = load_career_data()
    return sorted([d.get("title", k) for k, d in data.items()])

def get_career_by_title(title):
    return db_get_career_by_title(title)

def compare_careers(title_a, title_b, skills_raw):
    c_a, c_b = get_career_by_title(title_a), get_career_by_title(title_b)
    if not c_a or not c_b:
        return None
    u_skills = set(clean_input(skills_raw))
    s_a = set(s.lower() for s in c_a["skills"])
    s_b = set(s.lower() for s in c_b["skills"])
    m_a = len(u_skills & s_a) / len(s_a)
    m_b = len(u_skills & s_b) / len(s_b)
    rec = title_a if m_a >= m_b else title_b
    return {
        "recommended": rec,
        "justification": f"Better fit with {int(max(m_a, m_b) * 100)}% alignment.",
        "match_a": m_a, "match_b": m_b,
        "effort_a": len(s_a - u_skills), "effort_b": len(s_b - u_skills),
        "strength": "strong" if abs(m_a - m_b) > 0.1 else "moderate"
    }
