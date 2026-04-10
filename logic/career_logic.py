import json
import os
from utils.helpers import clean_input, calculate_match_percentage, get_missing_skills

def load_career_data(filepath="data/careers.json"):
    """Loads career data from JSON file."""
    try:
        # Resolve path relative to the root directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, filepath)
        with open(full_path, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_all_careers():
    """Returns a list of all available career titles for comparison."""
    career_data = load_career_data()
    titles = set()
    for _, data in career_data.items():
        title = data.get("title")
        if title:
            titles.add(title)
    return sorted(list(titles))

def get_career_by_title(title):
    career_data = load_career_data()
    for key, data in career_data.items():
        if data.get("title") == title:
            return data
    return None

def get_skill_reasoning(skill):
    """Provides a brief industry-standard justification for a skill."""
    skill_lower = skill.lower()
    reasoning = {
        "python": "Foundational for logic, automation, and core back-end functionality.",
        "javascript": "Crucial for interactive web experiences and modern full-stack development.",
        "sql": "Essential for managing and querying the data that powers every modern application.",
        "git": "Industry-standard for version control and collaborative software engineering.",
        "docker": "Key for ensuring consistent environments from development to production.",
        "aws": "Cloud infrastructure knowledge is critical for modern scalability.",
        "communication": "Vital for translating technical concepts into business value.",
        "html": "The base structure of the entire web; non-negotiable for front-end roles.",
        "css": "Responsible for the visual design and user experience of web applications.",
        "statistics": "The pillar of reliable data analysis and machine learning models.",
        "math": "Provides the algorithmic foundation for complex problem-solving.",
        "react": "Standard library for building scalable, component-based user interfaces.",
        "node.js": "Enables efficient, scalable server-side applications using JavaScript."
    }
    return reasoning.get(skill_lower, "Critical technical component required for industry-standard workflows in this role.")

def interpret_readiness(score, exp_level):
    """Translates match score into a career readiness assessment."""
    exp_factor = 1.2 if exp_level == "advanced" else 1.0 if exp_level == "intermediate" else 0.8
    effective_score = score * exp_factor
    
    if score >= 90:
        return "Market Ready: You have the technical depth to compete for top-tier roles immediately."
    elif score >= 75:
        return "Job Candidate: You meet core requirements and are ready for professional interviews."
    elif score >= 50:
        return "Transition Stage: You have a solid base but need domain-specific projects to be hireable."
    elif score >= 30:
        return "Learning Phase: You are building foundational blocks and should focus on consistency."
    else:
        return "Initiation: You are at the start of the journey; focus on mastering one core language first."

def categorize_skills(missing_skills, all_required_skills):
    """Categorizes missing skills into priority levels with reasoning."""
    if not missing_skills:
        return []
    
    foundational_cores = ["python", "javascript", "html", "css", "sql", "git", "communication", "math", "statistics"]
    
    categorized = []
    for skill in missing_skills:
        skill_lower = skill.lower()
        idx = all_required_skills.index(skill) if skill in all_required_skills else 99
        
        if skill_lower in foundational_cores:
            priority = "High"
        elif idx < len(all_required_skills) * 0.3:
            priority = "High"
        elif idx < len(all_required_skills) * 0.7:
            priority = "Medium"
        else:
            priority = "Low"
            
        categorized.append({
            "skill": skill, 
            "priority": priority,
            "reason": get_skill_reasoning(skill)
        })
        
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    categorized.sort(key=lambda x: priority_order[x["priority"]])
    return categorized

def process_career_data(goal, user_skills, experience_level):
    """Core logic to match career goal and generate roadmap with deep guidance."""
    career_data = load_career_data()
    
    goal_key = goal.strip().lower()
    
    custom_mappings = {
        "ai": "ai engineer", "ai dev": "ai engineer", "ai developer": "ai engineer",
        "ml": "machine learning engineer", "ml dev": "machine learning engineer",
        "ml engineer": "machine learning engineer", "machine learning": "machine learning engineer",
        "web": "web developer", "web dev": "web developer",
        "frontend": "frontend developer", "front-end": "frontend developer", "front end": "frontend developer",
        "backend": "backend developer", "back-end": "backend developer", "back end": "backend developer",
        "fullstack": "full stack developer", "full-stack": "full stack developer", "full stack": "full stack developer",
        "app dev": "mobile app developer", "mobile": "mobile app developer", "mobile dev": "mobile app developer",
        "ios dev": "mobile app developer", "android dev": "mobile app developer",
        "game": "game developer", "game dev": "game developer",
        "cyber": "cybersecurity analyst", "cybersecurity": "cybersecurity analyst", "security": "cybersecurity analyst",
        "devops": "devops engineer", "cloud": "cloud engineer",
        "ui": "ui/ux designer", "ux": "ui/ux designer", "ui/ux": "ui/ux designer", "ui ux": "ui/ux designer", "designer": "ui/ux designer",
        "ds": "data scientist", "data science": "data scientist", "da": "data analyst",
        "ba": "business analyst", "biz analyst": "business analyst",
        "blockchain": "blockchain developer", "crypto": "blockchain developer", "web3": "blockchain developer", "smart contract": "blockchain developer",
        "qa": "software tester (qa)", "tester": "software tester (qa)", "qa tester": "software tester (qa)",
        "sysadmin": "system administrator", "sys admin": "system administrator",
        "ar": "ar/vr developer", "vr": "ar/vr developer", "ar/vr": "ar/vr developer",
        "pm": "product manager", "product": "product manager"
    }
    
    original_input = goal_key
    goal_key = custom_mappings.get(goal_key, goal_key)
    
    career_keys_lower = {k.lower(): k for k in career_data.keys()}
    matched_key_lower = None
    is_exact_match = False
    
    if goal_key in career_keys_lower:
        matched_key_lower = goal_key
        if original_input in career_keys_lower:
            is_exact_match = True
            
    if not matched_key_lower:
        user_words = goal_key.replace("-", " ").split()
        user_tokens = set(user_words)
        best_match, best_score = None, 0
        for k_lower in career_keys_lower.keys():
            if k_lower.startswith(goal_key):
                matched_key_lower = k_lower
                break
            career_words = k_lower.replace("-", " ").replace("/", " ").split()
            career_tokens = set(career_words)
            overlap = len(user_tokens.intersection(career_tokens))
            if user_words and career_words and user_words[0] == career_words[0]:
                overlap += 2
            if overlap > best_score:
                best_score, best_match = overlap, k_lower
        if not matched_key_lower and best_score > 0:
            matched_key_lower = best_match

    if not matched_key_lower:
        import difflib
        close_matches = difflib.get_close_matches(goal_key, career_keys_lower.keys(), n=1, cutoff=0.5)
        if close_matches:
            matched_key_lower = close_matches[0]
            
    if not matched_key_lower:
        return {"status": "error", "message": "Career goal not found in our database. Try another profession."}
    
    original_key = career_keys_lower[matched_key_lower]
    matched_career = career_data[original_key]
    cleaned_user_skills = clean_input(user_skills)
    required_skills = matched_career["skills"]
    match_percentage = calculate_match_percentage(cleaned_user_skills, required_skills)
    missing_skills = get_missing_skills(cleaned_user_skills, required_skills)
    
    # Categorize skills with reasoning
    categorized_missing = categorize_skills(missing_skills, required_skills)
    most_impactful = next((s["skill"] for s in categorized_missing if s["priority"] == "High"), None)
    impact_reason = next((s["reason"] for s in categorized_missing if s["priority"] == "High"), None)
    if not most_impactful and categorized_missing:
        most_impactful = categorized_missing[0]["skill"]
        impact_reason = categorized_missing[0]["reason"]

    original_roadmap = matched_career.get("roadmap", [])
    filtered_roadmap, steps_skipped = [], False
    
    beginner_keywords = ["basic", "fundamental", "understand", "intro", "learn", "study"]
    advanced_keywords = ["build", "project", "apply", "deploy", "internship", "portfolio", "practice", "create", "architect", "real-world", "master"]
    
    user_skills_set = set([s.lower() for s in cleaned_user_skills])
    required_skills_set = set([s.lower() for s in required_skills])
    known_required_skills = required_skills_set.intersection(user_skills_set)
    exp_level_lower = experience_level.lower() if experience_level else "beginner"
    
    for step in original_roadmap:
        step_lower = step.lower()
        mentions_known = any(ks in step_lower for ks in known_required_skills)
        mentions_missing = any(ms in step_lower for ms in missing_skills)
        is_advanced_step = any(kw in step_lower for kw in advanced_keywords)
        is_beginner_step = any(kw in step_lower for kw in beginner_keywords)
        
        if mentions_known and not mentions_missing and not is_advanced_step:
            steps_skipped = True
            continue
        if exp_level_lower == "advanced" and not is_advanced_step:
            steps_skipped = True
            continue
        elif exp_level_lower == "intermediate" and (is_beginner_step and not mentions_missing):
            steps_skipped = True
            continue
        filtered_roadmap.append(step)
        
    if exp_level_lower == "advanced" and len(filtered_roadmap) < 2:
        title = matched_career.get("title", "this role")
        filtered_roadmap.extend([f"Architect and deploy a production-grade {title} application", f"Prepare for senior-level technical interviews and system design rounds for {title} roles"])
            
    if not filtered_roadmap:
        filtered_roadmap = original_roadmap

    # Directional Roadmap Labels
    roadmap_with_labels = []
    for idx, step in enumerate(filtered_roadmap):
        step_lower = step.lower()
        label = ""
        if idx == 0:
            label = "[START HERE] "
        elif any(kw in step_lower for kw in ["project", "deploy", "portfolio", "practice"]):
            label = "[CRITICAL MILESTONE] "
        roadmap_with_labels.append(f"{label}{step}")

    # Readiness & Guidance
    readiness_interpretation = interpret_readiness(match_percentage, exp_level_lower)
    focus_area, next_action = "", ""
    if match_percentage >= 80:
        focus_area = "Advanced Mastery & Portfolio."
        next_action = "Execute a final end-to-end production project to validate your seniority."
    elif match_percentage >= 40:
        focus_area = f"Bridge the Domain Gap with {most_impactful.title() if most_impactful else 'core skills'}."
        next_action = f"Complete a targeted module on {most_impactful.title() if most_impactful else 'the missing link'} this week."
    else:
        focus_area = "Foundational Logic & Core Syntax."
        next_action = "Master the basics before touching any frameworks. Focus on one core language."

    expert_guidance = readiness_interpretation + " "
    if match_percentage >= 80:
         expert_guidance += "Your depth allows you to focus on architectural nuance rather than syntax. Prioritize system design."
    elif match_percentage >= 40:
         expert_guidance += "The transition is feasible but requires shift from generalist to specialist knowledge."
    else:
         expert_guidance += "Be patient with the fundamentals; they are the strongest predictors of long-term success."

    return {
        "status": "success",
        "title": matched_career.get("title", original_key),
        "is_exact_match": is_exact_match,
        "match_percentage": match_percentage,
        "readiness_summary": readiness_interpretation,
        "missing_skills": missing_skills,
        "categorized_missing": categorized_missing,
        "most_impactful_skill": most_impactful,
        "impact_reason": impact_reason,
        "roadmap": roadmap_with_labels,
        "steps_skipped": steps_skipped,
        "resources": matched_career.get("resources", []),
        "expert_guidance": expert_guidance,
        "focus_area": focus_area,
        "next_action": next_action
    }
