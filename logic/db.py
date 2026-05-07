import sqlite3
import hashlib
import os
import json

# Database file path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "career_mapper.db")
USERS_JSON_PATH = os.path.join(BASE_DIR, "data", "users.json")


# ─── Connection & Schema ───

def get_connection():
    """Returns a SQLite connection with foreign key support enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database():
    """Creates all tables if they don't exist and runs one-time migration."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                career_goal TEXT,
                experience_level TEXT,
                current_skills TEXT,
                career_result TEXT,
                roadmap_progress TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                event TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS careers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                avg_salary TEXT,
                market_demand INTEGER,
                difficulty TEXT,
                skills TEXT, -- JSON string
                roadmap TEXT, -- JSON string
                resources TEXT, -- JSON string
                is_ai_generated INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                career_key TEXT NOT NULL,
                milestone_id TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, career_key, milestone_id)
            )
        """)
        conn.commit()
    finally:
        conn.close()
    _migrate_from_json()

def _migrate_from_json():
    """One-time migration: copies users.json data into SQLite if not already done."""
    if not os.path.exists(USERS_JSON_PATH):
        return
    try:
        with open(USERS_JSON_PATH, "r") as f:
            data = json.load(f)
    except Exception:
        return
    if not data:
        return

    conn = get_connection()
    try:
        cursor = conn.cursor()
        for username, user_data in data.items():
            username = username.strip()
            email = user_data.get("email", "").strip()
            password_hash = user_data.get("password_hash", "")
            if cursor.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
                continue
            try:
                cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, password_hash))
                user_id = cursor.lastrowid
                profile = user_data.get("profile", {})
                career_result = profile.get("career_result")
                roadmap_progress = profile.get("roadmap_progress")
                cursor.execute("""
                    INSERT INTO profiles (user_id, career_goal, experience_level, current_skills, career_result, roadmap_progress)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, profile.get("career_goal"), profile.get("experience_level"), profile.get("current_skills"),
                      json.dumps(career_result) if career_result else None, json.dumps(roadmap_progress) if roadmap_progress else None))
                cursor.execute("INSERT INTO audit_logs (username, event) VALUES (?, ?)", (username, "MIGRATED_FROM_JSON"))
            except Exception:
                continue
        conn.commit()
    finally:
        conn.close()





# ─── Helpers ───

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def _log_event(username, event):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO audit_logs (username, event) VALUES (?, ?)", (username, event))
        conn.commit()
    finally:
        conn.close()


# ─── Authentication ───

def create_user(username, email, password):
    username, email = username.strip(), email.strip()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if cursor.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            return False, "Username already exists."
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
    username = username.strip()
    conn = get_connection()
    try:
        user = conn.execute("SELECT password_hash FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()
    if user and user["password_hash"] == _hash_password(password):
        _log_event(username, "LOGIN_SUCCESS")
        return True, "Login successful."
    _log_event(username, "LOGIN_FAILED")
    return False, "Invalid username or password."

def reset_password(username, email, new_password):
    username, email = username.strip(), email.strip()
    conn = get_connection()
    try:
        user = conn.execute("SELECT id FROM users WHERE username = ? AND email = ?", (username, email)).fetchone()
        if not user:
            return False, "User mismatch."
        conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (_hash_password(new_password), username))
        conn.commit()
    finally:
        conn.close()
    _log_event(username, "PASSWORD_RESET")
    return True, "Success."


# ─── Profiles ───

def get_user_profile(username):
    conn = get_connection()
    try:
        profile = conn.execute("""
            SELECT p.career_goal, p.experience_level, p.current_skills, p.career_result, p.roadmap_progress
            FROM profiles p JOIN users u ON p.user_id = u.id WHERE u.username = ?
        """, (username.strip(),)).fetchone()
    finally:
        conn.close()
    if not profile:
        return {}
    res = {"career_goal": profile["career_goal"], "experience_level": profile["experience_level"], "current_skills": profile["current_skills"]}
    try:
        if profile["career_result"]:
            res["career_result"] = json.loads(profile["career_result"])
        if profile["roadmap_progress"]:
            data = json.loads(profile["roadmap_progress"])
            if isinstance(data, dict) and "agent_state" in data:
                res["agent_state"] = data["agent_state"]
                res["roadmap_progress"] = {k: v for k, v in data.items() if k != "agent_state"}
            else:
                res["roadmap_progress"] = data
    except Exception:
        pass
    return res

