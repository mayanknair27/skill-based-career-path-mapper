import streamlit as st
import os

def load_css(file_path):
    """Reads a CSS file and injects it into the Streamlit app."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"CSS file not found at {file_path}")
