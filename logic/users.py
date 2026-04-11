import hashlib
import json
from logic.db import get_connection, initialize_database

# Initialize DB on import
initialize_database()

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def _log_event(username, event):
    """Writes a security event to the audit_logs table."""
    conn = get_connection()
    conn.execute("INSERT INTO audit_logs (username, event) VALUES (?, ?)", (username, event))
    conn.commit()
    conn.close()

# --- Authentication Logic ---

def create_user(username, email, password):
    """Creates a new user account and empty profile."""
    username, email = username.strip(), email.strip()
    conn = get_connection()
    cursor = conn.cursor()
    
    if cursor.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
        conn.close()
        return False, "Username already exists."

    try:
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                       (username, email, _hash_password(password)))
        cursor.execute("INSERT INTO profiles (user_id) VALUES (?)", (cursor.lastrowid,))
        conn.commit()
        _log_event(username, "SIGNUP")
        return True, "Account created successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Registration error: {str(e)}"
    finally:
        conn.close()

def authenticate_user(username, password):
    """Verifies credentials."""
    username = username.strip()
    conn = get_connection()
    user = conn.execute("SELECT password_hash FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user and user["password_hash"] == _hash_password(password):
        _log_event(username, "LOGIN_SUCCESS")
        return True, "Login successful."
    
    _log_event(username, "LOGIN_FAILED")
    return False, "Invalid username or password."

def reset_password(username, email, new_password):
    """Resets password after credential check."""
    username, email = username.strip(), email.strip()
    conn = get_connection()
    user = conn.execute("SELECT id FROM users WHERE username = ? AND email = ?", (username, email)).fetchone()
    if not user:
        conn.close()
        return False, "User mismatch."
    
    conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (_hash_password(new_password), username))
    conn.commit()
    conn.close()
    _log_event(username, "PASSWORD_RESET")
    return True, "Success."

# --- Profile & Audit Logic ---

def get_user_profile(username):
    """Retrieves full profile data, including embedded agent state."""
    conn = get_connection()
    profile = conn.execute("""
        SELECT p.career_goal, p.experience_level, p.current_skills, p.career_result, p.roadmap_progress
        FROM profiles p JOIN users u ON p.user_id = u.id WHERE u.username = ?
    """, (username.strip(),)).fetchone()
    conn.close()

    if not profile: return {}

    res = {
        "career_goal": profile["career_goal"],
        "experience_level": profile["experience_level"],
        "current_skills": profile["current_skills"]
    }
    
    try:
        if profile["career_result"]: res["career_result"] = json.loads(profile["career_result"])
        if profile["roadmap_progress"]:
            data = json.loads(profile["roadmap_progress"])
            if isinstance(data, dict) and "agent_state" in data:
                res["agent_state"] = data["agent_state"]
                res["roadmap_progress"] = {k: v for k, v in data.items() if k != "agent_state"}
            else:
                res["roadmap_progress"] = data
    except Exception: pass
    return res

def save_user_profile(username, profile_keys):
    """Persists merged profile state."""
    username = username.strip()
    existing = get_user_profile(username)
    existing.update(profile_keys)

    conn = get_connection()
    conn.execute("""
        UPDATE profiles SET career_goal=?, experience_level=?, current_skills=?, career_result=?, roadmap_progress=?, updated_at=CURRENT_TIMESTAMP
        WHERE user_id = (SELECT id FROM users WHERE username = ?)
    """, (
        existing.get("career_goal"), existing.get("experience_level"), existing.get("current_skills"),
        json.dumps(existing.get("career_result")),
        json.dumps({**existing.get("roadmap_progress", {}), "agent_state": existing.get("agent_state")}),
        username
    ))
    conn.commit()
    conn.close()
    return True

def get_recent_activity(limit=50):
    conn = get_connection()
    logs = conn.execute("SELECT username, event, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(l) for l in logs]

def get_failed_logins():
    conn = get_connection()
    logs = conn.execute("SELECT username, event, timestamp FROM audit_logs WHERE event='LOGIN_FAILED' ORDER BY timestamp DESC").fetchall()
    conn.close()
    return [dict(l) for l in logs]

def get_summary_stats():
    conn = get_connection()
    stats = {
        "total_users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "logins_today": conn.execute("SELECT COUNT(*) FROM audit_logs WHERE event='LOGIN_SUCCESS' AND DATE(timestamp)=DATE('now')").fetchone()[0],
        "failed_today": conn.execute("SELECT COUNT(*) FROM audit_logs WHERE event='LOGIN_FAILED' AND DATE(timestamp)=DATE('now')").fetchone()[0],
        "total_signups": conn.execute("SELECT COUNT(*) FROM audit_logs WHERE event='SIGNUP'").fetchone()[0]
    }
    conn.close()
    return stats

def get_all_users():
    conn = get_connection()
    users = conn.execute("SELECT username, email, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(u) for u in users]