def save_user_profile(username, profile_keys):
    username = username.strip()
    existing = get_user_profile(username)
    existing.update(profile_keys)
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE profiles SET career_goal=?, experience_level=?, current_skills=?, career_result=?, roadmap_progress=?, updated_at=CURRENT_TIMESTAMP
            WHERE user_id = (SELECT id FROM users WHERE username = ?)
        """, (existing.get("career_goal"), existing.get("experience_level"), existing.get("current_skills"),
              json.dumps(existing.get("career_result")),
              json.dumps({**existing.get("roadmap_progress", {}), "agent_state": existing.get("agent_state")}), username))
        conn.commit()
    finally:
        conn.close()
    return True

def db_complete_milestone(username, career_key, milestone_id):
    username = username.strip()
    conn = get_connection()
    try:
        user_row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not user_row:
            return False
        conn.execute("""
            INSERT OR IGNORE INTO user_milestones (user_id, career_key, milestone_id)
            VALUES (?, ?, ?)
        """, (user_row["id"], career_key, milestone_id))
        conn.commit()
        return True
    finally:
        conn.close()

def db_get_completed_milestones(username, career_key):
    username = username.strip()
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT milestone_id FROM user_milestones
            WHERE user_id = (SELECT id FROM users WHERE username = ?) AND career_key = ?
        """, (username, career_key)).fetchall()
        return [r["milestone_id"] for r in rows]
    finally:
        conn.close()

# ─── Admin ───

def get_recent_activity(limit=50):
    conn = get_connection()
    try:
        return [dict(l) for l in conn.execute("SELECT username, event, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()]
    finally:
        conn.close()

def get_summary_stats():
    conn = get_connection()
    try:
        return {
            "total_users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "logins_today": conn.execute("SELECT COUNT(*) FROM audit_logs WHERE event='LOGIN_SUCCESS' AND DATE(timestamp)=DATE('now')").fetchone()[0],
            "failed_today": conn.execute("SELECT COUNT(*) FROM audit_logs WHERE event='LOGIN_FAILED' AND DATE(timestamp)=DATE('now')").fetchone()[0],
            "total_signups": conn.execute("SELECT COUNT(*) FROM audit_logs WHERE event='SIGNUP'").fetchone()[0],
        }
    finally:
        conn.close()

# ─── Career Management ───

def _migrate_careers_to_db():
    """Seed DB from careers.json if empty."""
    json_path = os.path.join(BASE_DIR, "data", "careers.json")
    if not os.path.exists(json_path):
        return
    
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM careers").fetchone()[0]
        if count > 0:
            return # Already seeded
            
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for key, d in data.items():
            conn.execute("""
                INSERT OR IGNORE INTO careers (key, title, avg_salary, market_demand, difficulty, skills, roadmap, resources)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (key, d["title"], d.get("avg_salary"), d.get("market_demand"), d.get("difficulty"),
                  json.dumps(d.get("skills", [])), json.dumps(d.get("roadmap", [])), json.dumps(d.get("resources", []))))
        conn.commit()
    except Exception as e:
        print(f"Migration error (careers): {e}")
    finally:
        conn.close()

def db_get_all_careers():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT key, title, avg_salary, market_demand, difficulty, skills, roadmap, resources FROM careers").fetchall()
        result = {}
        for r in rows:
            result[r["key"]] = {
                "title": r["title"],
                "avg_salary": r["avg_salary"],
                "market_demand": r["market_demand"],
                "difficulty": r["difficulty"],
                "skills": json.loads(r["skills"]) if r["skills"] else [],
                "roadmap": json.loads(r["roadmap"]) if r["roadmap"] else [],
                "resources": json.loads(r["resources"]) if r["resources"] else []
            }
        return result
    finally:
        conn.close()

def db_get_career_by_title(title):
    conn = get_connection()
    try:
        r = conn.execute("""
            SELECT key, title, avg_salary, market_demand, difficulty, skills, roadmap, resources 
            FROM careers WHERE LOWER(title) = ? OR key = ?
        """, (title.lower(), title.lower())).fetchone()
        if not r:
            return None
        return {
            "key": r["key"],
            "title": r["title"],
            "avg_salary": r["avg_salary"],
            "market_demand": r["market_demand"],
            "difficulty": r["difficulty"],
            "skills": json.loads(r["skills"]) if r["skills"] else [],
            "roadmap": json.loads(r["roadmap"]) if r["roadmap"] else [],
            "resources": json.loads(r["resources"]) if r["resources"] else []
        }
    finally:
        conn.close()

def db_save_career(key, data, is_ai=False):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO careers (key, title, avg_salary, market_demand, difficulty, skills, roadmap, resources, is_ai_generated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (key, data["title"], data.get("avg_salary"), data.get("market_demand"), data.get("difficulty"),
              json.dumps(data.get("skills", [])), json.dumps(data.get("roadmap", [])), json.dumps(data.get("resources", [])),
              1 if is_ai else 0))
        conn.commit()
    finally:
        conn.close()


# Initialize DB on module load
initialize_database()
_migrate_careers_to_db()
