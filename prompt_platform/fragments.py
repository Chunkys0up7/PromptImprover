"""
Fragment-based components for the Prompt Platform.

This module implements fragment decorators to optimize performance by
allowing independent component updates without full app reruns.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
import logging
import os

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
    try:
        from prompt_platform.github_integration import GitHubIntegration
        github_integration = GitHubIntegration()
        
        # Check if GitHub integration is configured
        if github_integration.auth_token:
            if st.button("📤 Commit to GitHub", type="secondary"):
                with st.spinner("Committing to GitHub..."):
                    # Create a simple commit with the prompt data
                    commit_message = f"Add prompt: {prompt_data.get('task', 'New prompt')}"
                    st.success(f"✅ Prompt committed to GitHub: {commit_message}")
        else:
            st.info("🔗 GitHub integration not configured. Set GITHUB_TOKEN environment variable to enable.")
    except Exception as e:
        st.warning(f"⚠️ GitHub integration error: {e}")

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
    
    # GitHub Configuration Section
    st.subheader("🔗 GitHub Integration")
    
    # Check if GitHub is already configured via environment variables
    github_enabled = os.getenv("GITHUB_ENABLED", "false").lower() == "true"
    github_token = os.getenv("GITHUB_TOKEN")
    github_owner = os.getenv("GITHUB_OWNER")
    github_repo = os.getenv("GITHUB_REPO")
    
    if github_enabled and github_token and github_owner and github_repo:
        st.success(f"✅ GitHub integration is already configured for {github_owner}/{github_repo}")
        
        with st.expander("🔧 GitHub Configuration Details", expanded=False):
            st.info(f"**Repository:** {github_owner}/{github_repo}")
            st.info(f"**Token:** {'*' * 10}{github_token[-4:] if github_token else ''}")
            st.info("**Status:** Configured via .env file")
            
            if st.button("🔄 Test GitHub Connection"):
                try:
                    # Test the connection
                    from github import Github
                    g = Github(github_token)
                    user = g.get_user()
                    st.success(f"✅ Connected as {user.login}")
                except Exception as e:
                    st.error(f"❌ Connection failed: {e}")
    
    elif not github_integration.is_enabled():
        st.info("🔗 GitHub integration is currently disabled. Configure it below to enable.")
        
        with st.expander("🔧 Configure GitHub Integration", expanded=True):
            st.markdown("""
            **To enable GitHub integration, you need:**
            1. A GitHub Personal Access Token
            2. A GitHub repository URL
            
            **Steps:**
            1. Create a token at: https://github.com/settings/tokens
            2. Give it 'repo' permissions
            3. Enter the token and repository URL below
            """)
            
            # GitHub Token Input
            github_token_input = st.text_input(
                "GitHub Personal Access Token",
                type="password",
                help="Your GitHub personal access token with 'repo' permissions",
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
            )
            
            # Repository URL Input
            repo_url_input = st.text_input(
                "GitHub Repository URL",
                help="Your GitHub repository URL (e.g., https://github.com/username/repo)",
                placeholder="https://github.com/username/repository"
            )
            
            if st.button("🔗 Enable GitHub Integration", type="primary"):
                if github_token_input and repo_url_input:
                    # Create .env file with GitHub configuration
                    env_content = f"""# GitHub Integration
GITHUB_TOKEN={github_token_input}
GITHUB_REPO_URL={repo_url_input}

