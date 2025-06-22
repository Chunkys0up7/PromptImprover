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

@st.dialog("📜 View Lineage")
def view_lineage_dialog(lineage_id):
    """Renders the 'View Lineage' dialog."""
    st.title(f"Lineage: {lineage_id}")
    prompts = st.session_state.version_manager.get_lineage(lineage_id)
    if not prompts:
        st.warning("No prompts found for this lineage.")
        return
    df = pd.DataFrame(prompts).sort_values('version', ascending=False)
    df['created_at'] = pd.to_datetime(df['created_at'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    # Escape the prompt content to prevent markdown injection
    df['prompt'] = df['prompt'].apply(escape_markdown)
    st.dataframe(df[['version', 'task', 'prompt', 'created_at']], use_container_width=True)

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
            with st.spinner("Improving..."):
                run_async(improve_and_save_prompt(prompt_id, task_desc))
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
    st.title(f"Testing: {prompt_data.get('task', 'Untitled')}")
    st.button("Close", on_click=close_test_dialog, use_container_width=True)

    with st.expander("Show Current Prompt"):
        st.code(prompt_data['prompt'], language='text')

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
                run_async(handle_correction_and_improve(
                    prompt_id, 
                    correction_data["user_input"], 
                    desired_output,
                    critique
                ))
                # The async action will handle closing the dialog via rerun
                st.spinner("Saving and improving...")

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
                    final_prompt = prompt_data['prompt'].format(input=last_user_input)
                    messages = [{"role": "user", "content": final_prompt}]
                    
                    with st.chat_message("assistant"):
                        response_stream = st.session_state.api_client.stream_chat_completion(messages)
                        assistant_response = st.write_stream(response_stream)

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
        st.info("No prompts found. Use the sidebar to generate or improve a prompt.")
        return
        
    df = pd.DataFrame(prompts)
    latest_prompts = df.loc[df.groupby('lineage_id')['version'].idxmax()].sort_values('created_at', ascending=False)
    
    for _, row in latest_prompts.iterrows():
        with st.container(border=True):
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
                improve_prompt_dialog(row['id'])

            if has_training_data:
                cols[2].button(
                    "⚡ Optimize", 
                    key=f"optimize_{row['id']}", 
                    on_click=partial(handle_optimize_prompt, row['id']), 
                    use_container_width=True
                )

            if cols[3].button("📜 Lineage", key=f"lineage_{row['id']}", use_container_width=True):
                view_lineage_dialog(row['lineage_id'])
            
            cols[4].button("🗑️ Delete", key=f"delete_{row['id']}", on_click=partial(handle_delete_lineage, row['lineage_id']), type="primary", use_container_width=True)

def draw_sidebar():
    """Renders the sidebar for global actions."""
    with st.sidebar:
        st.header("🛠️ Global Actions")
        with st.form("new_prompt_form", clear_on_submit=True):
            st.subheader("🚀 Generate New Prompt")
            task = sanitize_text(st.text_area("Task Description:", height=100))
            if st.form_submit_button("Generate", use_container_width=True):
                if task:
                    st.session_state.request_id_var.set(str(st.session_state.uuid.uuid4()))
                    with st.spinner("Generating..."):
                        run_async(generate_and_save_prompt(task))
                        st.cache_data.clear() # To show the new prompt
                        st.rerun()
                else:
                    st.warning("Please provide a task description.")

        # This form is now removed as "Improve" is contextual per prompt
        # with st.form("improve_prompt_form", clear_on_submit=True):
        # ... 