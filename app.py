import streamlit as st
import os
from dotenv import load_dotenv
from logic.users import save_user_profile
from logic.agent import process_career_data
from logic.utils import load_css
from logic.ui_renderer import render_auth_section, render_agent_thinking, render_dashboard_tab, \
                             render_skill_gaps, render_roadmap, render_comparison, render_admin

load_dotenv()
st.set_page_config(page_title=os.getenv("APP_TITLE", "Career Mapper"), page_icon="✨", layout="wide")
load_css("assets/css/style.css")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    render_auth_section(); st.stop()

# --- Main App Orchestration ---
st.markdown("<h1>Skill-Based Career Path Mapper</h1>", unsafe_allow_html=True)

with st.sidebar:
    if st.button("Logout", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.markdown("### Configuration")
    goal = st.text_input("Desired Role", value=st.session_state.get("career_goal_input", ""))
    exp = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced"], index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.get("experience_level_input", "Beginner")))
    skills = st.text_area("Current Skills", value=st.session_state.get("current_skills_input", ""), height=100)
    if st.button("Activate Agent", type="primary", use_container_width=True):
        if not goal: st.sidebar.error("Enter a role.")
        else:
            res = render_agent_thinking(goal, skills, exp)
            st.session_state.update({"career_result": res, "current_skills_input": skills, "career_goal_input": goal, "experience_level_input": exp})
            save_user_profile(st.session_state.username, {"career_goal": goal, "experience_level": exp, "current_skills": skills, "career_result": res, "agent_state": st.session_state.get("agent_state")})
            st.rerun()

# --- Tabs Logic ---
tabs = st.tabs(["My Career Plan", "Compare Careers"] + (["Admin Panel"] if st.session_state.username == os.getenv("ADMIN_USERNAME") else []))

def save_callback():
    res = st.session_state.career_result
    steps = res.get("roadmap_labeled", [])
    prog = {f"step_{res['title']}_{s['index']}": st.session_state[f"step_{res['title']}_{s['index']}"] for s in steps}
    comp = [k for k, v in prog.items() if v]
    agent_st = st.session_state.get("agent_state", {})
    agent_st["completed_steps"] = comp
    new_res = process_career_data(st.session_state.career_goal_input, st.session_state.current_skills_input, st.session_state.experience_level_input, agent_st)
    if new_res.get("status") == "success":
        st.session_state.update({"career_result": new_res, "agent_state": agent_st, "current_skills_input": ", ".join(new_res.get("updated_skills", [])), "experience_level_input": new_res.get("updated_experience_level", "beginner").capitalize()})
    save_user_profile(st.session_state.username, {"roadmap_progress": prog, "agent_state": agent_st, "career_result": st.session_state.career_result, "current_skills": st.session_state.current_skills_input, "experience_level": st.session_state.experience_level_input})

with tabs[0]:
    if "career_result" in st.session_state:
        res = st.session_state.career_result
        render_dashboard_tab(res)
        render_skill_gaps(res)
        render_roadmap(res, save_callback)
    else: st.info("Activate the agent in the sidebar to begin.")

with tabs[1]: render_comparison()
if len(tabs) > 2:
    with tabs[2]: render_admin()