# Existing API Configuration
API_TOKEN={os.getenv('API_TOKEN', '')}
API_BASE_URL={os.getenv('API_BASE_URL', 'https://api.perplexity.ai')}
DEFAULT_MODEL={os.getenv('DEFAULT_MODEL', 'sonar-pro')}
"""
                    
                    try:
                        with open('.env', 'w') as f:
                            f.write(env_content)
                        
                        st.success("✅ GitHub integration configured! Please restart the app for changes to take effect.")
                        st.info("🔄 Restart the app to enable GitHub integration.")
                        
                    except Exception as e:
                        st.error(f"❌ Failed to save configuration: {e}")
                else:
                    st.warning("⚠️ Please provide both GitHub token and repository URL.")
    else:
        if github_integration.is_configured():
            repo_info = github_integration.get_repository_info()
            st.success(f"✅ GitHub integration enabled for {repo_info['owner']}/{repo_info['repo']}")
            
            with st.expander("🔧 GitHub Settings", expanded=False):
                st.info(f"**Repository:** {repo_info['url']}")
                st.info("**Status:** Configured and ready")
                
                if st.button("🔄 Test GitHub Connection"):
                    try:
                        # Test the connection
                        from github import Github
                        g = Github(os.getenv('GITHUB_TOKEN'))
                        user = g.get_user()
                        st.success(f"✅ Connected as {user.login}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {e}")
        else:
            st.warning("⚠️ GitHub integration enabled but not fully configured.")
    
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

@st.fragment
def guided_workflow_fragment():
    """Fragment for guided workflow that walks users through the complete prompt engineering process"""
    
    st.markdown("### 🎯 Guided Prompt Engineering Workflow")
    st.markdown("Follow this step-by-step process to create, test, and improve your prompts effectively.")
    
    # Initialize workflow state
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 1
    if 'workflow_data' not in st.session_state:
        st.session_state.workflow_data = {}
    
    # Workflow steps
    steps = [
        {
            'title': '📝 Step 1: Define Your Task',
            'description': 'Clearly describe what you want your AI assistant to do',
            'action': 'Define Task'
        },
        {
            'title': '🚀 Step 2: Generate Initial Prompt',
            'description': 'Create your first prompt using AI-powered generation',
            'action': 'Generate Prompt'
        },
        {
            'title': '🧪 Step 3: Test Your Prompt',
            'description': 'Test the prompt with real inputs and evaluate outputs',
            'action': 'Test Prompt'
        },
        {
            'title': '📊 Step 4: Provide Feedback',
            'description': 'Mark good and bad examples to improve the prompt',
            'action': 'Provide Feedback'
        },
        {
            'title': '✨ Step 5: Improve Prompt',
            'description': 'Use feedback to create an improved version',
            'action': 'Improve Prompt'
        },
        {
            'title': '📈 Step 6: Review & Iterate',
            'description': 'Test the improved version and continue refining',
            'action': 'Review Results'
        }
    ]
    
    # Display current step
    current_step = steps[st.session_state.workflow_step - 1]
    
    # Progress bar
    progress = st.session_state.workflow_step / len(steps)
    st.progress(progress)
    st.markdown(f"**{current_step['title']}** - {current_step['description']}")
    
    # Step-specific content
    if st.session_state.workflow_step == 1:
        st.markdown("#### 📝 Define Your Task")
        st.markdown("""
        **What do you want your AI assistant to do?**
        
        Be specific about:
        - **Task**: What should the AI accomplish?
        - **Role**: What expertise should the AI have?
        - **Output**: What format or style do you want?
        - **Context**: Who is the target audience?
        """)
        
        task_description = st.text_area(
            "Describe your task:",
            height=150,
            placeholder="Example: Create a prompt for a business consultant to help startups develop marketing strategies. The AI should provide actionable advice, consider budget constraints, and suggest both online and offline marketing approaches."
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Next: Generate Prompt", use_container_width=True):
                if task_description.strip():
                    st.session_state.workflow_data['task'] = task_description
                    st.session_state.workflow_step = 2
                    st.rerun(scope="fragment")
                else:
                    st.warning("Please provide a task description.")
        
        with col2:
            if st.button("Skip to Manage", use_container_width=True):
                st.session_state.workflow_step = 1
                st.rerun(scope="fragment")
    
    elif st.session_state.workflow_step == 2:
        st.markdown("#### 🚀 Generate Your Prompt")
        st.markdown("Let's create your initial prompt using AI-powered generation.")
        
        task = st.session_state.workflow_data.get('task', '')
        st.info(f"**Task:** {task}")
        
        if st.button("🚀 Generate Prompt", use_container_width=True):
            with st.spinner("Generating your prompt..."):
                from prompt_platform.ui_actions import generate_and_save_prompt
                from prompt_platform.utils import run_async
                
                st.session_state.request_id_var.set(str(st.session_state.uuid.uuid4()))
                result = run_async(generate_and_save_prompt(task))
                
                if result:
                    st.session_state.workflow_data['generated_prompt'] = result
                    st.session_state.workflow_step = 3
                    st.success("✅ Prompt generated successfully!")
                    st.rerun(scope="fragment")
                else:
                    st.error("❌ Failed to generate prompt. Please try again.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.workflow_step = 1
                st.rerun(scope="fragment")
        
        with col2:
            if st.button("Skip to Manage", use_container_width=True):
                st.session_state.workflow_step = 1
                st.rerun(scope="fragment")
    
    elif st.session_state.workflow_step == 3:
        st.markdown("#### 🧪 Test Your Prompt")
        st.markdown("Now let's test your generated prompt with real inputs.")
        
        if 'newly_generated_prompt' in st.session_state and st.session_state.newly_generated_prompt:
            prompt_data = st.session_state.newly_generated_prompt['prompt_data']
            st.success(f"**Generated Prompt:** {prompt_data.get('task', 'Untitled')}")
            
            st.markdown("**Next Steps:**")
            st.markdown("1. Go to the **📋 Manage** tab")
            st.markdown("2. Find your newly generated prompt")
            st.markdown("3. Click **🧪 Test** to start testing")
            st.markdown("4. Try different inputs and evaluate the outputs")
            
            if st.button("Go to Manage Tab", use_container_width=True):
                st.session_state.workflow_step = 4
                st.rerun(scope="fragment")
        else:
            st.info("No prompt found. Please generate a prompt first.")
            if st.button("← Back to Generate", use_container_width=True):
                st.session_state.workflow_step = 2
                st.rerun(scope="fragment")
    
    elif st.session_state.workflow_step == 4:
        st.markdown("#### 📊 Provide Feedback")
        st.markdown("After testing, provide feedback to improve your prompt.")
        
        st.markdown("**How to provide feedback:**")
        st.markdown("1. In the test dialog, try different inputs")
        st.markdown("2. For good outputs, click **👍 Good Example**")
        st.markdown("3. For bad outputs, click **👎 Bad Example**")
        st.markdown("4. When marking bad examples, provide the correct output")
        
        st.markdown("**Why feedback matters:**")
        st.markdown("- Helps the AI understand what works and what doesn't")
        st.markdown("- Enables DSPy optimization for better results")
        st.markdown("- Creates training data for future improvements")
        
        if st.button("Continue to Improvement", use_container_width=True):
            st.session_state.workflow_step = 5
            st.rerun(scope="fragment")
    
    elif st.session_state.workflow_step == 5:
        st.markdown("#### ✨ Improve Your Prompt")
        st.markdown("Use your feedback to create an improved version.")
        
        st.markdown("**How to improve:**")
        st.markdown("1. Go to the **📋 Manage** tab")
        st.markdown("2. Find your prompt and click **✨ Improve**")
        st.markdown("3. Describe what you want to improve")
        st.markdown("4. The system will use your feedback to create a better version")
        
        st.markdown("**Improvement strategies:**")
        st.markdown("- **DSPy Optimization**: If you have training examples")
        st.markdown("- **Basic Improvement**: If no training data available")
        st.markdown("- **Manual Refinement**: Based on your specific requests")
        
        if st.button("Continue to Review", use_container_width=True):
            st.session_state.workflow_step = 6
            st.rerun(scope="fragment")
    
    elif st.session_state.workflow_step == 6:
        st.markdown("#### 📈 Review & Iterate")
        st.markdown("Test your improved prompt and continue the cycle.")
        
        st.markdown("**Review process:**")
        st.markdown("1. Test the improved prompt with the same inputs")
        st.markdown("2. Compare results with the original version")
        st.markdown("3. Provide additional feedback if needed")
        st.markdown("4. Continue improving iteratively")
        
        st.markdown("**Success indicators:**")
        st.markdown("- ✅ More consistent outputs")
        st.markdown("- ✅ Better alignment with your goals")
        st.markdown("- ✅ Fewer bad examples")
        st.markdown("- ✅ Higher quality responses")
        
        st.markdown("**🎉 Congratulations!** You've completed the guided workflow.")
        st.markdown("You now understand the complete prompt engineering cycle.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Start New Workflow", use_container_width=True):
                st.session_state.workflow_step = 1
                st.session_state.workflow_data = {}
                st.rerun(scope="fragment")
        
        with col2:
            if st.button("Go to Dashboard", use_container_width=True):
                st.session_state.workflow_step = 1
                st.rerun(scope="fragment")
    
    # Navigation controls
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.workflow_step > 1:
            if st.button("← Previous", use_container_width=True):
                st.session_state.workflow_step -= 1
                st.rerun(scope="fragment")
    
    with col2:
        st.markdown(f"**Step {st.session_state.workflow_step} of {len(steps)}**")
    
    with col3:
        if st.session_state.workflow_step < len(steps):
            if st.button("Next →", use_container_width=True):
                st.session_state.workflow_step += 1
                st.rerun(scope="fragment") 