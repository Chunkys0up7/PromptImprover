"""
This module contains the UI components for the Streamlit app, including dialogs and views.
"""
import streamlit as st
import pandas as pd
from functools import partial
import re
import json
import logging

from .ui_actions import (
    handle_optimize_prompt, 
    handle_delete_lineage, 
    handle_save_example,
    generate_and_save_prompt,
    improve_and_save_prompt,
    handle_correction_and_improve
)
from .api_client import APITimeoutError, APIResponseError
from .utils import run_async
from .sanitizers import sanitize_text

logger = logging.getLogger(__name__)

def show_error(message: str):
    """Displays a standardized error message in the UI."""
    st.toast(f"❌ {message}", icon="🔥")
    logger.error(message)

def escape_markdown(text: str) -> str:
    """Escapes characters that have special meaning in Markdown."""
    # Incomplete list, but covers common cases for table corruption
    return re.sub(r"([\\`*_{}[\]()#+.!|])", r"\\\1", text)

def _generate_test_suggestions(task: str) -> list:
    """Generate contextual test suggestions based on the prompt task."""
    # For now, return an empty list to remove generic suggestions
    # This can be enhanced later with AI-generated contextual suggestions
    return []

@st.dialog("📜 View Lineage")
def view_lineage_dialog(lineage_id):
    """Renders the 'View Lineage' dialog."""
    st.title(f"Lineage: {lineage_id}")
    prompts = st.session_state.version_manager.get_lineage(lineage_id)
    if not prompts:
        st.warning("No prompts found for this lineage.")
        return
    
    # Sort prompts by version in descending order
    sorted_prompts = sorted(prompts, key=lambda x: x.get('version', 0), reverse=True)
    
    for prompt in sorted_prompts:
        with st.expander(f"Version {prompt.get('version', 1)} - {prompt.get('task', 'Untitled')}", expanded=prompt.get('version', 1) == max(p.get('version', 1) for p in sorted_prompts)):
            st.markdown("**Prompt:**")
            st.code(prompt.get('prompt', ''), language='text')
            
            # Show improvement request if available
            if prompt.get('improvement_request'):
                st.markdown("**Improvement Request:**")
                st.info(prompt.get('improvement_request'))
            
            st.markdown(f"**Created:** {pd.to_datetime(prompt.get('created_at', 0), unit='s').strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            if prompt.get('parent_id'):
                st.markdown(f"**Parent ID:** `{prompt.get('parent_id')}`")

@st.dialog("✨ Improve Prompt")
def improve_prompt_dialog(prompt_id):
    """Renders a dialog to improve an existing prompt."""
    st.title("Improve Prompt")
    
    # Check if DSPy optimization is available
    prompt_data = st.session_state.db.get_prompt(prompt_id)
    has_training_data = False
    training_count = 0
    
    # Get training examples from the Example table
    examples = st.session_state.db.get_examples(prompt_id)
    if examples:
        training_count = len(examples)
        has_training_data = training_count > 0
    
    # Fallback to training_data JSON if no examples found (for backward compatibility)
    if not has_training_data and prompt_data and prompt_data.get('training_data'):
        try:
            # Handle both string (JSON) and list formats
            if isinstance(prompt_data['training_data'], str):
                training_data = json.loads(prompt_data['training_data'])
            else:
                training_data = prompt_data['training_data']
            
            training_count = len(training_data) if isinstance(training_data, list) else 0
            has_training_data = training_count > 0
        except (json.JSONDecodeError, TypeError, AttributeError):
            # If we can't parse the training data, assume it's empty
            has_training_data = False
            training_count = 0
    
    # Show DSPy status
    if has_training_data:
        st.success(f"🎯 **DSPy Optimization Available!** ({training_count} training examples)")
        st.info("The system will use DSPy's systematic optimization with your training data for better results.")
    else:
        st.info("💡 **Basic Improvement Mode** - No training data available yet.")
        st.info("Test your prompt and provide feedback to enable DSPy optimization!")
    
    # API client check
    if not st.session_state.api_client or not st.session_state.api_client.is_configured:
        st.error("API client is not configured. Please check your API token in the environment variables.")
        return

    # Check if improvement is in progress
    if hasattr(st.session_state, 'improvement_in_progress') and st.session_state.improvement_in_progress:
        st.warning("🔄 Improvement in progress... Please wait.")
        return

    # Check if improvement was just completed
    if hasattr(st.session_state, 'improvement_completed') and st.session_state.improvement_completed:
        st.success("✅ Improvement completed successfully!")
        
        # Show improvement results
        if hasattr(st.session_state, 'last_improvement') and st.session_state.last_improvement:
            improvement = st.session_state.last_improvement
            
            st.markdown("### 📊 Improvement Results")
            
            # Show the improvement request
            st.markdown(f"**Improvement Request:** {improvement.get('improvement_request', 'N/A')}")
            
            # Show methodology
            if improvement.get('methodology'):
                with st.expander("🧠 View Improvement Methodology", expanded=False):
                    st.markdown(improvement['methodology'])
            
            # Show diff if available
            if improvement.get('diff_html'):
                with st.expander("📝 View Changes", expanded=True):
                    st.markdown(improvement['diff_html'], unsafe_allow_html=True)
            
            # Show action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🧪 Test Improved Prompt", use_container_width=True):
                    # Set the improved prompt for testing
                    improved_prompt = improvement.get('improved_prompt')
                    if improved_prompt:
                        st.session_state.testing_prompt_id = improved_prompt['id']
                        st.session_state.improving_prompt_id = None  # Close improve dialog
                        st.session_state.improvement_completed = False  # Reset flag
                        st.rerun()
            
            with col2:
                if st.button("📋 View in Manage Tab", use_container_width=True):
                    st.session_state.improving_prompt_id = None  # Close dialog
                    st.session_state.improvement_completed = False  # Reset flag
                    st.rerun()
            
            with col3:
                if st.button("✨ Improve Again", use_container_width=True):
                    st.session_state.improvement_completed = False  # Reset flag
                    st.rerun()
        
        return

    task_desc = sanitize_text(st.text_area("Improvement instruction:", height=100))
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Generate Improvement", use_container_width=True):
            if task_desc:
                # Set improvement in progress flag
                st.session_state.improvement_in_progress = True
                
                with st.status("🔄 Improving prompt...", expanded=True) as status:
                    if has_training_data:
                        status.write("🎯 Using DSPy optimization...")
                        status.write("📊 Analyzing training data...")
                        status.write("🧠 Running systematic optimization...")
                    else:
                        status.write("📝 Analyzing improvement request...")
                        status.write("🧠 Generating enhanced prompt...")
                    status.write("💾 Saving new version...")
                    
                    # Run the improvement
                    from prompt_platform.ui_actions import improve_and_save_prompt
                    from prompt_platform.utils import run_async
                    
                    result = run_async(improve_and_save_prompt(prompt_id, task_desc))
                    
                    if result:
                        status.update(label="✅ Improvement complete! Check the results below.", state="complete")
                        
                        # Set completion flags
                        st.session_state.improvement_in_progress = False
                        st.session_state.improvement_completed = True
                        
                        # Show success message
                        st.success("🎉 Prompt improved successfully!")
                        
                        # Rerun to show results
                        st.rerun()
                    else:
                        status.update(label="❌ Improvement failed", state="error")
                        st.session_state.improvement_in_progress = False
                        st.error("Failed to improve prompt. Please try again.")
            else:
                st.warning("Please provide an improvement instruction.")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            # Clear the improving state to close dialog
            st.session_state.improving_prompt_id = None
            # Reset any improvement flags
            if hasattr(st.session_state, 'improvement_in_progress'):
                del st.session_state.improvement_in_progress
            if hasattr(st.session_state, 'improvement_completed'):
                del st.session_state.improvement_completed

@st.dialog("✍️ Correct AI Output")
def correction_dialog(prompt_id, user_input, actual_output):
    """A dialog to let the user provide the correct output."""
    st.write("Original Input:")
    st.code(user_input, language='text')
    st.write("AI's Incorrect Output:")
    st.code(actual_output, language='text')
    
    desired_output = st.text_area("Enter the desired output:", height=200)
    
    if st.button("Save Corrected Example"):
        if desired_output:
            handle_save_example(prompt_id, user_input, desired_output)
            st.rerun() # Closes dialog and refreshes the chat
        else:
            st.warning("Please provide the desired output.")

# --- State-Resetting Callbacks ---
def set_testing_prompt(prompt_id):
    """Callback to set the prompt being tested."""
    st.session_state.testing_prompt_id = prompt_id
    # Reset chat history for the new test session
    st.session_state.test_chat_history = []
    st.session_state.correction_mode = False

def set_correction_mode(user_input, assistant_response):
    """Callback to enter correction mode."""
    st.session_state.correction_mode = True
    st.session_state.correction_data = {
        "user_input": user_input,
        "assistant_response": assistant_response
    }

def close_test_dialog():
    """Callback to properly close the test dialog and clear its state."""
    st.session_state.testing_prompt_id = None
    st.session_state.test_chat_history = []
    st.session_state.correction_mode = False
    st.session_state.correction_data = None

@st.dialog("🧪 Test Prompt")
def test_prompt_dialog(prompt_id):
    """Renders the 'Test Prompt' dialog and handles the chat interaction."""
    prompt_data = st.session_state.db.get_prompt(prompt_id)
    
    # Check if this is a newly generated or improved prompt
    is_newly_generated = (
        'newly_generated_prompt' in st.session_state and 
        st.session_state.newly_generated_prompt is not None and
        st.session_state.newly_generated_prompt.get('prompt_data') is not None and
        st.session_state.newly_generated_prompt.get('prompt_data', {}).get('id') == prompt_id
    )
    
    # Check if this is an improved prompt (different from newly generated)
    is_improved_prompt = (
        'newly_generated_prompt' in st.session_state and 
        st.session_state.newly_generated_prompt is not None and
        st.session_state.newly_generated_prompt.get('original_prompt_id') == prompt_id and
        st.session_state.newly_generated_prompt.get('prompt_data') is not None and
        st.session_state.newly_generated_prompt.get('prompt_data', {}).get('id') != prompt_id
    )
    
    if is_newly_generated:
        st.success("✨ Your prompt has been created! Let's test it.")
    elif is_improved_prompt:
        improved_prompt_data = st.session_state.newly_generated_prompt['prompt_data']
        st.success(f"✨ Your prompt has been improved! (v{improved_prompt_data.get('version', 1)})")
        
        # Show improvement request
        improvement_request = st.session_state.newly_generated_prompt.get('improvement_request', '')
        if improvement_request:
            st.info(f"**Improvement:** {improvement_request}")
    else:
        st.info(f"Testing: {prompt_data.get('task', 'Untitled')} (v{prompt_data.get('version', 1)})")
    
    # Use improved prompt data if this is an improved prompt
    display_prompt_data = improved_prompt_data if is_improved_prompt else prompt_data
    
    # Display the prompt diff if it exists in the session state
    if 'prompt_diff' in st.session_state and st.session_state.prompt_diff:
        with st.expander("📊 Show Prompt Improvements", expanded=False):
            st.markdown(st.session_state.prompt_diff, unsafe_allow_html=True)
        # Clear the diff from session state after displaying it
        del st.session_state.prompt_diff

    with st.expander("📝 Show Current Prompt", expanded=False):
        st.code(display_prompt_data['prompt'], language='text')
        
        # Show generation process if available
        if display_prompt_data.get('generation_process'):
            st.markdown("**🧠 Generation Process:**")
            st.markdown(display_prompt_data['generation_process'])
    
    # For newly generated prompts, show compact testing guidance
    if is_newly_generated:
        st.subheader("🧪 Testing Your Prompt")
        
        # Generate contextual test suggestions based on the prompt task
        task = prompt_data.get('task', '').lower()
        test_suggestions = _generate_test_suggestions(task)
        
        with st.expander("💡 Suggested Test Scenarios", expanded=False):
            for i, suggestion in enumerate(test_suggestions[:3], 1):  # Limit to 3 suggestions
                st.markdown(f"**{i}. {suggestion['scenario']}**")
                st.markdown(f"*Try:* `{suggestion['example']}`")
                st.markdown(f"*Why:* {suggestion['description']}")
                st.markdown("---")
        
        st.info("💡 **Tip:** Use the chat input below to test your prompt with these scenarios or your own examples.")

    # --- Correction Mode UI ---
    if st.session_state.get('correction_mode'):
        st.subheader("✍️ Correct AI Output")
        correction_data = st.session_state.correction_data
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Original Input:**")
            st.text(correction_data["user_input"])
        with col2:
            st.write("**Incorrect AI Output:**")
            st.text(correction_data["assistant_response"])
        
        desired_output = st.text_area("Provide the desired, correct output:", height=100, placeholder="Enter the correct response...")
        critique = st.text_area("Why was this a bad response?", height=80, placeholder="Explain what went wrong...")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Correction & Improve", use_container_width=True):
                if not desired_output and not critique:
                    st.warning("Please provide either a desired output, a critique, or both.")
                else:
                    # Use the correct prompt ID for correction (improved version if available)
                    correction_prompt_id = display_prompt_data['id'] if is_improved_prompt else prompt_id
                    
                    with st.spinner("Saving correction and improving prompt..."):
                        run_async(handle_correction_and_improve(
                            correction_prompt_id, 
                            correction_data["user_input"], 
                            desired_output, 
                            critique
                        ))
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.correction_mode = False
                st.session_state.correction_data = None
                st.rerun()

    # --- Chat Interface ---
    st.subheader("💬 Test Your Prompt")
    
    # Initialize chat history if not exists
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Test your prompt here..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                try:
                    # Format the prompt with user input
                    formatted_prompt = display_prompt_data['prompt'].replace('{input}', prompt)
                    
                    # Get response from API
                    response = run_async(st.session_state.api_client.get_chat_completion([
                        {"role": "user", "content": formatted_prompt}
                    ]))
                    
                    st.markdown(response)
                    
                    # Add assistant message to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                    # Feedback buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("👍 Good", key=f"good_{len(st.session_state.chat_history)}"):
                            # Save as good example
                            run_async(handle_save_example(
                                display_prompt_data['id'], 
                                prompt, 
                                response
                            ))
                            st.success("Saved as good example!")
                    
                    with col2:
                        if st.button("👎 Bad", key=f"bad_{len(st.session_state.chat_history)}"):
                            # Enter correction mode
                            st.session_state.correction_mode = True
                            st.session_state.correction_data = {
                                "user_input": prompt,
                                "assistant_response": response
                            }
                            st.rerun()
                    
                    with col3:
                        if st.button("🔄 Clear Chat", key=f"clear_{len(st.session_state.chat_history)}"):
                            st.session_state.chat_history = []
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"Error generating response: {e}")
    
    # Close button at the bottom
    st.markdown("---")
    if st.button("Close Dialog", use_container_width=True):
        close_test_dialog()

