"""
Enhanced Streamlit application file for the Prompt Platform.

This file implements modern Streamlit best practices including:
- Fragment-based architecture for performance optimization
- Centralized state management
- Enhanced error handling and user feedback
- Modern theming and CSS architecture
"""
import streamlit as st
import asyncio
import logging
import uuid
import pandas as pd
import os

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
from prompt_platform.github_integration import commit_prompt_with_github_option

# Import new architecture components
from prompt_platform.state_manager import PromptPlatformState
from prompt_platform.performance_manager import PerformanceManager
from prompt_platform.error_handler import ErrorHandler
from prompt_platform.styles import load_custom_styles, load_animation_styles
from prompt_platform.fragments import (
    prompt_generation_fragment,
    prompt_management_fragment,
    prompt_review_fragment,
    performance_metrics_fragment,
    settings_fragment
)

# --- Enhanced Page Configuration ---
st.set_page_config(
    page_title="Prompt Platform",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io/',
        'About': "AI-Powered Prompt Engineering Platform v2.0"
    }
)
logger = logging.getLogger(__name__)

# --- Modern CSS Styling ---
st.markdown(load_custom_styles(), unsafe_allow_html=True)
st.markdown(load_animation_styles(), unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_all_prompts():
    """Cached function to fetch all prompts from the database."""
    logger.info("Cache miss: Loading all prompts from the database.")
    return st.session_state.db.get_all_prompts()

# --- Main App ---
def main():
    """Enhanced main application with modern architecture and performance optimization."""
    
    # Initialize core systems with error handling
    try:
        # Initialize state manager
        if 'state_manager' not in st.session_state:
            st.session_state.state_manager = PromptPlatformState()
        
        # Initialize performance manager
        if 'performance_manager' not in st.session_state:
            st.session_state.performance_manager = PerformanceManager()
        
        # Initialize error handler
        if 'error_handler' not in st.session_state:
            st.session_state.error_handler = ErrorHandler()
        
        # Initialize services and store them in session state ONCE
        if 'db' not in st.session_state:
            logger.info("Initializing services for the first time for this session.")
            try:
                st.session_state.db = PromptDB()
                st.session_state.api_client = APIClient()
                st.session_state.prompt_generator = PromptGenerator(st.session_state.db)
                st.session_state.version_manager = VersionManager(st.session_state.db)
            except Exception as e:
                st.session_state.error_handler._show_user_friendly_error("Service Initialization", e)
                logger.critical(f"Service initialization failed: {e}", exc_info=True)
                st.stop()
        
        # Set request tracking
        st.session_state.request_id_var = request_id_var
        st.session_state.uuid = uuid
        
    except Exception as e:
        st.error(f"Fatal Error: Could not initialize application systems. {e}")
        logger.critical(f"Application initialization failed: {e}", exc_info=True)
        st.stop()

    # Handle active dialogs using state manager (simplified)
    try:
        # Check for active dialogs and handle them appropriately
        if hasattr(st.session_state, 'testing_prompt_id') and st.session_state.testing_prompt_id:
            from prompt_platform.ui_components import test_prompt_dialog
            test_prompt_dialog(st.session_state.testing_prompt_id)
        
        if hasattr(st.session_state, 'improving_prompt_id') and st.session_state.improving_prompt_id:
            from prompt_platform.ui_components import improve_prompt_dialog
            improve_prompt_dialog(st.session_state.improving_prompt_id)
        
        if hasattr(st.session_state, 'viewing_lineage_id') and st.session_state.viewing_lineage_id:
            from prompt_platform.ui_components import view_lineage_dialog
            view_lineage_dialog(st.session_state.viewing_lineage_id)
        
    except Exception as e:
        logger.error(f"Error handling dialogs: {e}")
        # Continue without dialogs rather than crashing

    # Draw UI
    st.markdown("<h1 class='main-header'>✨ Prompt Platform</h1>", unsafe_allow_html=True)
    
    # Quick GitHub toggle in header
    from prompt_platform.github_integration import GitHubIntegration
    github_integration = GitHubIntegration()
    
    if github_integration.is_enabled():
        if github_integration.is_configured():
            repo_info = github_integration.get_repository_info()
            st.success(f"🔗 GitHub: {repo_info['owner']}/{repo_info['repo']}")
        else:
            st.warning("🔗 GitHub: Enabled but not configured")
    else:
        st.info("🔗 GitHub: Disabled")
    
    # Add informational section about the system
    with st.expander("🧠 How Our AI-Powered Prompt Engineering Works", expanded=False):
        st.markdown("""
        ### 🎯 **Our Systematic Approach to Prompt Engineering**
        
        We use advanced AI-powered methodologies to create and improve prompts that are both effective and reliable.
        
        #### **🚀 Prompt Generation Process:**
        
        **1. 📋 Systematic Analysis**
        - We analyze your task description using systematic prompt engineering principles
        - Identify key objectives, constraints, and desired outcomes
        - Apply proven frameworks for prompt structure and clarity
        
        **2. 🧠 AI-Powered Design**
        - Our AI generates prompts using systematic prompt engineering methodologies
        - Incorporates best practices for clarity, specificity, and effectiveness
        - Ensures prompts are well-structured and actionable
        
        **3. 📊 Quality Assurance**
        - Each prompt includes detailed generation process documentation
        - Shows the reasoning behind design decisions
        - Enables transparency and continuous improvement
        
        #### **✨ Prompt Improvement Process:**
        
        **1. 🔍 Analysis & Feedback**
        - We analyze testing results and user feedback
        - Identify areas for improvement based on actual performance
        - Apply systematic prompt engineering principles for enhancement
        
        **2. 🚀 DSPy-Powered Enhancement**
        - Our AI applies DSPy's systematic optimization framework
        - Uses data-driven improvement with training examples
        - Selects appropriate optimizers based on data size
        - Maintains core functionality while enhancing specific aspects
        
        **3. 📈 Version Control & Lineage**
        - Every improvement creates a new version with full history
        - Track changes and improvements over time
        - Enable continuous learning and optimization
        
        #### **🎨 Key Methodologies:**
        
        - **Systematic Prompt Design**: Structured approach to prompt creation
        - **DSPy Optimization**: Data-driven prompt improvement using DSPy framework
        - **AI-Powered Enhancement**: Advanced reasoning for prompt optimization
        - **Version Tracking**: Complete history of all changes and improvements
        - **Continuous Learning**: Iterative improvement based on real-world testing
        
        #### **💡 Best Practices We Apply:**
        
        - **Clarity**: Clear, unambiguous instructions
        - **Specificity**: Detailed, actionable guidance
        - **Context**: Appropriate role and tone definition
        - **Safety**: Reliable and trustworthy outputs
        - **Flexibility**: Adaptable to different use cases
        - **Data-Driven**: Optimization based on training examples
        
        #### **🔬 DSPy Optimization Strategies:**
        
        - **BootstrapFewShot**: For limited examples (<10)
        - **BootstrapFewShotWithRandomSearch**: For moderate data (10-50)
        - **MIPROv2**: For larger datasets (50+ examples)
        - **Fallback**: Basic improvement if DSPy optimization fails
        
        #### **🚀 How to Use DSPy Improvement:**
        
        **1. Test Your Prompt First:**
        - Click "🧪 Test" on any prompt
        - Try different inputs and evaluate the outputs
        - Use "👍 Good Example" for outputs you like
        - Use "👎 Bad Example" for outputs that need improvement
        
        **2. Provide Feedback:**
        - When you mark an output as "Bad Example"
        - Enter the correct/desired output
        - Add any specific critique or improvement suggestions
        
        **3. Trigger DSPy Improvement:**
        - Click "✨ Improve" on the prompt
        - Enter your improvement request (e.g., "Make it more concise")
        - The system will automatically:
          - Use DSPy optimization if you have training examples
          - Fall back to basic improvement if needed
        
        **4. Review Results:**
        - See detailed changes in a comparison table
        - Test the improved prompt immediately
        - Continue improving iteratively
        
        **💡 Pro Tip:** The more you test and provide feedback, the better DSPy can optimize your prompts using the accumulated training data!
        """)
    
    # Enhanced tab system with modern styling and fragments
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Generate", "📋 Manage", "📊 Dashboard", "⚙️ Settings"])

    with tab1:
        st.subheader("Generate New Prompt")
        
        # Display improvement results if available
        display_improvement_results("generate")
        
        # Use fragment-based generation
        prompt_generation_fragment()
        
        # Use fragment-based review
        prompt_review_fragment()

    with tab2:
        st.subheader("Manage Existing Prompts")
        
        # Display improvement results if available
        display_improvement_results("manage")
        
        # Add workflow guidance
        with st.expander("🔄 Understanding the Testing & Improvement Workflow", expanded=False):
            st.markdown("""
            ### 🧪 **How to Test and Improve Your Prompts**
            
            **1. 🎯 Test Your Prompts:**
            - Click the "Test" button on any prompt
            - Try different inputs to see how the prompt performs
            - Evaluate the quality and relevance of outputs
            
            **2. 📊 Provide Feedback:**
            - Use "👍 Good Example" for outputs you like
            - Use "👎 Bad Example" for outputs that need improvement
            - Provide specific feedback on what should be changed
            
            **3. ✨ Improve Based on Testing:**
            - Click "Improve" to refine prompts based on feedback
            - Our AI analyzes your feedback and applies systematic improvements
            - Each improvement creates a new version with full history
            
            **4. 📈 Track Progress:**
            - View the complete lineage of your prompts
            - See how each version improves upon the previous
            - Monitor performance over time
            
            ### 💡 **Best Practices for Testing:**
            
            - **Test with realistic inputs** that match your use case
            - **Try edge cases** to see how the prompt handles unusual requests
            - **Evaluate consistency** across multiple test runs
            - **Consider the target audience** when assessing outputs
            - **Focus on the most important aspects** for your specific needs
            
            ### 🔄 **Continuous Improvement Cycle:**
            
            1. **Generate** → Create initial prompt
            2. **Test** → Evaluate with real inputs
            3. **Improve** → Refine based on feedback
            4. **Repeat** → Continue testing and improving
            """)
        
        # Use fragment-based management
        prompt_management_fragment()

    with tab3:
        render_dashboard()
        
        # Add performance metrics if enabled
        if st.checkbox("Show Performance Metrics", value=False):
            performance_metrics_fragment()

    with tab4:
        # Use fragment-based settings
        settings_fragment()

if __name__ == "__main__":
    main() 