import streamlit as st
import time
import os
from dotenv import load_dotenv
from logic.agent import process_career_data, get_all_careers, get_career_by_title, compare_careers
from logic.users import create_user, authenticate_user, reset_password, get_user_profile, save_user_profile, \
                        get_recent_activity, get_failed_logins, get_summary_stats, get_all_users
from logic.utils import load_css

# Initialize environment
load_dotenv()

# 1. Page Configuration
st.set_page_config(
    page_title=os.getenv("APP_TITLE", "Skill-Based Career Path Mapper"),
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Premium Deep Purple Theme
load_css("assets/css/style.css")

# ---------------------------------------------
# AUTHENTICATION (unchanged)
# ---------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "login"

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Welcome to Career Mapper</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.auth_view == "login":
            st.markdown("<p style='text-align: center; color:rgba(255,255,255,0.6); font-size:1.05rem; margin-top:5px;'>Please authenticate to continue.</p>", unsafe_allow_html=True)
            with st.form("login_form"):
                st.markdown("<h3 style='text-align: center; margin-bottom: 25px;'>Secure Access</h3>", unsafe_allow_html=True)
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", type="primary", use_container_width=True)

                if submit:
                    success, msg = authenticate_user(username, password)
                    if success:
                        stale_keys = [k for k in st.session_state.keys() if k not in ["logged_in", "auth_view"]]
                        for k in stale_keys:
                            del st.session_state[k]

                        st.session_state.logged_in = True
                        st.session_state.username = username
                        profile = get_user_profile(username)
                        if "career_goal" in profile:
                            st.session_state.career_goal_input = profile["career_goal"]
                        if "experience_level" in profile:
                            st.session_state.experience_level_input = profile["experience_level"]
                        if "current_skills" in profile:
                            st.session_state.current_skills_input = profile["current_skills"]
                        if "career_result" in profile:
                            st.session_state.career_result = profile["career_result"]
                        if "agent_state" in profile:
                            st.session_state.agent_state = profile["agent_state"]
                        if "roadmap_progress" in profile:
                            for key, val in profile["roadmap_progress"].items():
                                st.session_state[key] = val
                        st.rerun()
                    else:
                        st.error(msg)

            c1, c2 = st.columns(2)
            if c1.button("Create an account", use_container_width=True):
                st.session_state.auth_view = "signup"
                st.rerun()
            if c2.button("Forgot Password", use_container_width=True):
                st.session_state.auth_view = "forgot"
                st.rerun()

        elif st.session_state.auth_view == "signup":
            st.markdown("<p style='text-align: center; color:rgba(255,255,255,0.6); font-size:1.05rem; margin-top:5px;'>Create a new account.</p>", unsafe_allow_html=True)
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align: center; margin-bottom: 25px;'>Sign Up</h3>", unsafe_allow_html=True)
                username = st.text_input("Username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm = st.text_input("Confirm Password", type="password")
                submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)

                if submit:
                    if not username or not email or not password:
                        st.error("Please fill in all fields.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        success, msg = create_user(username, email, password)
                        if success:
                            st.success(msg + " You can now log in.")
                            time.sleep(1)
                            st.session_state.auth_view = "login"
                            st.rerun()
                        else:
                            st.error(msg)

            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_view = "login"
                st.rerun()

        elif st.session_state.auth_view == "forgot":
            st.markdown("<p style='text-align: center; color:rgba(255,255,255,0.6); font-size:1.05rem; margin-top:5px;'>Reset your password.</p>", unsafe_allow_html=True)
            with st.form("forgot_form"):
                st.markdown("<h3 style='text-align: center; margin-bottom: 25px;'>Account Recovery</h3>", unsafe_allow_html=True)
                username = st.text_input("Username")
                email = st.text_input("Registered Email")
                new_password = st.text_input("New Password", type="password")
                submit = st.form_submit_button("Reset Password", type="primary", use_container_width=True)

                if submit:
                    if not username or not email or not new_password:
                        st.error("Please fill in all fields.")
                    else:
                        success, msg = reset_password(username, email, new_password)
                        if success:
                            st.success(msg)
                            time.sleep(1)
                            st.session_state.auth_view = "login"
                            st.rerun()
                        else:
                            st.error(msg)

            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_view = "login"
                st.rerun()

    st.stop()

# ---------------------------------------------
# MAIN UI — AGENT-DRIVEN
# ---------------------------------------------
st.markdown("<h1>Skill-Based Career Path Mapper</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:1.05rem; margin-top:5px;'>An agent-driven system that actively guides your career progression.</p>", unsafe_allow_html=True)

RESOURCE_LINKS = {
    "python": "https://www.python.org/about/gettingstarted/",
    "html": "https://developer.mozilla.org/en-US/docs/Web/HTML",
    "css": "https://developer.mozilla.org/en-US/docs/Web/CSS",
    "javascript": "https://javascript.info/",
    "react": "https://react.dev/",
    "node.js": "https://nodejs.org/en/learn/",
    "sql": "https://www.w3schools.com/sql/",
    "statistics": "https://www.khanacademy.org/math/statistics-probability",
    "machine learning": "https://www.coursera.org/learn/machine-learning",
    "data visualization": "https://www.tableau.com/learn/training",
    "deep learning": "https://www.deeplearning.ai/",
    "system design": "https://github.com/donnemartin/system-design-primer",
    "mlops": "https://ml-ops.org/",
    "pytorch": "https://pytorch.org/tutorials/"
}

# Initialize agent state
if "agent_state" not in st.session_state:
    st.session_state.agent_state = {"completed_steps": [], "previous_recommendations": []}

# Sidebar Configuration
with st.sidebar:
    col_lock, col_logout = st.columns([2, 1])
    with col_logout:
        if st.button("Logout", key="logout_btn", help="End session", use_container_width=True):
            keys_to_clear = [k for k in st.session_state.keys() if k not in ["logged_in", "auth_view"]]
            for k in keys_to_clear:
                del st.session_state[k]
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("<h3>Configuration</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:0.9rem;'>Enter your details below to activate the guidance agent.</p>", unsafe_allow_html=True)

    career_goal = st.text_input("Desired Role", value=st.session_state.get("career_goal_input", ""), placeholder="e.g., Data Scientist")

    exp_levels = ["Beginner", "Intermediate", "Advanced"]
    saved_exp = st.session_state.get("experience_level_input", "Beginner")
    default_idx = exp_levels.index(saved_exp) if saved_exp in exp_levels else 0

    experience_level = st.selectbox("Experience Level", exp_levels, index=default_idx)

    current_skills = st.text_area("Current Skills", value=st.session_state.get("current_skills_input", ""), placeholder="e.g., Python, HTML, Node.js", height=100)

    generate_btn = st.button("Activate Agent", type="primary")

# =============================================
# AGENT PIPELINE EXECUTION
# =============================================
if generate_btn:
    if not career_goal:
        st.sidebar.error("Error: Please enter a desired career goal.")
    else:
        agent_state = st.session_state.get("agent_state", {})

        # ── VISIBLE AGENT THINKING ──
        status_container = st.empty()
        thinking_placeholder = st.container()

        with thinking_placeholder:
            st.markdown("""
            <div style="background: rgba(124, 58, 237, 0.08); border: 1px solid #4C3C8A; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom: 16px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#7C3AED;animation:pulse 1.5s infinite;"></div>
                    <span style="color:#C4B5FD; font-weight:700; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.1em;">Agent Pipeline Active</span>
                </div>
            """, unsafe_allow_html=True)

            # Stage 1: Observe
            step1 = st.empty()
            step1.markdown("&nbsp;&nbsp;&nbsp;&nbsp;`[1/5]` **OBSERVE** — Collecting and normalizing user profile...", unsafe_allow_html=True)
            time.sleep(0.5)

            # Stage 2: Analyze
            step2 = st.empty()
            step2.markdown("&nbsp;&nbsp;&nbsp;&nbsp;`[2/5]` **ANALYZE** — Matching career pathways and scoring skills...", unsafe_allow_html=True)
            time.sleep(0.5)

            # Actually run the pipeline
            result = process_career_data(career_goal, current_skills, experience_level, agent_state)

            # Stage 3: Decide
            step3 = st.empty()
            step3.markdown("&nbsp;&nbsp;&nbsp;&nbsp;`[3/5]` **DECIDE** — Determining optimal career alignment...", unsafe_allow_html=True)
            time.sleep(0.4)

            # Stage 4: Act
            step4 = st.empty()
            step4.markdown("&nbsp;&nbsp;&nbsp;&nbsp;`[4/5]` **ACT** — Building dynamic roadmap...", unsafe_allow_html=True)
            time.sleep(0.4)

            # Stage 5: Adapt
            step5 = st.empty()
            step5.markdown("&nbsp;&nbsp;&nbsp;&nbsp;`[5/5]` **ADAPT** — Tailoring output to your experience level...", unsafe_allow_html=True)
            time.sleep(0.3)

            if result["status"] == "error":
                st.markdown("</div>", unsafe_allow_html=True)
                st.error(result.get("message", "Career not found. Try variations like 'Data Scientist' or 'Web Developer'."))
                st.stop()
            else:
                # Show real thinking trail results
                if result.get("thinking_trail"):
                    for step in result["thinking_trail"]:
                        if step:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ _{step['detail']}_ `({step['duration_ms']}ms)`")

                st.markdown("</div>", unsafe_allow_html=True)

                st.session_state.career_result = result
                st.session_state.current_skills_input = current_skills
                st.session_state.career_goal_input = career_goal
                st.session_state.experience_level_input = experience_level

                # Track recommendation
                agent_state["previous_recommendations"] = agent_state.get("previous_recommendations", [])
                if result["title"] not in agent_state["previous_recommendations"]:
                    agent_state["previous_recommendations"].append(result["title"])
                st.session_state.agent_state = agent_state

                # Save profile
                if "username" in st.session_state:
                    save_user_profile(st.session_state.username, {
                        "career_goal": career_goal,
                        "experience_level": experience_level,
                        "current_skills": current_skills,
                        "career_result": result,
                        "agent_state": agent_state,
                    })

        time.sleep(0.5)
        st.rerun()

# =============================================
# DISPLAY TABS
# =============================================
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip().lower()
IS_ADMIN = st.session_state.get("username", "").strip().lower() == ADMIN_USERNAME and ADMIN_USERNAME != ""

tab_labels = ["My Career Plan", "Compare Careers"]
if IS_ADMIN:
    tab_labels.append("Admin Panel")

tabs = st.tabs(tab_labels)
tab1 = tabs[0]
tab2 = tabs[1]
tab3 = tabs[2] if IS_ADMIN else None


# =============================================
# HELPER: Recalculate next action from roadmap
# =============================================
def _get_live_next_action(result):
    """Recalculates the next action based on current step completion state."""
    labeled = result.get("roadmap_labeled", [])
    title = result.get("title", "")
    for step_data in labeled:
        key = f"step_{title}_{step_data['index']}"
        if not st.session_state.get(key, False):
            return step_data["text"]
    return None  # all done


def _get_live_completed_count(result):
    """Counts how many steps are currently checked."""
    labeled = result.get("roadmap_labeled", [])
    title = result.get("title", "")
    count = 0
    for step_data in labeled:
        key = f"step_{title}_{step_data['index']}"
        if st.session_state.get(key, False):
            count += 1
    return count


# =============================================
# TAB 1: MY CAREER PLAN
# =============================================
with tab1:
    if "career_result" in st.session_state:
        result = st.session_state.career_result
        current_skills_val = st.session_state.get("current_skills_input", "")

        # Live recalculation
        live_next_step = _get_live_next_action(result)
        live_completed = _get_live_completed_count(result)
        total_steps = result.get("total_steps", len(result.get("roadmap", [])))
        live_progress = live_completed / max(total_steps, 1)

        if not result.get("is_exact_match", True):
            st.warning(f"No exact match found. Closest role: **{result['title']}**")

        # ── AGENT STATUS HEADER ──
        agent_state = st.session_state.get("agent_state", {})
        prev_recs = agent_state.get("previous_recommendations", [])
        session_note = ""
        if len(prev_recs) > 1:
            session_note = f" | Careers explored: {', '.join(prev_recs)}"

        st.markdown(f"""
        <div style="background: rgba(124,58,237,0.06); border:1px solid #4C3C8A; border-radius:12px;
                    padding:14px 20px; margin-bottom:18px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div>
                <span style="color:#A78BFA; font-weight:700; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em;">Agent Status</span>
                <span style="color:#6EE7B7; font-size:0.75rem; margin-left:10px; font-weight:600;">● Active</span>
            </div>
            <div style="color:#94A3B8; font-size:0.8rem;">
                Target: <b style="color:#F1F5F9;">{result['title']}</b> |
                Match: <b style="color:#F1F5F9;">{result['match_percentage']}%</b> |
                Progress: <b style="color:#F1F5F9;">{int(live_progress*100)}%</b>
                {session_note}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── PIVOT INTERVENTION ──
        if result.get("pivot_summary"):
            st.markdown(f"""
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 18px; margin-bottom: 20px;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom: 8px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#F59E0B;animation:pulse 1.5s infinite;"></div>
                    <span style="color:#FBBF24; font-weight:700; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.1em;">Strategic Pivot Recommendation</span>
                </div>
                <div style="color:#F1F5F9; font-size:1rem; font-weight:600; margin-bottom:6px;">{result['pivot_summary']}</div>
                <div style="color:#D1D5DB; font-size:0.9rem; line-height:1.5;">{result['pivot_justification']}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── SILENT DASHBOARD OBSERVATION ──
        if result.get("agent_observation"):
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.05); border-left: 4px solid #10B981; padding: 12px 16px; margin-bottom: 20px; border-radius: 0 8px 8px 0;">
                <p style="color: #6EE7B7; font-size: 0.88rem; margin: 0; font-weight: 500;">{result['agent_observation']}</p>
            </div>
            """, unsafe_allow_html=True)

        # ── 1. NEXT ACTION (recalculated live) ──
        decision_action = result.get("next_action", "Start the first roadmap step.")

        if live_progress >= 1.0:
            action_color = "#6EE7B7"
            action_icon = "&#x2705;"
            action_text = f"All {total_steps} roadmap steps completed. You are ready to apply for {result['title']} roles."
            step_text = ""
        else:
            action_color = "#64FFDA"
            action_icon = "&#x1F3AF;"
            action_text = decision_action
            step_text = f'<div style="color: #94A3B8; font-size: 0.85rem; margin-top: 6px;">Next roadmap step: <b style="color:#F1F5F9;">{live_next_step}</b></div>' if live_next_step else ""

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(100, 255, 218, 0.06), rgba(56, 189, 248, 0.06));
                    border: 1px solid rgba(100, 255, 218, 0.25); border-radius: 12px; padding: 16px 20px; margin-bottom: 20px;">
            <div style="font-weight: 700; font-size: 0.8rem; color: {action_color}; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px;">
                {action_icon} Next Action
            </div>
            <div style="color: #F1F5F9; font-size: 1.05rem; font-weight: 600; line-height: 1.5;">
                {action_text}
            </div>
            {step_text}
        </div>
        """, unsafe_allow_html=True)

        percentage = result["match_percentage"]
        missing_skills = result.get("missing_skills", [])
        user_skills_list = [s.strip() for s in current_skills_val.split(",") if s.strip()]
        user_skills_count = len(user_skills_list)
        missing_count = len(missing_skills)

        # ── 2. METRICS ──
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.markdown(f"""
            <div class="dashboard-card">
                <div class="metric-label">Profile Match</div>
                <div class="metric-value">{percentage}%</div>
                <div style="margin-top: 8px; font-size: 0.85rem; color: #94A3B8;">{result.get('readiness_summary', result['title'])}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="dashboard-card">
                <div class="metric-label">Skills Acquired</div>
                <div class="metric-value">{user_skills_count}</div>
                <div style="margin-top: 8px; font-size: 0.85rem; color: #94A3B8;">Core Foundations</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="dashboard-card">
                <div class="metric-label">Missing Gaps</div>
                <div class="metric-value" style="color: #FCA5A5;">{missing_count}</div>
                <div style="margin-top: 8px; font-size: 0.85rem; color: #94A3B8;">{missing_count} Priority Areas</div>
            </div>
            """, unsafe_allow_html=True)

        # ── 3. AGENT RECOMMENDATION + REASONING ──
        recommendation = result.get("recommendation", result["title"])
        reasoning = result.get("reasoning", "")
        expert_guidance = result.get("expert_guidance", "")
        focus_area = result.get("focus_area", "General foundation building.")

        st.markdown(f"""
        <div class="info-box">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
                <div style="width:8px;height:8px;border-radius:50%;background:#7C3AED;"></div>
                <span style="color: #A78BFA; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight:700;">Agent Recommendation</span>
            </div>
            <h4 style="margin: 0 0 10px 0; color: #F8FAFC; font-size: 1.2rem;">{recommendation}</h4>
            <p style="margin: 0 0 10px 0; color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">
                <b style="color: #C4B5FD;">Reasoning:</b> {reasoning}
            </p>
            <p style="margin: 8px 0; color: #F1F5F9; font-size: 0.95rem; line-height: 1.5;">
                {expert_guidance}
            </p>
            <div style="margin-top:12px; padding-top:10px; border-top:1px solid #334155;">
                <span style="color: #64FFDA; font-weight:600; font-size:0.9rem;">Current Focus:</span>
                <span style="color: #F1F5F9; font-size:0.9rem;"> {focus_area}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 4. SKILL GAP ANALYSIS ──
        st.markdown("<h3 style='margin-top:20px;'>Skill Gap Analysis</h3>", unsafe_allow_html=True)
        if result.get("categorized_missing"):
            # Priority chips
            chips_html = ""
            for item in result["categorized_missing"]:
                p_class = f"priority-{item['priority'].lower()}"
                chips_html += f'<span class="{p_class}" style="margin-right: 8px; margin-bottom: 8px; display: inline-block;">{item["skill"].title()} ({item["priority"]})</span>'
            st.markdown(f'<div style="margin-bottom: 1.5rem;">{chips_html}</div>', unsafe_allow_html=True)

            # Detailed skill breakdown
            for item in result["categorized_missing"]:
                if item["priority"] == "High":
                    bar_color = "#EF4444"
                elif item["priority"] == "Medium":
                    bar_color = "#F59E0B"
                else:
                    bar_color = "#10B981"

                st.markdown(f"""
                <div style="background: rgba(15,10,30,0.5); border:1px solid #2D264D; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#F1F5F9; font-weight:600; font-size:0.9rem;">{item['skill'].title()}</span>
                        <span style="color:{bar_color}; font-weight:700; font-size:0.75rem; text-transform:uppercase;">{item['priority']} Priority</span>
                    </div>
                    <p style="color:#94A3B8; font-size:0.82rem; margin:4px 0 0 0;">{item['reason']}</p>
                </div>
                """, unsafe_allow_html=True)

            # Most impactful
            most_impactful = result.get("most_impactful_skill", "N/A")
            impact_reason = result.get("impact_reason", "Crucial technical component.")
            st.markdown(f"""
            <div style="background: rgba(56, 189, 248, 0.05); border-radius: 8px; padding: 12px; margin-top: 10px; border: 1px dashed #334155;">
                <p style="color: #38BDF8; font-size: 0.9rem; margin-bottom: 4px; font-weight: 600;">&#x1F680; Most Critical Skill: {most_impactful.title() if most_impactful else 'N/A'}</p>
                <p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 0;">{impact_reason}</p>
            </div>
            """, unsafe_allow_html=True)
        elif missing_skills:
            chips_html = "".join([f'<span class="priority-medium" style="margin-right: 8px;">{skill.title()}</span>' for skill in missing_skills])
            st.markdown(f'<div style="margin-bottom: 2rem;">{chips_html}</div>', unsafe_allow_html=True)

            st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:0.95rem; font-weight:500;'>Recommended Learning Material:</p>", unsafe_allow_html=True)
            for skill in missing_skills:
                if skill.lower() in RESOURCE_LINKS:
                    st.markdown(f"- **{skill.title()}**: [View Documentation]({RESOURCE_LINKS[skill.lower()]})")
        else:
            st.success("You meet all core skill requirements for this role.")

        if result.get("resources"):
            with st.expander("Role-Specific External Resources"):
                for resource in result["resources"]:
                    st.markdown(f"- [{resource['name']}]({resource['url']})")

        st.markdown("<hr style='border:1px solid rgba(122,40,255,0.2); margin: 30px 0;'>", unsafe_allow_html=True)

        # ── 5. DYNAMIC ROADMAP WITH LIVE ADAPTATION ──
        st.markdown("<h3>Actionable Roadmap</h3>", unsafe_allow_html=True)

        if result.get("steps_skipped"):
            st.markdown("<p style='color:rgba(255,255,255,0.5); font-size:0.9rem; margin-bottom:15px; font-weight:400;'><i>The agent omitted foundational steps based on your existing skills and experience level.</i></p>", unsafe_allow_html=True)

        # Live progress (recalculated from actual checkbox state)
        if total_steps > 0:
            # Gamification status
            if live_progress >= 1.0:
                progress_status = "&#x1F3C6; **Ready to Apply!** You've completed all steps in this roadmap."
            elif live_progress >= 0.75:
                progress_status = "&#x1F680; **Almost there!** You have the core down, focus on polish."
            elif live_progress >= 0.5:
                progress_status = "&#x1F4C8; **Great Momentum!** You've covered half the path."
            elif live_progress > 0:
                progress_status = "&#x1F331; **Good start!** Keep building consistency."
            else:
                progress_status = "Begin your roadmap below. Check steps as you complete them."

            st.markdown(f"<p style='color:#38BDF8; font-weight:600; margin-bottom: 4px;'>{progress_status}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#94A3B8; font-size: 0.85rem;'>{int(live_progress*100)}% Complete ({live_completed}/{total_steps} steps)</p>", unsafe_allow_html=True)
            st.progress(live_progress)

        st.markdown("<br>", unsafe_allow_html=True)

        def save_progress():
            """Saves roadmap progress + agent state and triggers autonomous learning."""
            if "username" in st.session_state and "career_result" in st.session_state:
                res = st.session_state.career_result
                tot = res.get("total_steps", len(res.get("roadmap", [])))
                progress = {}
                completed_list = []
                for idx in range(1, tot + 1):
                    k = f"step_{res['title']}_{idx}"
                    if k in st.session_state:
                        progress[k] = st.session_state[k]
                        if st.session_state[k]:
                            completed_list.append(k)

                agent_st = st.session_state.get("agent_state", {})
                agent_st["completed_steps"] = completed_list
                st.session_state.agent_state = agent_st

                # --- AUTONOMOUS LEARNING TRIGGER ---
                # Re-run pipeline in background to see if skills were learned
                goal = st.session_state.get("career_goal_input", "")
                skills = st.session_state.get("current_skills_input", "")
                exp = st.session_state.get("experience_level_input", "Beginner")

                new_result = process_career_data(goal, skills, exp, agent_st)
                if new_result.get("status") == "success":
                    # Update skills if agent learned something
                    if new_result.get("updated_skills"):
                        joined_skills = ", ".join(new_result["updated_skills"])
                        st.session_state.current_skills_input = joined_skills
                    
                    # Update experience level if agent promoted user
                    if new_result.get("updated_experience_level"):
                        promoted = new_result["updated_experience_level"].capitalize()
                        if promoted in ["Beginner", "Intermediate", "Advanced"]:
                            st.session_state.experience_level_input = promoted
                    
                    st.session_state.career_result = new_result

                save_user_profile(st.session_state.username, {
                    "career_goal": goal,
                    "experience_level": st.session_state.experience_level_input,
                    "current_skills": st.session_state.get("current_skills_input", skills),
                    "roadmap_progress": progress,
                    "agent_state": agent_st,
                })

        # Render labeled roadmap steps
        roadmap_labeled = result.get("roadmap_labeled", [])
        if roadmap_labeled:
            for step_data in roadmap_labeled:
                i = step_data["index"]
                text = step_data["text"]
                tier = step_data.get("tier", "applied")
                key = f"step_{result['title']}_{i}"
                is_done = st.session_state.get(key, False)

                # Determine live label
                if is_done:
                    prefix = "[DONE]"
                    tier_badge = ""
                elif live_next_step and text == live_next_step:
                    prefix = "[CURRENT FOCUS]"
                    tier_badge = f'<span style="background:rgba(56,189,248,0.15);color:#38BDF8;padding:1px 6px;border-radius:4px;font-size:0.7rem;font-weight:600;margin-left:8px;">{tier.upper()}</span>'
                elif i == 1 and not any(st.session_state.get(f"step_{result['title']}_{j}", False) for j in range(1, len(roadmap_labeled)+1)):
                    prefix = "[START HERE]"
                    tier_badge = ""
                else:
                    prefix = "[UPCOMING]"
                    tier_badge = ""

                st.checkbox(
                    f"{prefix} Step {i}: {text}",
                    key=key,
                    on_change=save_progress,
                )
        else:
            for i, step in enumerate(result.get("roadmap", []), 1):
                st.checkbox(f"Step {i}: {step}", key=f"step_{result['title']}_{i}", on_change=save_progress)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── AGENT MEMORY PANEL ──
        with st.expander("Agent Memory & State", expanded=False):
            agent_state = st.session_state.get("agent_state", {})
            completed_list = agent_state.get("completed_steps", [])
            prev = agent_state.get("previous_recommendations", [])

            st.markdown(f"""
            **Completed Steps:** {len(completed_list)} of {total_steps}

            **Careers Explored:** {', '.join(prev) if prev else 'None yet'}

            **Current Target:** {result['title']}

            **Experience Level:** {st.session_state.get('experience_level_input', 'N/A')}

            **Pivot Recommended:** {"Yes (interrupt active)" if result.get('pivot_summary') else "No"}

            **Autonomous Findings:** 
            - Learned Skills: {', '.join(result.get('learned_skills', [])) or 'None in this session'}
            - Promotion Status: {result.get('updated_experience_level', 'N/A').title()}

            **Adaptation Note:** The Agent now takes full initiative. When you check a box, it performs a background re-analysis, updates your skill profile, and evaluates if a career pivot or level rank-up is warranted.
            """)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── DOWNLOAD ──
        md_content = f"# Career Plan: {result['title']}\n\n"
        md_content += f"**Assessment Readiness:** {result.get('readiness_summary', 'N/A')}\n"
        md_content += f"**Match Score:** {percentage}% | **Progress:** {int(live_progress*100)}% Complete\n\n"
        md_content += f"## Agent Recommendation\n"
        md_content += f"**Career:** {result.get('recommendation', result['title'])}\n"
        md_content += f"**Reasoning:** {result.get('reasoning', 'N/A')}\n"
        md_content += f"- **Focus Area:** {result.get('focus_area', 'N/A')}\n"
        md_content += f"- **Next Action:** {result.get('next_action', 'N/A')}\n\n"
        md_content += f"## Expert Guidance\n{result.get('expert_guidance', '')}\n\n"
        md_content += f"## Skill Gap Analysis\n"
        if result.get("categorized_missing"):
            for item in result["categorized_missing"]:
                priority_emoji = "HIGH" if item['priority'] == "High" else "MED" if item['priority'] == "Medium" else "LOW"
                md_content += f"- [{priority_emoji}] **{item['skill'].title()}**: {item.get('reason', 'Essential requirement.')}\n"
        elif missing_skills:
            for skill in missing_skills:
                md_content += f"- [ ] {skill.title()}\n"
        else:
            md_content += "No critical gaps.\n"

        md_content += f"\n## Progression Roadmap\n"
        if roadmap_labeled:
            for step_data in roadmap_labeled:
                i = step_data["index"]
                is_checked = "[x]" if st.session_state.get(f"step_{result['title']}_{i}", False) else "[ ]"
                md_content += f"{is_checked} Step {i}: {step_data['text']}\n"
        else:
            for i, step in enumerate(result.get("roadmap", []), 1):
                is_checked = "[x]" if st.session_state.get(f"step_{result['title']}_{i}", False) else "[ ]"
                md_content += f"{is_checked} Step {i}: {step}\n"

        md_content += f"\n---\n*Generated by Career Mapper Agent Pipeline*"

        col_d1, col_d2, col_d3 = st.columns([1, 2, 1])
        with col_d2:
            st.download_button(
                label="Download Progression Plan",
                data=md_content,
                file_name="career_plan.md",
                mime="text/markdown",
                use_container_width=True
            )
    else:
        # No results yet — show agent idle state
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px;">
            <div style="font-size: 3rem; margin-bottom: 16px;">&#x1F916;</div>
            <h3 style="color: #C4B5FD; margin-bottom: 8px;">Agent Idle</h3>
            <p style="color: #94A3B8; font-size: 0.95rem; max-width: 450px; margin: 0 auto;">
                Enter your desired role and current skills in the sidebar, then click <b>"Activate Agent"</b> to start the guided career analysis pipeline.
            </p>
        </div>
        """, unsafe_allow_html=True)


# =============================================
# TAB 2: COMPARE CAREERS
# =============================================
with tab2:
    st.markdown("<h3>Career Comparison Analysis</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6); font-weight:400;'>The agent evaluates two career tracks and makes an opinionated recommendation based on your profile.</p>", unsafe_allow_html=True)

    all_careers = get_all_careers()

    if len(all_careers) >= 2:
        comp_col1, comp_col2 = st.columns(2)

        with comp_col1:
            career_1 = st.selectbox("First Career Track", all_careers, index=0)
        with comp_col2:
            career_2 = st.selectbox("Second Career Track", all_careers, index=min(1, len(all_careers)-1))

        data_1 = get_career_by_title(career_1)
        data_2 = get_career_by_title(career_2)

        if data_1 and data_2:
            user_skills_raw = st.session_state.get("current_skills_input", "").strip()
            comparison = compare_careers(career_1, career_2, user_skills_raw)

            if comparison and user_skills_raw:
                # Agent decision header
                st.markdown("""
                <div style="display:flex; align-items:center; gap:8px; margin:16px 0 10px 0;">
                    <div style="width:8px;height:8px;border-radius:50%;background:#7C3AED;"></div>
                    <span style="color: #A78BFA; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight:700;">Agent Decision</span>
                </div>
                """, unsafe_allow_html=True)

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown(f"<p style='margin-bottom:2px; font-size:0.9rem; color:#94A3B8;'>{career_1} Alignment</p>", unsafe_allow_html=True)
                    st.progress(comparison["match_a"])
                with col_m2:
                    st.markdown(f"<p style='margin-bottom:2px; font-size:0.9rem; color:#94A3B8;'>{career_2} Alignment</p>", unsafe_allow_html=True)
                    st.progress(comparison["match_b"])

                st.markdown("<br>", unsafe_allow_html=True)

                strength = comparison["strength"]
                if strength == "strong":
                    st.success(f"**Agent Recommendation: {comparison['recommended']}**")
                elif strength == "moderate":
                    st.info(f"**Slight Edge: {comparison['recommended']}**")
                else:
                    st.info(f"**Marginal Edge: {comparison['recommended']}**")

                st.markdown(comparison["justification"])

                st.markdown(f"""
                <div style="background: rgba(124, 58, 237, 0.05); border-radius: 8px; padding: 12px; margin-top: 10px; border: 1px dashed #334155;">
                    <p style="color: #A78BFA; font-size: 0.85rem; margin-bottom: 4px; font-weight: 600;">Effort Comparison</p>
                    <p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 0;">
                        <b>{career_1}:</b> {comparison['effort_a']} skill(s) to learn &nbsp;|&nbsp;
                        <b>{career_2}:</b> {comparison['effort_b']} skill(s) to learn
                    </p>
                </div>
                """, unsafe_allow_html=True)

            elif not user_skills_raw:
                st.markdown("""
                <div class="info-box">
                    <p style="color: #94A3B8; margin: 0;">Enter your current skills in the sidebar and activate the agent to get an opinionated recommendation between these two career paths.</p>
                </div>
                """, unsafe_allow_html=True)

            # Skill breakdown
            skills_1 = set([s.lower() for s in data_1.get("skills", [])])
            skills_2 = set([s.lower() for s in data_2.get("skills", [])])
            common_skills = skills_1.intersection(skills_2)
            unique_1 = skills_1 - skills_2
            unique_2 = skills_2 - skills_1

            if common_skills:
                st.markdown(f"""
                <div class="dashboard-card" style="padding:20px; margin-top:20px; margin-bottom:10px; background: rgba(56, 189, 248, 0.05); border-left: 4px solid #38BDF8;">
                    <div style="font-weight:700; font-size:0.85rem; color:#38BDF8; margin-bottom:4px; text-transform:uppercase; letter-spacing:0.05em;">Shared Foundations</div>
                    <div style="color:#F1F5F9; font-size:1rem; font-weight:500;">{", ".join([s.title() for s in common_skills])}</div>
                </div>
                """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <div class="dashboard-card">
                    <div style="font-weight:700; font-size:0.8rem; color:#94A3B8; border-bottom:1px solid #334155; margin-bottom:12px; padding-bottom:8px; text-transform:uppercase;">Unique to {career_1}</div>
                    <div style="color:#F1F5F9; font-size:1rem; line-height:1.6; font-weight:400;">
                        {", ".join([s.title() for s in unique_1]) if unique_1 else "No unique core skills"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"Standard {career_1} Path", expanded=False):
                    for i, step in enumerate(data_1.get("roadmap", []), 1):
                        st.markdown(f"<p style='color:#94A3B8; font-size:0.9rem;'><b>Step {i}:</b> {step}</p>", unsafe_allow_html=True)

            with col_b:
                st.markdown(f"""
                <div class="dashboard-card">
                    <div style="font-weight:700; font-size:0.8rem; color:#94A3B8; border-bottom:1px solid #334155; margin-bottom:12px; padding-bottom:8px; text-transform:uppercase;">Unique to {career_2}</div>
                    <div style="color:#F1F5F9; font-size:1rem; line-height:1.6; font-weight:400;">
                        {", ".join([s.title() for s in unique_2]) if unique_2 else "No unique core skills"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"Standard {career_2} Path", expanded=False):
                    for i, step in enumerate(data_2.get("roadmap", []), 1):
                        st.markdown(f"<p style='color:#94A3B8; font-size:0.9rem;'><b>Step {i}:</b> {step}</p>", unsafe_allow_html=True)
    else:
        st.warning("Insufficient career data points loaded into the database.")


# =============================================
# TAB 3: ADMIN PANEL (unchanged)
# =============================================
if IS_ADMIN and tab3 is not None:
    with tab3:
        st.markdown("<h3>Security & User Monitoring</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:rgba(255,255,255,0.5);'>Real-time audit trail — visible only to admin.</p>", unsafe_allow_html=True)

        stats = get_summary_stats()
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="dashboard-card" style="text-align:center;">
                <div class="metric-label">Total Users</div>
                <div class="metric-value">{stats['total_users']}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="dashboard-card" style="text-align:center;">
                <div class="metric-label">Logins Today</div>
                <div class="metric-value" style="color:#6EE7B7;">{stats['logins_today']}</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="dashboard-card" style="text-align:center;">
                <div class="metric-label">Failed Today</div>
                <div class="metric-value" style="color:#FCA5A5;">{stats['failed_today']}</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""
            <div class="dashboard-card" style="text-align:center;">
                <div class="metric-label">Total Signups</div>
                <div class="metric-value" style="color:#A78BFA;">{stats['total_signups']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<h4>Live Audit Log</h4>", unsafe_allow_html=True)
        logs = get_recent_activity(limit=50)
        if logs:
            for log in logs:
                event = log["event"]
                ts = log["timestamp"]
                user = log["username"]
                if event == "LOGIN_FAILED":
                    badge = "<span style='background:rgba(239,68,68,0.15);color:#FCA5A5;padding:2px 8px;border-radius:12px;font-size:0.78rem;font-weight:600;'>FAILED</span>"
                elif event == "LOGIN_SUCCESS":
                    badge = "<span style='background:rgba(16,185,129,0.15);color:#6EE7B7;padding:2px 8px;border-radius:12px;font-size:0.78rem;font-weight:600;'>SUCCESS</span>"
                elif event == "SIGNUP":
                    badge = "<span style='background:rgba(124,58,237,0.15);color:#A78BFA;padding:2px 8px;border-radius:12px;font-size:0.78rem;font-weight:600;'>SIGNUP</span>"
                else:
                    badge = f"<span style='background:rgba(148,163,184,0.1);color:#94A3B8;padding:2px 8px;border-radius:12px;font-size:0.78rem;font-weight:600;'>{event}</span>"

                st.markdown(
                    f"<div style='padding:8px 12px;border-bottom:1px solid #2D264D;display:flex;gap:16px;align-items:center;'>"
                    f"<span style='color:#64748B;font-size:0.8rem;min-width:160px;'>{ts}</span>"
                    f"<span style='color:#F1F5F9;font-weight:600;min-width:120px;'>{user}</span>"
                    f"{badge}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No audit events recorded yet.")

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("Registered Users"):
            all_users = get_all_users()
            if all_users:
                for u in all_users:
                    st.markdown(
                        f"<div style='padding:6px 12px;border-bottom:1px solid #2D264D;'>"
                        f"<b style='color:#A78BFA;'>{u['username']}</b> "
                        f"<span style='color:#64748B; font-size:0.85rem;'>— {u['email']} &nbsp;|&nbsp; Joined: {u['created_at']}</span></div>",
                        unsafe_allow_html=True
                    )

        with st.expander("Failed Login Attempts"):
            failed = get_failed_logins()
            if failed:
                for log in failed:
                    st.markdown(
                        f"<div style='padding:6px 12px;border-bottom:1px solid #2D264D;color:#FCA5A5;'>"
                        f"<b>{log['username']}</b> <span style='color:#64748B; font-size:0.85rem;'>— {log['timestamp']}</span></div>",
                        unsafe_allow_html=True
                    )
            else:
                st.success("No failed login attempts recorded.")
