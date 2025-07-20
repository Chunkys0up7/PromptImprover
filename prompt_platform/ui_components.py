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
    
    # API client check
    if not st.session_state.api_client or not st.session_state.api_client.is_configured:
        st.error("API client is not configured. Please check your API token in the environment variables.")
        return

    task_desc = sanitize_text(st.text_area("Improvement instruction:", height=100))
    if st.button("Generate Improvement"):
        if task_desc:
            with st.status("🔄 Improving prompt...", expanded=True) as status:
                status.write("📝 Analyzing improvement request...")
                status.write("🧠 Generating enhanced prompt...")
                status.write("💾 Saving new version...")
                
                run_async(improve_and_save_prompt(prompt_id, task_desc))
                
                status.update(label="✅ Improvement complete! Check the results below.", state="complete")
                st.success("🎉 Prompt improved successfully! The results will be displayed on the main page.")
                st.rerun() # Close dialog and refresh main page
        else:
            st.warning("Please provide an improvement instruction.")

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
    
    # Check if this is a newly generated prompt
    is_newly_generated = (
        'newly_generated_prompt' in st.session_state and 
        st.session_state.newly_generated_prompt.get('prompt_data', {}).get('id') == prompt_id
    )
    
    if is_newly_generated:
        st.title(f"🎉 Testing New Prompt: {prompt_data.get('task', 'Untitled')}")
        st.success("✨ Your prompt has been created! Let's test it with some relevant examples.")
    else:
        st.title(f"Testing: {prompt_data.get('task', 'Untitled')} (v{prompt_data.get('version', 1)})")
    
    st.button("Close", on_click=close_test_dialog, use_container_width=True)

    # Display the prompt diff if it exists in the session state
    if 'prompt_diff' in st.session_state and st.session_state.prompt_diff:
        with st.expander("Show Prompt Improvements", expanded=True):
            st.markdown(st.session_state.prompt_diff, unsafe_allow_html=True)
        # Clear the diff from session state after displaying it
        del st.session_state.prompt_diff

    with st.expander("Show Current Prompt"):
        st.code(prompt_data['prompt'], language='text')
        
        # Show generation process if available
        if prompt_data.get('generation_process'):
            st.markdown("**🧠 Generation Process:**")
            st.markdown(prompt_data['generation_process'])
    
    # For newly generated prompts, show contextual testing guidance
    if is_newly_generated:
        st.subheader("🧪 Testing Your Prompt")
        
        # Generate contextual test suggestions based on the prompt task
        task = prompt_data.get('task', '').lower()
        test_suggestions = _generate_test_suggestions(task)
        
        st.markdown("**💡 Suggested Test Scenarios:**")
        for i, suggestion in enumerate(test_suggestions, 1):
            st.markdown(f"{i}. **{suggestion['scenario']}** - {suggestion['description']}")
            st.markdown(f"   *Try:* `{suggestion['example']}`")
        
        st.markdown("---")
        st.info("**Tip:** Use the chat input below to test your prompt with these scenarios or your own examples.")

    # --- Correction Mode UI ---
    if st.session_state.get('correction_mode'):
        st.subheader("✍️ Correct AI Output")
        correction_data = st.session_state.correction_data
        
        st.write("**Original Input:**")
        st.text(correction_data["user_input"])

        st.write("**Incorrect AI Output:**")
        st.text(correction_data["assistant_response"])
        
        desired_output = st.text_area("Provide the desired, correct output (optional if critique is provided):", height=150)
        critique = st.text_area("Why was this a bad response? (Optional if desired output is provided)", height=100)

        if st.button("Save Correction & Improve", use_container_width=True):
            if not desired_output and not critique:
                st.warning("Please provide either a desired output, a critique, or both.")
            else:
                with st.spinner("Saving correction and improving prompt..."):
                    run_async(handle_correction_and_improve(
                        prompt_id, 
                        correction_data["user_input"], 
                        desired_output,
                        critique
                    ))
                # The session state is now updated with the new prompt ID.
                # Rerunning will automatically reopen the dialog with the new prompt.
                st.rerun()

    # --- Standard Chat UI ---
    else:
        chat_container = st.container(height=400)
        with chat_container:
            for message in st.session_state.test_chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Step 2: If the last message is from the user, generate a response
        if st.session_state.test_chat_history and st.session_state.test_chat_history[-1]["role"] == "user":
            with st.spinner("🧠 Thinking..."):
                try:
                    last_user_input = st.session_state.test_chat_history[-1]["content"]
                    
                    # Fix placeholder on the fly for backwards compatibility.
                    # We only replace the first instance to avoid corrupting examples.
                    prompt_template = prompt_data['prompt'].replace('{{input}}', '{input}', 1)
                    final_prompt = prompt_template.format(input=last_user_input)

                    messages = [
                        {"role": "system", "content": "You are a helpful AI assistant. Execute the user's instruction."},
                        {"role": "user", "content": final_prompt}
                    ]
                    response_generator = st.session_state.api_client.stream_chat_completion(messages)
                    assistant_response = st.write_stream(response_generator)

                    st.session_state.test_chat_history.append({"role": "assistant", "content": assistant_response})
                    st.rerun()

                except (APIResponseError, APITimeoutError) as e:
                    st.error(f"API Error: {e}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred: {e}", exc_info=True)
                    st.error(f"An unexpected error occurred: {e}")

        # Step 1: Get user input
        if user_input := st.chat_input("Enter test input..."):
            sanitized_input = sanitize_text(user_input)
            st.session_state.test_chat_history.append({"role": "user", "content": sanitized_input})
            st.rerun()

        # Display feedback buttons only after an assistant has responded
        if st.session_state.test_chat_history and st.session_state.test_chat_history[-1]["role"] == "assistant":
            last_user_input = st.session_state.test_chat_history[-2]["content"]
            assistant_response = st.session_state.test_chat_history[-1]["content"]
            
            feedback_key_base = f"feedback_{len(st.session_state.test_chat_history)}"
            col1, col2 = st.columns(2)
            
            with col1:
                st.button(
                    "👍 Good Example", 
                    key=f"{feedback_key_base}_good", 
                    use_container_width=True,
                    on_click=handle_save_example,
                    args=(prompt_id, last_user_input, assistant_response)
                )
            
            with col2:
                st.button(
                    "👎 Bad Example", 
                    key=f"{feedback_key_base}_bad", 
                    use_container_width=True,
                    on_click=set_correction_mode,
                    args=(last_user_input, assistant_response)
                )

