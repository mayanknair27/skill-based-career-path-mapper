from database.db import get_connection

def get_recent_activity(limit=50):
    """Returns the most recent N audit log events."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT username, event, timestamp
        FROM audit_logs
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_failed_logins():
    """Returns all failed login attempts."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT username, event, timestamp
        FROM audit_logs
        WHERE event = 'LOGIN_FAILED'
        ORDER BY timestamp DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_user_activity(username):
    """Returns all audit events for a specific user."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT username, event, timestamp
        FROM audit_logs
        WHERE username = ?
        ORDER BY timestamp DESC
    """, (username,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_summary_stats():
    """Returns high-level security metrics for the admin dashboard."""
    conn = get_connection()
    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_logins_today = conn.execute("""
        SELECT COUNT(*) as c FROM audit_logs
        WHERE event = 'LOGIN_SUCCESS' AND DATE(timestamp) = DATE('now')
    """).fetchone()["c"]
    failed_today = conn.execute("""
        SELECT COUNT(*) as c FROM audit_logs
        WHERE event = 'LOGIN_FAILED' AND DATE(timestamp) = DATE('now')
    """).fetchone()["c"]
    total_signups = conn.execute("""
        SELECT COUNT(*) as c FROM audit_logs WHERE event = 'SIGNUP'
    """).fetchone()["c"]
    conn.close()

    return {
        "total_users": total_users,
        "logins_today": total_logins_today,
        "failed_today": failed_today,
        "total_signups": total_signups
    }

def get_all_users():
    """Returns a list of all registered users with timestamps."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT username, email, created_at FROM users ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]
