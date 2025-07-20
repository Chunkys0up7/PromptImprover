"""
Fragment-based components for the Prompt Platform.

This module implements fragment decorators to optimize performance by
allowing independent component updates without full app reruns.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

@st.fragment
def prompt_generation_fragment():
    """Fragment for prompt generation that runs independently"""
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
    
    from prompt_platform.sanitizers import sanitize_text
    from prompt_platform.ui_actions import generate_and_save_prompt
    from prompt_platform.utils import run_async
    
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
                        st.rerun(scope="fragment")
                else:
                    st.warning("Please provide a task description.")
        
        with col2:
            if st.form_submit_button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun(scope="fragment")

@st.fragment
def prompt_management_fragment():
    """Fragment for managing existing prompts"""
    from prompt_platform.performance_manager import PerformanceManager
    from prompt_platform.ui_components import main_manager_view
    
    # Use optimized loading
    try:
        prompts_data = PerformanceManager.load_prompts_optimized()
        prompts = prompts_data.get('prompts', []) if prompts_data else []
    except Exception as e:
        logger.error(f"Error loading prompts: {e}")
        prompts = []
    
    if st.button("🔄 Refresh Prompts", use_container_width=True):
        st.cache_data.clear()
        st.rerun(scope="fragment")
    
    main_manager_view(prompts)

@st.fragment
def prompt_review_fragment():
    """Fragment for reviewing newly generated prompts"""
    if ('pending_prompt_review' not in st.session_state or 
        not st.session_state.pending_prompt_review or 
        not isinstance(st.session_state.pending_prompt_review, dict) or
        not st.session_state.pending_prompt_review.get('needs_review')):
        return
    
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
            from prompt_platform.sanitizers import sanitize_text
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
                    st.rerun(scope="fragment")
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
            st.rerun(scope="fragment")
    
    with col2:
        if st.button("✨ Improve", key="improve_prompt", use_container_width=True):
            # Set the prompt for improvement
            st.session_state.improving_prompt_id = prompt_data['id']
            st.session_state.improvement_request = f"Improve this prompt based on testing feedback: {task}"
            # Clear the review state but keep the prompt in database
            del st.session_state.pending_prompt_review
            st.session_state.review_chat_history = []
            st.toast("✨ Opening improvement dialog...", icon="✨")
            st.rerun(scope="fragment")
    
    with col3:
        if st.button("🗑️ Delete", key="discard_prompt", use_container_width=True):
            # Remove from database and clear state
            st.session_state.db.delete_prompt_lineage(prompt_data['lineage_id'])
            del st.session_state.pending_prompt_review
            st.session_state.review_chat_history = []
            st.toast("🗑️ Prompt deleted", icon="🗑️")
            st.rerun(scope="fragment")
    
    # GitHub integration option
    from prompt_platform.github_integration import commit_prompt_with_github_option
    commit_prompt_with_github_option(prompt_data)

@st.fragment
def performance_metrics_fragment():
    """Fragment for displaying performance metrics"""
    from prompt_platform.performance_manager import show_performance_metrics
    from prompt_platform.error_handler import show_error_summary
    
    # Show performance metrics
    show_performance_metrics()
    
    # Show error summary if there are errors
    show_error_summary()

@st.fragment
def settings_fragment():
    """Fragment for settings configuration"""
    st.subheader("⚙️ Settings")
    
    # GitHub Integration Settings
    from prompt_platform.github_integration import GitHubIntegration
    github_integration = GitHubIntegration()
    github_config = github_integration.get_github_settings_ui()
    
    st.markdown("---")
    
    # LLM Provider Settings
    st.subheader("🤖 LLM Provider Configuration")
    
    import os
    current_provider = os.getenv('LLM_PROVIDER', 'perplexity')
    
    with st.expander("🔄 Switch LLM Provider", expanded=False):
        st.info("💡 Change your LLM provider here. Make sure to set the required environment variables for your chosen provider.")
        
        provider = st.selectbox(
            "Select LLM Provider",
            options=['perplexity', 'custom_token', 'bedrock', 'openai', 'anthropic'],
            index=['perplexity', 'custom_token', 'bedrock', 'openai', 'anthropic'].index(current_provider),
            help="Choose your preferred LLM provider"
        )
        
        if provider != current_provider:
            st.warning(f"⚠️ To switch to {provider}, set the LLM_PROVIDER environment variable and restart the app.")
            st.code(f"export LLM_PROVIDER={provider}")
        
        # Show provider-specific configuration
        if provider == 'perplexity':
            st.success("✅ Perplexity AI - Current default provider")
            st.info("Set PERPLEXITY_API_KEY environment variable")
            
        elif provider == 'custom_token':
            st.info("🔧 Custom Token-Based API")
            st.markdown("""
            **Required Environment Variables:**
            - `CUSTOM_API_BASE_URL` - Your API endpoint
            - `CUSTOM_AUTH_URL` - Authentication endpoint
            - `CUSTOM_CLIENT_ID` - Client ID
            - `CUSTOM_CLIENT_SECRET` - Client secret
            - `CUSTOM_MODEL_NAME` - Model name
            """)
            
        elif provider == 'bedrock':
            st.info("☁️ AWS Bedrock")
            st.markdown("""
            **Required Environment Variables:**
            - `AWS_ACCESS_KEY_ID` - AWS access key
            - `AWS_SECRET_ACCESS_KEY` - AWS secret key
            - `AWS_REGION` - AWS region (default: us-east-1)
            - `BEDROCK_MODEL_ID` - Bedrock model ID
            """)
            
        elif provider == 'openai':
            st.info("🤖 OpenAI")
            st.markdown("""
            **Required Environment Variables:**
            - `OPENAI_API_KEY` - OpenAI API key
            - `OPENAI_MODEL` - Model name (default: gpt-4o)
            """)
            
        elif provider == 'anthropic':
            st.info("🧠 Anthropic Claude")
            st.markdown("""
            **Required Environment Variables:**
            - `ANTHROPIC_API_KEY` - Anthropic API key
            - `ANTHROPIC_MODEL` - Model name (default: claude-3-5-sonnet-20241022)
            """)
    
    # Current Configuration Status
    st.markdown("---")
    st.subheader("📊 Current Configuration Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔗 GitHub Integration:**")
        if github_integration.is_enabled():
            if github_integration.is_configured():
                repo_info = github_integration.get_repository_info()
                st.success(f"✅ Enabled - {repo_info['owner']}/{repo_info['repo']}")
            else:
                st.warning("⚠️ Enabled but not configured")
        else:
            st.info("🔴 Disabled")
    
    with col2:
        st.markdown("**🤖 LLM Provider:**")
        if st.session_state.api_client.is_configured:
            st.success(f"✅ {current_provider.title()} configured")
        else:
            st.error(f"❌ {current_provider.title()} not configured")
    
    # Documentation Links
    st.markdown("---")
    st.subheader("📚 Documentation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔗 Quick Links:**")
        st.markdown("- [LLM Provider Guide](docs/llm_provider_guide.md)")
        st.markdown("- [Development Guide](docs/DEVELOPMENT.md)")
        st.markdown("- [Database Migration](docs/database_migration_guide.md)")
    
    with col2:
        st.markdown("**📖 GitHub Integration:**")
        st.markdown("- [GitHub Token Setup](https://github.com/settings/tokens)")
        st.markdown("- [Repository Permissions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-teams-and-people-with-access-to-your-repository)")
        st.markdown("- [Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/managing-a-branch-protection-rule)") 