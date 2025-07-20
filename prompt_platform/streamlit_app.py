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

    # If an improvement is active, open the dialog immediately
    if hasattr(st.session_state, 'improving_prompt_id') and st.session_state.improving_prompt_id:
        # We need to import here to avoid a circular dependency
        from prompt_platform.ui_components import improve_prompt_dialog
        improve_prompt_dialog(st.session_state.improving_prompt_id)

    # If viewing lineage is active, open the dialog immediately
    if hasattr(st.session_state, 'viewing_lineage_id') and st.session_state.viewing_lineage_id:
        # We need to import here to avoid a circular dependency
        from prompt_platform.ui_components import view_lineage_dialog
        view_lineage_dialog(st.session_state.viewing_lineage_id)

    # Draw UI
    st.markdown("<h1 class='main-header'>✨ Prompt Platform</h1>", unsafe_allow_html=True)
    
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
    
    tab1, tab2, tab3 = st.tabs(["🚀 Generate", "📋 Manage", "📊 Dashboard"])

    with tab1:
        st.subheader("Generate New Prompt")
        
        # Display improvement results if available
        display_improvement_results("generate")
        
        # Generate prompt form with more space
        with st.container():
            st.markdown("### Create a New Prompt")
            st.markdown("Describe what you want your AI assistant to do. Be specific about the task, role, and expected output.")
            
            # Add helpful tips
            with st.expander("💡 Tips for Writing Effective Task Descriptions", expanded=False):
                st.markdown("""
                **🎯 Be Specific:**
                - Clearly define the task and desired outcome
                - Specify the AI's role (e.g., "expert consultant", "creative writer")
                - Include any constraints or requirements
                
                **📋 Include Context:**
                - Describe the target audience or use case
                - Mention tone, style, or format preferences
                - Specify any technical requirements
                
                **✅ Good Examples:**
                - "Create a prompt for a business consultant to help startups develop marketing strategies"
                - "Design a prompt for a creative writer to generate engaging blog posts about technology"
                - "Build a prompt for a data analyst to explain complex statistics in simple terms"
                
                **❌ Avoid:**
                - Vague descriptions like "make it better" or "improve this"
                - Too many requirements in one prompt
                - Unrealistic expectations or conflicting instructions
                """)
            
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
        
        # Review section for newly generated prompts
        if 'pending_prompt_review' in st.session_state and st.session_state.pending_prompt_review.get('needs_review'):
            st.markdown("---")
            st.subheader("🎯 Review Generated Prompt")
            
            prompt_data = st.session_state.pending_prompt_review['prompt_data']
            task = st.session_state.pending_prompt_review['task']
            
            # Create two columns for better layout
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Show the generated prompt
                st.markdown("**📝 Generated Prompt:**")
                st.code(prompt_data['prompt'], language='text')
                
                # Show generation process - always visible
                if prompt_data.get('generation_process'):
                    st.markdown("**🧠 Generation Process:**")
                    st.markdown(prompt_data['generation_process'])
            
            with col2:
                # Test the prompt inline
                st.markdown("**🧪 Test Your Prompt:**")
                
                # Generate contextual test suggestions (if any)
                from prompt_platform.ui_components import _generate_test_suggestions
                test_suggestions = _generate_test_suggestions(task)
                
                # Only show suggestions if we have them
                if test_suggestions:
                    st.markdown("**💡 Suggested Test Scenarios:**")
                    for i, suggestion in enumerate(test_suggestions, 1):
                        st.markdown(f"{i}. **{suggestion['scenario']}** - {suggestion['description']}")
                        st.markdown(f"   *Try:* `{suggestion['example']}`")
                
                # Inline chat interface for testing
                st.markdown("**💬 Test Chat:**")
                
                # Initialize chat history for this review session
                if 'review_chat_history' not in st.session_state:
                    st.session_state.review_chat_history = []
                
                # Display chat history
                chat_container = st.container(height=300)
                with chat_container:
                    for message in st.session_state.review_chat_history:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])
                
                # Handle chat input
                if user_input := st.chat_input("Test your prompt here..."):
                    sanitized_input = sanitize_text(user_input)
                    st.session_state.review_chat_history.append({"role": "user", "content": sanitized_input})
                    
                    # Generate response using the prompt
                    with st.spinner("🧠 Testing..."):
                        try:
                            # Fix placeholder on the fly for backwards compatibility
                            prompt_template = prompt_data['prompt'].replace('{{input}}', '{input}', 1)
                            final_prompt = prompt_template.format(input=sanitized_input)
                            
                            messages = [
                                {"role": "system", "content": "You are a helpful AI assistant. Execute the user's instruction."},
                                {"role": "user", "content": final_prompt}
                            ]
                            response_generator = st.session_state.api_client.stream_chat_completion(messages)
                            assistant_response = st.write_stream(response_generator)
                            
                            st.session_state.review_chat_history.append({"role": "assistant", "content": assistant_response})
                            # Don't rerun immediately to preserve the generation process display
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error testing prompt: {e}")
            
            # Action buttons - full width below the columns
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Approve & Save", key="approve_prompt", use_container_width=True):
                    # Move to main management area
                    st.session_state.newly_generated_prompt = {
                        'prompt_data': prompt_data,
                        'task': task,
                        'should_show_inline': True
                    }
                    # Clear the review state
                    del st.session_state.pending_prompt_review
                    st.session_state.review_chat_history = []
                    st.toast("✅ Prompt approved and moved to Manage tab!", icon="🎉")
                    st.rerun()
            
            with col2:
                if st.button("✨ Improve", key="improve_prompt", use_container_width=True):
                    # Set the prompt for improvement
                    st.session_state.improving_prompt_id = prompt_data['id']
                    st.session_state.improvement_request = f"Improve this prompt based on testing feedback: {task}"
                    # Clear the review state but keep the prompt in database
                    del st.session_state.pending_prompt_review
                    st.session_state.review_chat_history = []
                    st.toast("✨ Opening improvement dialog...", icon="✨")
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Delete", key="discard_prompt", use_container_width=True):
                    # Remove from database and clear state
                    st.session_state.db.delete_prompt_lineage(prompt_data['lineage_id'])
                    del st.session_state.pending_prompt_review
                    st.session_state.review_chat_history = []
                    st.toast("🗑️ Prompt deleted", icon="🗑️")
                    st.rerun()

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
        
        if st.button("🔄 Refresh Prompts", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        prompts = load_all_prompts()
        main_manager_view(prompts)

    with tab3:
        render_dashboard()

if __name__ == "__main__":
    main() 