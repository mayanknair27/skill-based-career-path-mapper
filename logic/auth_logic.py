import hashlib
import json
from database.db import get_connection, initialize_database

# Initialize DB on import
initialize_database()

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def _log_event(username, event):
    """Writes a security event to the audit_logs table."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_logs (username, event) VALUES (?, ?)",
        (username, event)
    )
    conn.commit()
    conn.close()

def create_user(username, email, password):
    """Creates a new user account."""
    conn = get_connection()
    cursor = conn.cursor()

    username = username.strip()
    email = email.strip()

    # Check for duplicate username
    if cursor.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
        conn.close()
        return False, "Username already exists."

    # Check for duplicate email
    if cursor.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
        conn.close()
        return False, "Email already registered."

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, _hash_password(password))
        )
        user_id = cursor.lastrowid
        # Create an empty profile row
        cursor.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
        conn.commit()
        _log_event(username, "SIGNUP")
        return True, "Account created successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Registration error: {str(e)}"
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticates a user by username and password."""
    username = username.strip()
    conn = get_connection()
    user = conn.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if not user:
        _log_event(username, "LOGIN_FAILED")
        return False, "Invalid username or password."

    if user["password_hash"] == _hash_password(password):
        _log_event(username, "LOGIN_SUCCESS")
        return True, "Login successful."

    _log_event(username, "LOGIN_FAILED")
    return False, "Invalid username or password."

def reset_password(username, email, new_password):
    """Resets a user's password after verifying their email."""
    username = username.strip()
    email = email.strip()
    conn = get_connection()
    user = conn.execute(
        "SELECT id FROM users WHERE username = ? AND email = ?", (username, email)
    ).fetchone()

    if not user:
        conn.close()
        return False, "Username and email do not match our records."

    conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (_hash_password(new_password), username)
    )
    conn.commit()
    conn.close()
    _log_event(username, "PASSWORD_RESET")
    return True, "Password reset successfully."

def get_user_profile(username):
    """Returns the career profile for a given user."""
    username = username.strip()
    conn = get_connection()
    profile = conn.execute("""
        SELECT p.career_goal, p.experience_level, p.current_skills, p.career_result, p.roadmap_progress
        FROM profiles p
        JOIN users u ON p.user_id = u.id
        WHERE u.username = ?
    """, (username,)).fetchone()
    conn.close()

    if not profile:
        return {}

    result = {}
    if profile["career_goal"]:
        result["career_goal"] = profile["career_goal"]
    if profile["experience_level"]:
        result["experience_level"] = profile["experience_level"]
    if profile["current_skills"]:
        result["current_skills"] = profile["current_skills"]
    if profile["career_result"]:
        try:
            result["career_result"] = json.loads(profile["career_result"])
        except Exception:
            pass
    if profile["roadmap_progress"]:
        try:
            result["roadmap_progress"] = json.loads(profile["roadmap_progress"])
        except Exception:
            pass
    return result

def save_user_profile(username, profile_keys):
    """Merges new profile data with existing profile for a given user."""
    username = username.strip()

    # Load existing data
    existing = get_user_profile(username)
    existing.update(profile_keys)

    career_result = existing.get("career_result")
    roadmap_progress = existing.get("roadmap_progress")

    conn = get_connection()
    conn.execute("""
        UPDATE profiles SET
            career_goal = ?,
            experience_level = ?,
            current_skills = ?,
            career_result = ?,
            roadmap_progress = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = (SELECT id FROM users WHERE username = ?)
    """, (
        existing.get("career_goal"),
        existing.get("experience_level"),
        existing.get("current_skills"),
        json.dumps(career_result) if career_result else None,
        json.dumps(roadmap_progress) if roadmap_progress else None,
        username
    ))
    conn.commit()
    conn.close()
    return True
