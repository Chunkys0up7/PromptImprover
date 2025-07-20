"""
Main Streamlit application file for the Prompt Platform.

This file is responsible for:
- Initializing services and session state.
- Orchestrating the UI by calling components from other modules.
"""
import streamlit as st
import asyncio
import logging
import uuid
import pandas as pd

from prompt_platform.config import request_id_var
# Import classes instead of singleton instances
from prompt_platform.database import PromptDB
from prompt_platform.prompt_generator import PromptGenerator
from prompt_platform.version_manager import VersionManager
from prompt_platform.api_client import APIClient, APIConfigurationError
from prompt_platform.ui_components import main_manager_view
from prompt_platform.dashboard import render_dashboard
from prompt_platform.ui_actions import display_improvement_results, generate_and_save_prompt
from prompt_platform.sanitizers import sanitize_text
from prompt_platform.utils import run_async

# --- Page & Logging Setup ---
st.set_page_config(page_title="Prompt Platform", layout="wide", initial_sidebar_state="expanded")
logger = logging.getLogger(__name__)

# --- CSS ---
st.markdown("""
<style>
.main-header { font-size: 2.5rem; font-weight: 700; color: #1e3a8a; text-align: center; margin-bottom: 2rem; background: linear-gradient(90deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stButton > button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 0.5rem; padding: 0.75rem 1.5rem; font-weight: 600; transition: all 0.3s ease; }
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 15px rgba(102, 126, 234, 0.4); }
</style>
""", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_all_prompts():
    """Cached function to fetch all prompts from the database."""
    logger.info("Cache miss: Loading all prompts from the database.")
    return st.session_state.db.get_all_prompts()

# --- Main App ---
def main():
    """Initializes services and renders the main application layout."""
    # Initialize services and store them in session state ONCE
    if 'db' not in st.session_state:
        logger.info("Initializing services for the first time for this session.")
        try:
            st.session_state.db = PromptDB()
            st.session_state.api_client = APIClient()
            st.session_state.prompt_generator = PromptGenerator(st.session_state.db)
            st.session_state.version_manager = VersionManager(st.session_state.db)
        except Exception as e:
            st.error(f"Fatal Error: Could not initialize services. {e}")
            logger.critical(f"Service initialization failed: {e}", exc_info=True)
            st.stop()

    st.session_state.request_id_var = request_id_var
    st.session_state.uuid = uuid

    # Initialize other session state variables
    if "test_chat_history" not in st.session_state:
        st.session_state.test_chat_history = []
    if "test_prompt_id" not in st.session_state:
        st.session_state.test_prompt_id = None
    if "testing_prompt_id" not in st.session_state:
        st.session_state.testing_prompt_id = None

    # If a test is active, open the dialog immediately
    if st.session_state.testing_prompt_id:
        # We need to import here to avoid a circular dependency
        from prompt_platform.ui_components import test_prompt_dialog
        test_prompt_dialog(st.session_state.testing_prompt_id)

    # Draw UI
    st.markdown("<h1 class='main-header'>✨ Prompt Platform</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🚀 Generate", "📋 Manage", "📊 Dashboard"])

    with tab1:
        st.subheader("Generate New Prompt")
        
        # Display improvement results if available
        display_improvement_results()
        
        # Generate prompt form with more space
        with st.container():
            st.markdown("### Create a New Prompt")
            st.markdown("Describe what you want your AI assistant to do. Be specific about the task, role, and expected output.")
            
            with st.form("new_prompt_form", clear_on_submit=True):
                task = sanitize_text(st.text_area(
                    "**Task Description:**", 
                    height=200,
                    placeholder="Example: Create a prompt that helps users write professional emails. The AI should act as a business communication expert, provide clear structure, and suggest appropriate tone and language."
                ))
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.form_submit_button("🚀 Generate Prompt", use_container_width=True):
                        if task:
                            st.session_state.request_id_var.set(str(st.session_state.uuid.uuid4()))
                            with st.spinner("Generating your prompt..."):
                                run_async(generate_and_save_prompt(task))
                                st.cache_data.clear() # To show the new prompt
                                st.rerun()
                        else:
                            st.warning("Please provide a task description.")
                
                with col2:
                    if st.form_submit_button("🔄 Refresh", use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()

    with tab2:
        st.subheader("Manage Existing Prompts")
        
        # Display improvement results if available
        display_improvement_results()
        
        if st.button("🔄 Refresh Prompts", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        prompts = load_all_prompts()
        main_manager_view(prompts)

    with tab3:
        render_dashboard()

if __name__ == "__main__":
    main() 