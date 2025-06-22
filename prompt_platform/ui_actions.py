"""
This module contains the handler functions (callbacks) for the Streamlit UI.
"""
import streamlit as st
import logging
import uuid
import json
from functools import partial
from typing import Optional

from .config import request_id_var
from .utils import run_async
from .database import db

logger = logging.getLogger(__name__)

def handle_optimize_prompt(prompt_id):
    """Handles the async optimization of a prompt."""
    request_id_var.set(str(uuid.uuid4()))
    with st.status("⚙️ Optimizing prompt...", expanded=True) as status:
        try:
            prompt_data = st.session_state.db.get_prompt(prompt_id)
            
            status.write("Running DSPy optimization...")
            # Use run_async from the utils module
            optimized_data = run_async(st.session_state.prompt_generator.optimize_prompt(prompt_data))
            
            if optimized_data.get('id') == prompt_id:
                status.update(label="Optimization complete: No changes were found to be better.", state="complete", expanded=False)
            else:
                st.session_state.db.save_prompt(optimized_data)
                status.update(label="Optimization complete! New version created.", state="complete", expanded=False)
                st.toast("✅ New version created!", icon="🎉")
                st.cache_data.clear()
            st.rerun()
        except ValueError as e:
            # Handle specific value errors, like no training data
            status.update(label=f"Optimization Warning: {e}", state="warning")
        except Exception as e:
            status.update(label=f"Optimization Failed: {e}", state="error")
            logger.error(f"Optimization failed for prompt {prompt_id}", exc_info=True)

def handle_save_example(prompt_id: int, input_text: str, output_text: str, critique: Optional[str] = None):
    """Handles the saving of a new training example."""
    try:
        if not input_text or not output_text:
            st.warning("Input and output fields cannot be empty.")
            return

        db.add_example(prompt_id, input_text, output_text, critique)
        
        toast_message = "✅ Example saved!"
        if critique:
            toast_message = "✅ Corrected example saved!"
            
        st.toast(toast_message)
        
        # Clear relevant caches
        st.cache_data.clear()

    except Exception as e:
        logger.error(f"Failed to save example for prompt {prompt_id}: {e}", exc_info=True)
        st.error(f"Failed to save example: {e}")

def handle_delete_lineage(lineage_id):
    """Handles the deletion of an entire prompt lineage."""
    request_id_var.set(str(uuid.uuid4()))
    if st.session_state.db.delete_prompt_lineage(lineage_id):
        st.toast(f"🗑️ Lineage `{lineage_id}` deleted.", icon="✅")
        st.cache_data.clear()
        st.rerun()
    else:
        st.error(f"Failed to delete lineage `{lineage_id}`.")

async def generate_and_save_prompt(task):
    """Asynchronously generates a new prompt and saves it to the database."""
    try:
        new_prompt = await st.session_state.prompt_generator.generate_initial_prompt(
            task, st.session_state.api_client
        )
        st.session_state.db.save_prompt(new_prompt)
        st.toast("✅ New prompt created!", icon="🎉")
    except Exception as e:
        st.toast(f"❌ Generation failed: {e}", icon="🔥")
        logger.error(f"Failed to generate and save prompt for task: {task}", exc_info=True)

async def improve_and_save_prompt(prompt_id, task_desc):
    """Asynchronously improves a prompt and saves the new version."""
    try:
        improved_prompt = await st.session_state.prompt_generator.improve_prompt(
            prompt_id, task_desc, st.session_state.api_client, st.session_state.db
        )
        st.session_state.db.save_prompt(improved_prompt)
        st.toast("✅ Prompt improved and new version created!", icon="🎉")
    except Exception as e:
        st.toast(f"❌ Improvement failed: {e}", icon="🔥")
        logger.error(f"Failed to improve and save prompt for id: {prompt_id}", exc_info=True)

async def handle_correction_and_improve(prompt_id: int, user_input: str, desired_output: str, critique: Optional[str]):
    """Saves a corrected example and immediately triggers the prompt improvement process."""
    try:
        # 1. Save the new "good" example, but only if one was provided.
        if desired_output:
            handle_save_example(prompt_id, user_input, desired_output, critique)
            st.toast("✅ Correction saved. Now improving prompt...", icon="🧠")
        else:
            st.toast("✅ Critique received. Now improving prompt...", icon="🧠")

        # 2. Trigger the improvement process
        task_description = (
            f"The previous prompt version produced a bad output for the input: '{user_input}'. "
        )
        if desired_output:
            task_description += f"The desired output was: '{desired_output}'. "
        
        if critique:
            task_description += f"The user provided this critique: '{critique}'. "
        
        task_description += "Improve the prompt based on this new feedback."

        # This function saves the new prompt version and reruns the app
        await improve_and_save_prompt(prompt_id, task_description)

    except Exception as e:
        logger.error(f"Correction and improvement process failed: {e}", exc_info=True)
        st.error(f"Failed to improve prompt: {e}") 