import re

def clean_input(user_input):
    """Cleans user input by lowercasing and splitting skills."""
    if not user_input:
        return []
    if isinstance(user_input, list):
        user_input = ",".join(user_input)
    # Split by comma or newline and strip whitespace
    skills = [s.strip().lower() for s in re.split(r'[,\n]+', user_input) if s.strip()]
    return skills

def calculate_match_percentage(user_skills, required_skills):
    """Calculates the percentage of required skills the user has."""
    if not required_skills:
        return 0
    
    user_skills_set = set(clean_input(user_skills))
    required_skills_set = set([s.lower() for s in required_skills])
    
    match_count = len(user_skills_set.intersection(required_skills_set))
    percentage = (match_count / len(required_skills_set)) * 100
    return int(percentage)

def get_missing_skills(user_skills, required_skills):
    """Identifies skills the user is missing."""
    user_skills_set = set(clean_input(user_skills))
    required_skills_set = set([s.lower() for s in required_skills])
    
    missing = required_skills_set - user_skills_set
    return list(missing)
