import streamlit as st
import time
from logic.users import create_user, authenticate_user, reset_password, get_user_profile, save_user_profile
from logic.agent import process_career_data

# --- Constants & Static Data ---

RESOURCE_LINKS = {
    "python": "https://www.python.org/about/gettingstarted/",
    "html": "https://developer.mozilla.org/en-US/docs/Web/HTML",
    "css": "https://developer.mozilla.org/en-US/docs/Web/CSS",
    "javascript": "https://javascript.info/",
    "react": "https://react.dev/", "node.js": "https://nodejs.org/en/learn/",
    "sql": "https://www.w3schools.com/sql/", "statistics": "https://www.khanacademy.org/math/statistics-probability",
    "machine learning": "https://www.coursera.org/learn/machine-learning",
}

# --- Shared UI Components ---

def render_metric_card(label, value, subtext="", color="#F1F5F9"):
    st.markdown(f"""
    <div class="dashboard-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {color};">{value}</div>
        <div style="margin-top: 8px; font-size: 0.85rem; color: #94A3B8;">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

def render_agent_status(title, match, progress, notes=""):
    st.markdown(f"""
    <div style="background: rgba(124,58,237,0.06); border:1px solid #4C3C8A; border-radius:12px;
                padding:14px 20px; margin-bottom:18px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span style="color:#A78BFA; font-weight:700; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em;">Agent Active</span>
            <span style="color:#6EE7B7; font-size:0.75rem; margin-left:10px; font-weight:600;">● Online</span>
        </div>
        <div style="color:#94A3B8; font-size:0.8rem;">
            Target: <b style="color:#F1F5F9;">{title}</b> | Match: <b style="color:#F1F5F9;">{match}%</b> | Progress: <b style="color:#F1F5F9;">{progress}%</b> {notes}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Section Renderers ---

def render_auth_section():
    if "auth_view" not in st.session_state: st.session_state.auth_view = "login"
    st.markdown("<br><br><h1 style='text-align: center;'>Welcome to Career Mapper</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1.5, 2, 1.5])
    
    with col:
        st.markdown("<br>", unsafe_allow_html=True)
        view = st.session_state.auth_view
        
        if view == "login":
            st.markdown("<p style='text-align: center; color:rgba(255,255,255,0.6); font-size:1.05rem;'>Secure Access</p>", unsafe_allow_html=True)
            with st.form("login_form"):
                u, p = st.text_input("Username"), st.text_input("Password", type="password")
                if st.form_submit_button("Login", type="primary", use_container_width=True):
                    success, msg = authenticate_user(u, p)
                    if success:
                        for k in list(st.session_state.keys()): 
                            if k not in ["logged_in", "auth_view"]: del st.session_state[k]
                        st.session_state.logged_in, st.session_state.username = True, u
                        profile = get_user_profile(u)
                        st.session_state.update({
                            "career_goal_input": profile.get("career_goal", ""),
                            "experience_level_input": profile.get("experience_level", "Beginner"),
                            "current_skills_input": profile.get("current_skills", ""),
                            "career_result": profile.get("career_result"),
                            "agent_state": profile.get("agent_state"),
                        })
                        for k, v in profile.get("roadmap_progress", {}).items(): st.session_state[k] = v
                        st.rerun()
                    else: st.error(msg)
            c1, c2 = st.columns(2)
            if c1.button("Create Account", use_container_width=True): st.session_state.auth_view = "signup"; st.rerun()
            if c2.button("Forgot Password", use_container_width=True): st.session_state.auth_view = "forgot"; st.rerun()
            
        elif view == "signup":
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align: center;'>Sign Up</h3>", unsafe_allow_html=True)
                u, e, p, c = st.text_input("Username"), st.text_input("Email"), st.text_input("Password", type="password"), st.text_input("Confirm", type="password")
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    if p != c: st.error("Passwords mismatch.")
                    else:
                        ok, msg = create_user(u, e, p)
                        if ok: st.success("Created! Redirecting..."); time.sleep(1); st.session_state.auth_view = "login"; st.rerun()
                        else: st.error(msg)
            if st.button("Back to Login", use_container_width=True): st.session_state.auth_view = "login"; st.rerun()

def render_agent_thinking(career_goal, current_skills, exp_level):
    with st.container():
        st.markdown('<div style="background: rgba(124, 58, 237, 0.08); border: 1px solid #4C3C8A; border-radius: 12px; padding: 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
        st.markdown('<div style="display:flex; align-items:center; gap:10px; margin-bottom: 16px;"><div style="width:10px;height:10px;border-radius:50%;background:#7C3AED;animation:pulse 1.5s infinite;"></div><span style="color:#C4B5FD; font-weight:700; font-size:0.85rem; text-transform:uppercase;">Agent Pipeline Active</span></div>', unsafe_allow_html=True)
        
        placeholders = [st.empty() for _ in range(5)]
        stages = ["OBSERVE — Normalizing profile...", "ANALYZE — Scoring skills...", "DECIDE — Aligning career...", "ACT — Building roadmap...", "ADAPT — Personalizing data..."]
        
        for i, text in enumerate(stages):
            placeholders[i].markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;`[{i+1}/5]` **{text}**")
            time.sleep(0.3)
            
        res = process_career_data(career_goal, current_skills, exp_level, st.session_state.get("agent_state", {}))
        
        if res.get("thinking_trail"):
            for step in res["thinking_trail"]:
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ _{step['detail']}_ `({step['duration_ms']}ms)`")
        st.markdown("</div>", unsafe_allow_html=True)
        return res

def render_dashboard_tab(result):
    # Status & Alerts
    render_agent_status(result['title'], result['match_percentage'], int((result.get('live_progress', 0))*100))
    
    if result.get("pivot_summary"):
        st.markdown(f'<div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 18px; margin-bottom: 20px;"><div style="color:#FBBF24; font-weight:700; font-size:0.85rem; text-transform:uppercase;">Strategic Pivot Recommended</div><div style="color:#F1F5F9; font-size:1rem; font-weight:600;">{result["pivot_summary"]}</div><div style="color:#D1D5DB; font-size:0.9rem;">{result["pivot_justification"]}</div></div>', unsafe_allow_html=True)

    if result.get("agent_observation"):
        st.markdown(f'<div style="background: rgba(16, 185, 129, 0.05); border-left: 4px solid #10B981; padding: 12px 16px; margin-bottom: 20px; border-radius: 0 8px 8px 0;"><p style="color: #6EE7B7; font-size: 0.88rem; margin: 0; font-weight: 500;">{result["agent_observation"]}</p></div>', unsafe_allow_html=True)

    # Metrics
    c1, c2, c3 = st.columns(3)
    with c1: render_metric_card("Profile Match", f"{result['match_percentage']}%", result.get('readiness_summary', 'Learning'))
    with c2: render_metric_card("Skills Acquired", len(st.session_state.get("current_skills_input", "").split(",")), "Core Foundations")
    with c3: render_metric_card("Missing Gaps", len(result.get("missing_skills", [])), "Priority Areas", "#FCA5A5")

    # Recommendation
    st.markdown(f"""
    <div class="info-box">
        <span style="color: #A78BFA; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight:700;">Agent Recommendation</span>
        <h4 style="margin: 5px 0 10px 0; color: #F8FAFC;">{result.get('recommendation', result['title'])}</h4>
        <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;"><b>Reasoning:</b> {result.get('reasoning', '')}</p>
        <p style="color: #F1F5F9; font-size: 0.95rem;">{result.get('expert_guidance', '')}</p>
    </div>
    """, unsafe_allow_html=True)

def render_skill_gaps(result):
    st.markdown("<h3>Skill Gap Analysis</h3>", unsafe_allow_html=True)
    gaps = result.get("categorized_missing", [])
    if gaps:
        for item in gaps:
            color = "#EF4444" if item['priority'] == "High" else "#F59E0B" if item['priority'] == "Medium" else "#10B981"
            st.markdown(f'<div style="background: rgba(15,10,30,0.5); border:1px solid #2D264D; border-radius:8px; padding:10px 14px; margin-bottom:8px;"><div style="display:flex; justify-content:space-between;"><b>{item["skill"].title()}</b><span style="color:{color}; font-size:0.75rem; font-weight:700;">{item["priority"].upper()} PRIORITY</span></div><p style="color:#94A3B8; font-size:0.82rem; margin:4px 0 0 0;">{item["reason"]}</p></div>', unsafe_allow_html=True)
    elif result.get("missing_skills"):
        for s in result["missing_skills"]:
            if s.lower() in RESOURCE_LINKS: st.markdown(f"- **{s.title()}**: [View Documentation]({RESOURCE_LINKS[s.lower()]})")
    else: st.success("No critical skill gaps detected.")

def render_roadmap(result, save_callback):
    st.markdown("<h3>Actionable Roadmap</h3>", unsafe_allow_html=True)
    steps = result.get("roadmap_labeled", [])
    total = result.get("total_steps", len(steps))
    done = sum(1 for s in steps if st.session_state.get(f"step_{result['title']}_{s['index']}", False))
    prog = done / max(total, 1)
    
    st.markdown(f"<p style='color:#38BDF8; font-weight:600; margin-bottom: 4px;'>{int(prog*100)}% Complete ({done}/{total} steps)</p>", unsafe_allow_html=True)
    st.progress(prog)
    st.markdown("<br>", unsafe_allow_html=True)
    
    for s in steps:
        key = f"step_{result['title']}_{s['index']}"
        st.checkbox(f"Step {s['index']}: {s['text']}", key=key, on_change=save_callback)

def render_comparison():
    from logic.agent import get_all_careers, get_career_by_title, compare_careers
    st.markdown("<h3>Career Comparison</h3>", unsafe_allow_html=True)
    all_c = get_all_careers()
    if len(all_c) < 2: return st.info("Not enough careers to compare.")
    
    c1, c2 = st.columns(2)
    with c1: car1 = st.selectbox("Track 1", all_c, index=0)
    with c2: car2 = st.selectbox("Track 2", all_c, index=1)
    
    skills = st.session_state.get("current_skills_input", "")
    comp = compare_careers(car1, car2, skills)
    if comp:
        st.write(f"**Agent Recommends: {comp['recommended']}**")
        st.progress(comp["match_a"])
        st.progress(comp["match_b"])
        st.markdown(comp["justification"])

def render_admin():
    from logic.users import get_summary_stats, get_recent_activity
    st.markdown("<h3>Security & Audit Panel</h3>", unsafe_allow_html=True)
    stats = get_summary_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Users", stats["total_users"])
    with c2: st.metric("Logins", stats["logins_today"])
    with c3: st.metric("Failures", stats["failed_today"], delta_color="inverse")
    with c4: st.metric("Signups", stats["total_signups"])
    
    st.table(get_recent_activity(20))
