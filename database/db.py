import sqlite3
import os
import json

# Database file path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "career_mapper.db")
USERS_JSON_PATH = os.path.join(BASE_DIR, "data", "users.json")

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
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create profiles table
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

    # Create audit_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            event TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    # Run migration once if users.json exists and has data
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
    cursor = conn.cursor()

    migrated_count = 0
    for username, user_data in data.items():
        username = username.strip()
        email = user_data.get("email", "").strip()
        password_hash = user_data.get("password_hash", "")

        # Skip if user already migrated
        exists = cursor.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            continue

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            user_id = cursor.lastrowid

            # Migrate profile data
            profile = user_data.get("profile", {})
            career_result = profile.get("career_result")
            roadmap_progress = profile.get("roadmap_progress")

            cursor.execute("""
                INSERT INTO profiles (user_id, career_goal, experience_level, current_skills, career_result, roadmap_progress)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                profile.get("career_goal"),
                profile.get("experience_level"),
                profile.get("current_skills"),
                json.dumps(career_result) if career_result else None,
                json.dumps(roadmap_progress) if roadmap_progress else None
            ))

            # Log the migration event
            cursor.execute(
                "INSERT INTO audit_logs (username, event) VALUES (?, ?)",
                (username, "MIGRATED_FROM_JSON")
            )
            migrated_count += 1
        except Exception:
            continue

    conn.commit()
    conn.close()

    if migrated_count > 0:
        print(f"[DB] Migrated {migrated_count} user(s) from users.json to SQLite.")