def main_manager_view(prompts):
    """Renders the main view of the prompt manager."""
    if not prompts:
        st.info("No prompts found. Use the '🚀 Generate' tab to create your first prompt.")
        return
    
    # Add loading state
    with st.spinner("Loading prompts..."):
        df = pd.DataFrame(prompts)
        latest_prompts = df.loc[df.groupby('lineage_id')['version'].idxmax()].sort_values('created_at', ascending=False)
    
    # Show loading progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (_, row) in enumerate(latest_prompts.iterrows()):
        # Update progress
        progress = (idx + 1) / len(latest_prompts)
        progress_bar.progress(progress)
        status_text.text(f"Loading prompt {idx + 1} of {len(latest_prompts)}")
        
        # Use custom container styling
        st.markdown('<div class="prompt-container">', unsafe_allow_html=True)
        
        # Clear loading indicators after first prompt
        if idx == 0:
            progress_bar.empty()
            status_text.empty()
        
        # Check if this is the latest improvement
        is_latest_improvement = (
            'last_improvement' in st.session_state and 
            st.session_state.last_improvement and 
            isinstance(st.session_state.last_improvement, dict) and
            st.session_state.last_improvement.get('improved_prompt') and
            isinstance(st.session_state.last_improvement['improved_prompt'], dict) and
            st.session_state.last_improvement['improved_prompt'].get('id') == row['id']
        )
        
        # Check if this is a newly generated prompt
        is_newly_generated = (
            'newly_generated_prompt' in st.session_state and 
            st.session_state.newly_generated_prompt and 
            isinstance(st.session_state.newly_generated_prompt, dict) and
            st.session_state.newly_generated_prompt.get('prompt_data') and
            isinstance(st.session_state.newly_generated_prompt['prompt_data'], dict) and
            st.session_state.newly_generated_prompt['prompt_data'].get('id') == row['id']
        )
        
        if is_newly_generated:
            st.markdown(f"#### 🆕 {row.get('task', 'Untitled')} (v{row.get('version', 1)}) - **Just Created!**")
            st.success("✨ This is a newly generated prompt! It's currently being tested.")
            
            # Show generation process for newly created prompts
            if row.get('generation_process'):
                with st.expander("🧠 View Generation Process", expanded=True):
                    st.markdown(row['generation_process'])
            
            # Add a special improve button for newly generated prompts
            if st.button("✨ Improve This Prompt", key=f"improve_new_{row['id']}", use_container_width=True):
                st.session_state.improving_prompt_id = row['id']
                st.rerun()
        elif is_latest_improvement:
            st.markdown(f"#### 🆕 {row.get('task', 'Untitled')} (v{row.get('version', 1)}) - **Just Improved!**")
            st.success("✨ This prompt was just improved! Check the improvement results above.")
        else:
            st.markdown(f"#### {row.get('task', 'Untitled')} (v{row.get('version', 1)})")
        
        st.code(row['prompt'], language='text')
        
        # Check for training data to enable/disable optimize button
        has_training_data = False
        if row.get('training_data'):
            try:
                # Handle both string (JSON) and list formats
                if isinstance(row['training_data'], str):
                    training_data = json.loads(row['training_data'])
                else:
                    training_data = row['training_data']
                
                if training_data and len(training_data) > 0:
                    has_training_data = True
            except (json.JSONDecodeError, TypeError, AttributeError):
                # If we can't parse the training data, assume it's empty
                has_training_data = False

        # Primary Actions Row - Most important actions
        st.markdown('<div class="prompt-actions">', unsafe_allow_html=True)
        st.markdown('<div class="button-group">', unsafe_allow_html=True)
        primary_cols = st.columns(2)
        
        # Primary Action 1: Test (Most important - users need to test first)
        if primary_cols[0].button("🧪 Test", key=f"test_{row['id']}", use_container_width=True, type="primary"):
            st.session_state.test_chat_history = [] 
            st.session_state.testing_prompt_id = row['id']
            st.rerun()
        
        # Primary Action 2: Improve (Second most important)
        if primary_cols[1].button("✨ Improve", key=f"improve_{row['id']}", use_container_width=True, type="primary"):
            # Only open improve dialog if no other dialog is active
            if not st.session_state.get('testing_prompt_id'):
                # Set the improving prompt ID to open the dialog on next rerun
                st.session_state.improving_prompt_id = row['id']
                st.rerun()
            else:
                st.warning("Please close the test dialog first.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Secondary Actions Row - Supporting actions
        st.markdown('<div class="button-group">', unsafe_allow_html=True)
        secondary_cols = st.columns(3)
        
        # Secondary Action 1: Optimize (when training data available)
        if has_training_data:
            secondary_cols[0].button(
                "⚡ Optimize", 
                key=f"optimize_{row['id']}", 
                on_click=partial(handle_optimize_prompt, row['id']), 
                use_container_width=True
            )
        else:
            # Disabled optimize button when no training data
            secondary_cols[0].button(
                "⚡ Optimize", 
                key=f"optimize_{row['id']}", 
                use_container_width=True, 
                disabled=True,
                help="Test your prompt and provide feedback to enable optimization"
            )

        # Secondary Action 2: Lineage
        if secondary_cols[1].button("📜 Lineage", key=f"lineage_{row['id']}", use_container_width=True):
            # Only open lineage dialog if no other dialog is active
            if not st.session_state.get('testing_prompt_id'):
                st.session_state.viewing_lineage_id = row['lineage_id']
                st.rerun()
            else:
                st.warning("Please close the test dialog first.")
        
        # Secondary Action 3: GitHub Commit
        from prompt_platform.github_integration import GitHubIntegration
        github_integration = GitHubIntegration()
        
        if github_integration.is_enabled() and github_integration.is_configured():
            if secondary_cols[2].button("🔗 Commit", key=f"commit_{row['id']}", use_container_width=True):
                # Commit the prompt to GitHub
                try:
                    result = github_integration.commit_prompt_to_github(row)
                    if result.get('success'):
                        # Show success message with appropriate styling
                        if result.get('note'):
                            st.info(f"ℹ️ {result.get('message', 'Prompt processed on GitHub')}")
                            st.info(f"💡 {result.get('note')}")
                        else:
                            st.success(f"✅ {result.get('message', 'Prompt committed to GitHub!')}")
                        
                        # Show GitHub link if available
                        if result.get('url'):
                            st.info(f"🔗 View at: {result['url']}")
                    else:
                        st.error(f"❌ {result.get('error', 'Failed to commit prompt to GitHub')}")
                except Exception as e:
                    st.error(f"❌ Error committing to GitHub: {e}")
        else:
            # Disabled commit button when GitHub is not configured
            secondary_cols[2].button(
                "🔗 Commit", 
                key=f"commit_{row['id']}", 
                use_container_width=True, 
                disabled=True, 
                help="GitHub integration not configured"
            )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Destructive Action Row - Separated for safety
        st.markdown('<div class="prompt-separator"></div>', unsafe_allow_html=True)
        st.markdown('<div class="button-group">', unsafe_allow_html=True)
        delete_col = st.columns([1, 1, 1])  # Center the delete button
        
        # Destructive Action: Delete (centered, styled as destructive)
        if delete_col[1].button(
            "🗑️ Delete", 
            key=f"delete_{row['id']}", 
            on_click=partial(handle_delete_lineage, row['lineage_id']), 
            type="secondary",
            use_container_width=True
        ):
            pass  # The on_click handler will take care of the deletion
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Close the custom container
        st.markdown('</div>', unsafe_allow_html=True)