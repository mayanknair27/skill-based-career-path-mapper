import streamlit as st
import time
import os
from dotenv import load_dotenv
from logic.career_logic import process_career_data, get_all_careers, get_career_by_title
from logic.auth_logic import create_user, authenticate_user, reset_password, get_user_profile, save_user_profile
from logic.audit_logic import get_recent_activity, get_failed_logins, get_summary_stats, get_all_users
from utils.ui_helpers import load_css

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
# AUTHENTICATION
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
                        # Clear any stale data from a previous user's session
                        stale_keys = [k for k in st.session_state.keys() if k not in ["logged_in", "auth_view"]]
                        for k in stale_keys:
                            del st.session_state[k]

                        st.session_state.logged_in = True
                        st.session_state.username = username
                        # Load this user's saved profile from the database
                        profile = get_user_profile(username)
                        if "career_goal" in profile:
                            st.session_state.career_goal_input = profile["career_goal"]
                        if "experience_level" in profile:
                            st.session_state.experience_level_input = profile["experience_level"]
                        if "current_skills" in profile:
                            st.session_state.current_skills_input = profile["current_skills"]
                        if "career_result" in profile:
                            st.session_state.career_result = profile["career_result"]
                        # Restore step checklists
                        if "roadmap_progress" in profile:
                            for key, val in profile["roadmap_progress"].items():
                                st.session_state[key] = val
                        st.rerun()
                    else:
                        st.error(msg)
            
            # Nav buttons outside form
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
# MAIN UI FLOW
# ---------------------------------------------
st.markdown("<h1>Skill-Based Career Path Mapper</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:1.05rem; margin-top:5px;'>A structured approach to planning your career growth.</p>", unsafe_allow_html=True)

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

# Sidebar Restructuring
with st.sidebar:
    col_lock, col_logout = st.columns([2, 1])
    with col_logout:
        if st.button("Logout", key="logout_btn", help="End session", use_container_width=True):
            # Wipe all user-specific data so next login starts clean
            keys_to_clear = [k for k in st.session_state.keys() if k not in ["logged_in", "auth_view"]]
            for k in keys_to_clear:
                del st.session_state[k]
            st.session_state.logged_in = False
            st.rerun()
            
    st.markdown("<h3>Configuration</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:0.9rem;'>Enter your details below to generate a tailored progression path.</p>", unsafe_allow_html=True)
    
    career_goal = st.text_input("Desired Role", value=st.session_state.get("career_goal_input", ""), placeholder="e.g., Data Scientist")
    
    exp_levels = ["Beginner", "Intermediate", "Advanced"]
    saved_exp = st.session_state.get("experience_level_input", "Beginner")
    default_idx = exp_levels.index(saved_exp) if saved_exp in exp_levels else 0
    
    experience_level = st.selectbox("Experience Level", exp_levels, index=default_idx)

    current_skills = st.text_area("Current Skills", value=st.session_state.get("current_skills_input", ""), placeholder="e.g., Python, HTML, Node.js", height=100)

    generate_btn = st.button("Generate Career Path", type="primary")

# Execute Logic
if generate_btn:
    if not career_goal:
        st.sidebar.error("Error: Please enter a desired career goal.")
    else:
        with st.status("Analyzing your profile...", expanded=True) as status:
            st.write("Searching the catalog for matching careers...")
            time.sleep(0.4)
            st.write("Evaluating your current skill proficiencies...")
            time.sleep(0.4)
            st.write("Optimizing your personalized roadmap...")
            
            result = process_career_data(career_goal, current_skills, experience_level)
            
            time.sleep(0.4)
            if result["status"] == "error":
                status.update(label="Analysis Failed", state="error", expanded=False)
                st.error("Career not found. Try variations like 'Data Scientist' or 'Web Developer'.")
                st.stop()
            else:
                status.update(label="Career Path Generated", state="complete", expanded=False)
                st.session_state.career_result = result
                st.session_state.current_skills_input = current_skills
                
                # Save to profile
                if "username" in st.session_state:
                    save_user_profile(st.session_state.username, {
                        "career_goal": career_goal,
                        "experience_level": experience_level,
                        "current_skills": current_skills,
                        "career_result": result
                    })

