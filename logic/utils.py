import re
import streamlit as st

def clean_input(user_input):
    """Cleans user input by lowercasing and splitting skills."""
    if not user_input:
        return []
    if isinstance(user_input, list):
        user_input = ",".join(user_input)
    # Split by comma or newline and strip whitespace
    skills = [s.strip().lower() for s in re.split(r'[,\n]+', user_input) if s.strip()]
    return skills

def load_css(file_path):
    """Injects custom CSS from a file into the Streamlit app."""
    try:
        with open(file_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file not found: {file_path}")
