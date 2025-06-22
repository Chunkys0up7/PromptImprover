import streamlit as st
from prompt_platform.prompt_generator import PromptGenerator
from prompt_platform.version_manager import version_manager, set_github_integration, is_github_enabled
from prompt_platform.database import db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize components
prompt_generator = PromptGenerator()

# Streamlit app configuration
st.set_page_config(
    page_title="Prompt Engineering Platform",
    layout="wide"
)

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Settings")
    
    # GitHub Integration Toggle
    github_enabled = st.toggle(
        "Enable GitHub Integration",
        value=is_github_enabled(),
        help="Enable to sync prompts with GitHub repository"
    )
    
    if github_enabled:
        set_github_integration(True)
        if st.button("Sync with GitHub"):
            with st.spinner("Syncing with GitHub..."):
                success = version_manager.pull_from_github()
                if success:
                    st.success("Successfully synced with GitHub!")
                else:
                    st.error("Failed to sync with GitHub")
    else:
        set_github_integration(False)

    # Clear database button
    if st.button("Clear Local Database"):
        with st.spinner("Clearing database..."):
            db.clear_database()
            st.success("Database cleared!")

# Main content
st.title("Prompt Engineering Platform")

# Create new prompt section
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Create New Prompt")
    task = st.text_area("Task Description", height=100)
    
    if st.button("Generate Prompt"):
        if not task:
            st.error("Please enter a task description")
            return
            
        with st.spinner("Generating prompt..."):
            try:
                prompt = await prompt_generator.generate_initial_prompt(task)
                st.success("Prompt generated successfully!")
                st.json(prompt)
                
                if github_enabled:
                    version_manager.push_to_github(prompt["id"])
                    st.success("Prompt synced to GitHub!")
                    
            except Exception as e:
                st.error(f"Failed to generate prompt: {str(e)}")

with col2:
    st.header("Prompt History")
    lineage_id = st.text_input("Lineage ID")
    
    if st.button("Show Lineage"):
        if not lineage_id:
            st.error("Please enter a lineage ID")
            return
            
        lineage = version_manager.get_lineage(lineage_id)
        if lineage:
            st.markdown(version_manager.format_lineage_table(lineage))
        else:
            st.error("No lineage found")

# Improve existing prompt section
st.header("Improve Existing Prompt")
prompt_id = st.text_input("Prompt ID to Improve")
improvement = st.text_area("Improvement Description", height=100)

if st.button("Improve Prompt"):
    if not prompt_id or not improvement:
        st.error("Please enter both prompt ID and improvement description")
        return
        
    with st.spinner("Improving prompt..."):
        try:
            improved_prompt = await prompt_generator.improve_prompt(prompt_id, improvement)
            st.success("Prompt improved successfully!")
            st.json(improved_prompt)
            
            if github_enabled:
                version_manager.push_to_github(improved_prompt["id"])
                st.success("Improved prompt synced to GitHub!")
                
        except Exception as e:
            st.error(f"Failed to improve prompt: {str(e)}")