# Display Tabs
# Display Tabs
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip().lower()
IS_ADMIN = st.session_state.get("username", "").strip().lower() == ADMIN_USERNAME and ADMIN_USERNAME != ""

tab_labels = ["My Career Plan", "Compare Careers"]
if IS_ADMIN:
    tab_labels.append("Admin Panel")

tabs = st.tabs(tab_labels)
tab1 = tabs[0]
tab2 = tabs[1]
tab3 = tabs[2] if IS_ADMIN else None

with tab1:
    if "career_result" in st.session_state:
        result = st.session_state.career_result
        current_skills = st.session_state.current_skills_input
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not result.get("is_exact_match", True):
            st.warning(f"No exact match found. Displaying roadmap for deepest correlated role: {result['title']}")
            
        percentage = result["match_percentage"]
        missing_skills = result["missing_skills"]
        
        # Split metrics
        user_skills_list = [s.strip() for s in current_skills.split(",") if s.strip()]
        user_skills_count = len(user_skills_list)
        missing_count = len(missing_skills)
        
        # Modern Dashboards
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
             
        # Decision Guidance: AI Insight Section
        st.markdown(f"""
        <div class="info-box">
            <h4 style="margin: 0 0 8px 0; color: #38BDF8; font-size: 1.1rem;">💡 AI Career Insight</h4>
            <p style="margin: 8px 0; color: #F1F5F9; font-size: 0.95rem; line-height: 1.5;">
                {result.get('expert_guidance', '')}
            </p>
            <p style="margin: 0; color: #F1F5F9; font-size: 0.95rem;">
                <b>Current Focus:</b> {result.get('focus_area', 'General foundation building.')}<br>
                <b>Next Action:</b> <span style="color: #64FFDA;">{result.get('next_action', 'Start the first roadmap step.')}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Missing Chips with Categorization
        st.markdown("<h3 style='margin-top:20px;'>Skill Gap Analysis</h3>", unsafe_allow_html=True)
        if result.get("categorized_missing"):
            chips_html = ""
            for item in result["categorized_missing"]:
                p_class = f"priority-{item['priority'].lower()}"
                chips_html += f'<span class="{p_class}" style="margin-right: 8px; margin-bottom: 8px; display: inline-block;">{item["skill"].title()}</span>'
            st.markdown(f'<div style="margin-bottom: 1.5rem;">{chips_html}</div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: rgba(56, 189, 248, 0.05); border-radius: 8px; padding: 12px; margin-top: 10px; border: 1px dashed #334155;">
                <p style="color: #38BDF8; font-size: 0.9rem; margin-bottom: 4px; font-weight: 600;">🚀 Most Impactful Skill: {result.get('most_impactful_skill', 'N/A').title()}</p>
                <p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 0;">{result.get('impact_reason', 'Crucial technical component.')}</p>
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
             st.markdown('<div class="success-chip" style="margin-bottom: 2rem;">You meet all core skill requirements.</div>', unsafe_allow_html=True)
             
        if result.get("resources"):
            with st.expander("Role Specific External Resources"):
                for resource in result["resources"]:
                    st.markdown(f"- [{resource['name']}]({resource['url']})")
                    
        st.markdown("<hr style='border:1px solid rgba(122,40,255,0.2); margin: 30px 0;'>", unsafe_allow_html=True)

        # Roadmap Timeline
        st.markdown("<h3>Actionable Roadmap</h3>", unsafe_allow_html=True)
        
        if result.get("steps_skipped"):
             st.markdown("<p style='color:rgba(255,255,255,0.5); font-size:0.9rem; margin-bottom:15px; font-weight:400;'><i>Selected foundational steps were omitted leveraging your existing knowledge.</i></p>", unsafe_allow_html=True)
            
        total_steps = len(result["roadmap"])
        completed_steps = 0
        
        for i in range(1, total_steps + 1):
            if st.session_state.get(f"step_{result['title']}_{i}", False):
                completed_steps += 1
                
        if total_steps > 0:
            progress_val = completed_steps / total_steps
            
            # Gamification Status Message
            status_msg = "Let's get started on your first step!"
            if progress_val == 1.0:
                 status_msg = "🏆 **Ready to Apply!** You've completed all blocks in this roadmap."
            elif progress_val >= 0.75:
                 status_msg = "🚀 **Almost there!** You have the core down, focus on polish."
            elif progress_val >= 0.5:
                 status_msg = "📈 **Great Momentum!** You've covered half the path."
            elif progress_val > 0:
                 status_msg = "🌱 **Good start!** Keep building consistency."
                 
            st.markdown(f"<p style='color:#38BDF8; font-weight:600; margin-bottom: 4px;'>{status_msg}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#94A3B8; font-size: 0.85rem;'>{int(progress_val*100)}% Complete ({completed_steps}/{total_steps} steps)</p>", unsafe_allow_html=True)
            st.progress(progress_val)
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        def save_progress():
            if "username" in st.session_state and "career_result" in st.session_state:
                res = st.session_state.career_result
                tot_steps = len(res["roadmap"])
                progress = {}
                for idx in range(1, tot_steps + 1):
                    k = f"step_{res['title']}_{idx}"
                    if k in st.session_state:
                        progress[k] = st.session_state[k]
                save_user_profile(st.session_state.username, {"roadmap_progress": progress})

        for i, step in enumerate(result["roadmap"], 1):
            st.checkbox(f"Step {i}: {step}", key=f"step_{result['title']}_{i}", on_change=save_progress)

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Download Export
        md_content = f"# 🎯 Career Plan: {result['title']}\n\n"
        md_content += f"**Assessment Readiness:** {result.get('readiness_summary', 'N/A')}\n"
        md_content += f"**Match Score:** {percentage}% | **Progress:** {int((completed_steps/total_steps)*100) if total_steps > 0 else 0}% Complete\n\n"
        
        md_content += f"## 💡 AI Career Insight\n"
        md_content += f"- **Focus Area:** {result.get('focus_area', 'N/A')}\n"
        md_content += f"- **Next Action:** {result.get('next_action', 'N/A')}\n\n"
        
        md_content += f"## 🧭 Expert Guidance\n{result.get('expert_guidance', '')}\n\n"
        
        md_content += f"## ⚠️ Priority Skill Gap Analysis\n"
        if result.get("categorized_missing"):
            for item in result["categorized_missing"]:
                priority_emoji = "🔴" if item['priority'] == "High" else "🟡" if item['priority'] == "Medium" else "🟢"
                md_content += f"- {priority_emoji} **{item['skill'].title()}** ({item['priority']} Priority)\n"
                md_content += f"  - *Impact:* {item.get('reason', 'Essential requirement.')}\n"
        elif missing_skills:
            for skill in missing_skills:
                md_content += f"- [ ] {skill.title()}\n"
        else:
            md_content += "No critical foundational gaps identified.\n"
            
        md_content += f"\n## 🗺️ Progression Roadmap\n"
        for i, step in enumerate(result["roadmap"], 1):
            is_checked = "[x]" if st.session_state.get(f"step_{result['title']}_{i}", False) else "[ ]"
            md_content += f"{is_checked} Step {i}: {step}\n"
        
        md_content += f"\n---\n*Generated by AI Skill-Based Career Mapper*"
            
        col_down1, col_down2, col_down3 = st.columns([1,2,1])
        with col_down2:
            st.download_button(
                label="Download Progression Plan",
                data=md_content,
                file_name="career_plan.md",
                mime="text/markdown",
                use_container_width=True
            )

with tab2:
    st.markdown("<h3>Career Comparison Analysis</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6); font-weight:400;'>Evaluate distinct career tracks to identify shared dependencies and unique paths.</p>", unsafe_allow_html=True)
    
    all_careers = get_all_careers()
    
    if len(all_careers) >= 2:
        comp_col1, comp_col2 = st.columns(2)
        
        with comp_col1:
            career_1 = st.selectbox("First Career Track", all_careers, index=0)
            data_1 = get_career_by_title(career_1)
        with comp_col2:
            career_2 = st.selectbox("Second Career Track", all_careers, index=min(1, len(all_careers)-1))
            data_2 = get_career_by_title(career_2)
            
        if data_1 and data_2:
            skills_1 = set([s.lower() for s in data_1.get("skills", [])])
            skills_2 = set([s.lower() for s in data_2.get("skills", [])])
            
            common_skills = skills_1.intersection(skills_2)
            unique_1 = skills_1 - skills_2
            unique_2 = skills_2 - skills_1
            
            # User alignment summary
            if "current_skills_input" in st.session_state and st.session_state.current_skills_input.strip():
                user_skills = set([s.strip().lower() for s in st.session_state.current_skills_input.split(",") if s.strip()])
                match_1 = len(user_skills.intersection(skills_1)) / len(skills_1) if skills_1 else 0
                match_2 = len(user_skills.intersection(skills_2)) / len(skills_2) if skills_2 else 0
                
                st.markdown("<h4 style='margin-top:10px; color:#FFFFFF;'>💡 Comparative Analysis</h4>", unsafe_allow_html=True)
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown(f"<p style='margin-bottom:2px; font-size:0.9rem; color:#94A3B8;'>{career_1} Alignment</p>", unsafe_allow_html=True)
                    st.progress(match_1)
                with col_m2:
                    st.markdown(f"<p style='margin-bottom:2px; font-size:0.9rem; color:#94A3B8;'>{career_2} Alignment</p>", unsafe_allow_html=True)
                    st.progress(match_2)

                st.markdown("<br>", unsafe_allow_html=True)
                if match_1 > match_2 + 0.1:
                    st.success(f"🎯 **Primary Recommendation: {career_1}**")
                    st.markdown(f"**Reason:** Closer domain proximity with `{int(match_1*100)}%` alignment. This represents a **safer transition** with fewer foundational shifts required.")
                elif match_2 > match_1 + 0.1:
                    st.success(f"🎯 **Primary Recommendation: {career_2}**")
                    st.markdown(f"**Reason:** Closer domain proximity with `{int(match_2*100)}%` alignment. This represents a **safer transition** with fewer foundational shifts required.")
                elif match_1 > match_2:
                    st.info(f"⚖️ **Slight Edge: {career_1}**")
                    st.markdown(f"Both paths are feasible, but **{career_1}** has a slight advantage in immediate skill overlap.")
                elif match_2 > match_1:
                    st.info(f"⚖️ **Slight Edge: {career_2}**")
                    st.markdown(f"Both paths are feasible, but **{career_2}** has a slight advantage in immediate skill overlap.")
                else:
                    st.info("⚖️ **Balanced Decision Point**")
                    st.markdown(f"Both paths show identical `{int(match_1*100)}%` alignment. Your choice should be based on long-term interest in either product or infrastructure focus.")
            
            # Shared Skills Dashboard Card
            if common_skills:
                st.markdown(f"""
                <div class="dashboard-card" style="padding:20px; margin-top:20px; margin-bottom:10px; background: rgba(56, 189, 248, 0.05); border-left: 4px solid #38BDF8;">
                    <div style="font-weight:700; font-size:0.85rem; color:#38BDF8; margin-bottom:4px; text-transform:uppercase; letter-spacing:0.05em;">🤝 Shared Foundations</div>
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

# Admin Panel
if IS_ADMIN and tab3 is not None:
    with tab3:
        st.markdown("<h3>Security & User Monitoring</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:rgba(255,255,255,0.5);'>Real-time audit trail — visible only to admin.</p>", unsafe_allow_html=True)

        # Summary Metrics
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

        # Live Audit Log
        st.markdown("<h4>Live Audit Log</h4>", unsafe_allow_html=True)
        logs = get_recent_activity(limit=50)
        if logs:
            for log in logs:
                event = log["event"]
                ts = log["timestamp"]
                user = log["username"]
                if event == "LOGIN_FAILED":
                    badge = f"<span style='background:rgba(239,68,68,0.15);color:#FCA5A5;padding:2px 8px;border-radius:12px;font-size:0.78rem;font-weight:600;'>FAILED</span>"
                elif event == "LOGIN_SUCCESS":
                    badge = f"<span style='background:rgba(16,185,129,0.15);color:#6EE7B7;padding:2px 8px;border-radius:12px;font-size:0.78rem;font-weight:600;'>SUCCESS</span>"
                elif event == "SIGNUP":
                    badge = f"<span style='background:rgba(124,58,237,0.15);color:#A78BFA;padding:2px 8px;border-radius:12px;font-size:0.78rem;font-weight:600;'>SIGNUP</span>"
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

        # All Users Table
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

        # Failed Logins
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