def main_manager_view(prompts):
    """Renders the main view of the prompt manager."""
    if not prompts:
        st.info("No prompts found. Use the '🚀 Generate' tab to create your first prompt.")
        return
        
    df = pd.DataFrame(prompts)
    latest_prompts = df.loc[df.groupby('lineage_id')['version'].idxmax()].sort_values('created_at', ascending=False)
    
    for _, row in latest_prompts.iterrows():
        with st.container(border=True):
            # Check if this is the latest improvement
            is_latest_improvement = (
                'last_improvement' in st.session_state and 
                st.session_state.last_improvement['improved_prompt']['id'] == row['id']
            )
            
            # Check if this is a newly generated prompt
            is_newly_generated = (
                'newly_generated_prompt' in st.session_state and 
                st.session_state.newly_generated_prompt.get('prompt_data', {}).get('id') == row['id']
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
                    improve_prompt_dialog(row['id'])
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
                    if json.loads(row['training_data']):
                        has_training_data = True
                except json.JSONDecodeError:
                    pass

            cols = st.columns(5)
            if cols[0].button("🧪 Test", key=f"test_{row['id']}", use_container_width=True):
                st.session_state.test_chat_history = [] 
                st.session_state.testing_prompt_id = row['id']
                st.rerun()
            
            if cols[1].button("✨ Improve", key=f"improve_{row['id']}", use_container_width=True):
                # Only open improve dialog if no other dialog is active
                if not st.session_state.get('testing_prompt_id'):
                    # For newly generated prompts, ensure we're improving the correct one
                    if is_newly_generated:
                        # Clear the newly generated flag to prevent confusion
                        if 'newly_generated_prompt' in st.session_state:
                            st.session_state.newly_generated_prompt['should_open_test'] = False
                    improve_prompt_dialog(row['id'])
                else:
                    st.warning("Please close the test dialog first.")

            if has_training_data:
                cols[2].button(
                    "⚡ Optimize", 
                    key=f"optimize_{row['id']}", 
                    on_click=partial(handle_optimize_prompt, row['id']), 
                    use_container_width=True
                )

            if cols[3].button("📜 Lineage", key=f"lineage_{row['id']}", use_container_width=True):
                # Only open lineage dialog if no other dialog is active
                if not st.session_state.get('testing_prompt_id'):
                    view_lineage_dialog(row['lineage_id'])
                else:
                    st.warning("Please close the test dialog first.")
            
            cols[4].button("🗑️ Delete", key=f"delete_{row['id']}", on_click=partial(handle_delete_lineage, row['lineage_id']), type="primary", use_container_width=True)