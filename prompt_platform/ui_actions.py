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
from .utils import run_async, get_text_diff
# from .database import db # No longer needed

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

        st.session_state.db.add_example(prompt_id, input_text, output_text, critique)
        
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
        # Clear any existing test state before creating a new prompt
        st.session_state.testing_prompt_id = None
        st.session_state.test_chat_history = []
        
        new_prompt = await st.session_state.prompt_generator.generate_initial_prompt(
            task, st.session_state.api_client
        )
        saved_prompt = st.session_state.db.save_prompt(new_prompt)
        
        # Store the newly generated prompt for review
        st.session_state.pending_prompt_review = {
            'prompt_data': saved_prompt,
            'task': task,
            'needs_review': True
        }
        
        st.toast("✅ Prompt generated! Review and test it below.", icon="🎉")
        st.rerun() # Refresh the page to show the review section
    except Exception as e:
        st.toast(f"❌ Generation failed: {e}", icon="🔥")
        logger.error(f"Failed to generate and save prompt for task: {task}", exc_info=True)

async def improve_and_save_prompt(prompt_id, task_desc):
    """
    Asynchronously improves a prompt, saves the new version, 
    and returns the new prompt data.
    """
    try:
        original_prompt = st.session_state.db.get_prompt(prompt_id)
        if not original_prompt:
            st.error(f"Could not find original prompt with ID {prompt_id}")
            return None

        improved_prompt = await st.session_state.prompt_generator.improve_prompt(
            prompt_id, task_desc, st.session_state.api_client, st.session_state.db
        )
        # save_prompt now returns the saved object
        saved_prompt = st.session_state.db.save_prompt(improved_prompt)

        # Generate and store the diff
        diff_html = get_text_diff(original_prompt['prompt'], saved_prompt['prompt'])
        st.session_state.prompt_diff = diff_html
        
        # Store improvement details for immediate display
        st.session_state.last_improvement = {
            'original_prompt': original_prompt,
            'improved_prompt': saved_prompt,
            'improvement_request': task_desc,
            'diff_html': diff_html,
            'methodology': _get_improvement_methodology(task_desc)
        }

        st.toast("✅ Prompt improved and new version created!", icon="🎉")
        return saved_prompt
    except Exception as e:
        st.toast(f"❌ Improvement failed: {e}", icon="🔥")
        logger.error(f"Failed to improve and save prompt for id: {prompt_id}", exc_info=True)
        return None

def _get_improvement_methodology(task_desc):
    """Returns methodology explanation based on the improvement request."""
    if isinstance(task_desc, dict):
        # Structured improvement from correction
        methodology = "**🔄 Iterative Refinement Methodology**\n\n"
        methodology += "**Framework:** Systematic Prompt Engineering + AI-Powered Enhancement\n\n"
        methodology += "**Process Steps:**\n\n"
        methodology += "• **📊 User Feedback Integration**\n"
        methodology += "  - Incorporated specific user input and desired output\n"
        methodology += "  - Analyzed feedback patterns for improvement opportunities\n\n"
        methodology += "• **🔍 Error Analysis**\n"
        methodology += "  - Identified gap between actual and expected responses\n"
        methodology += "  - Applied root cause analysis to prompt weaknesses\n\n"
        methodology += "• **⚡ AI-Powered Optimization**\n"
        methodology += "  - Applied targeted improvements using systematic prompt engineering\n"
        methodology += "  - Used advanced reasoning capabilities for prompt enhancement\n\n"
        methodology += "• **📈 Version Control**\n"
        methodology += "  - Created new version while preserving lineage\n"
        methodology += "  - Maintained audit trail for continuous improvement\n\n"
        methodology += "**Note:** For optimization with training data, we use DSPy framework for few-shot learning."
        return methodology
    else:
        # Text-based improvement
        methodology = "**🧠 Prompt Engineering Methodology**\n\n"
        methodology += "**Framework:** Systematic Prompt Design + AI-Powered Enhancement\n\n"
        methodology += "**Process Steps:**\n\n"
        methodology += "• **📋 Requirement Analysis**\n"
        methodology += "  - Parsed improvement request for key objectives\n"
        methodology += "  - Applied systematic prompt engineering principles\n\n"
        methodology += "• **🛡️ Context Preservation**\n"
        methodology += "  - Maintained core functionality while enhancing specific aspects\n"
        methodology += "  - Ensured prompt safety and reliability\n\n"
        methodology += "• **🚀 AI-Powered Enhancement**\n"
        methodology += "  - Applied systematic improvements using prompt engineering best practices\n"
        methodology += "  - Leveraged advanced reasoning for optimal prompt structure\n\n"
        methodology += "• **📊 Version Tracking**\n"
        methodology += "  - Created new version with full lineage history\n"
        methodology += "  - Enabled continuous improvement and audit trail\n\n"
        methodology += "**Note:** For optimization with training data, we use DSPy framework for few-shot learning."
        return methodology

def display_improvement_results(context="default"):
    """Display the results of the latest prompt improvement using native Streamlit components."""
    if 'last_improvement' not in st.session_state:
        return
    
    improvement = st.session_state.last_improvement
    
    with st.expander("🎯 **Latest Improvement Results**", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**📝 Improvement Request:**")
            if isinstance(improvement['improvement_request'], dict):
                st.info(f"**User Input:** {improvement['improvement_request'].get('user_input', 'N/A')}")
                st.info(f"**Desired Output:** {improvement['improvement_request'].get('desired_output', 'N/A')}")
                st.info(f"**Critique:** {improvement['improvement_request'].get('critique', 'N/A')}")
            else:
                st.info(improvement['improvement_request'])
        
        with col2:
            st.markdown("**📊 Version Info:**")
            st.metric("Version", improvement['improved_prompt']['version'])
            st.metric("Lineage ID", improvement['improved_prompt']['lineage_id'][:8] + "...")
        
        # Display changes using native Streamlit components
        st.markdown("**🔍 Changes Made:**")
        
        # Original prompt section
        st.markdown("**📝 Original Prompt:**")
        with st.container():
            st.code(improvement['original_prompt']['prompt'], language='text')
        
        st.markdown("---")
        
        # Improved prompt section
        st.markdown("**✨ Improved Prompt:**")
        with st.container():
            st.code(improvement['improved_prompt']['prompt'], language='text')
        
        # Show key changes if available
        if 'diff_html' in improvement and improvement['diff_html']:
            st.markdown("**🔍 Key Changes:**")
            # Extract changes from the diff (simplified approach)
            original_lines = improvement['original_prompt']['prompt'].split('\n')
            improved_lines = improvement['improved_prompt']['prompt'].split('\n')
            
            changes = []
            for i, (orig, impr) in enumerate(zip(original_lines, improved_lines)):
                if orig != impr:
                    changes.append({
                        "Line": i+1,
                        "Type": "Modified",
                        "Original": orig[:100] + "..." if len(orig) > 100 else orig,
                        "Improved": impr[:100] + "..." if len(impr) > 100 else impr
                    })
            
            # Add any new lines
            if len(improved_lines) > len(original_lines):
                for i in range(len(original_lines), len(improved_lines)):
                    changes.append({
                        "Line": i+1,
                        "Type": "Added",
                        "Original": "",
                        "Improved": improved_lines[i][:100] + "..." if len(improved_lines[i]) > 100 else improved_lines[i]
                    })
            
            # Remove any deleted lines
            if len(original_lines) > len(improved_lines):
                for i in range(len(improved_lines), len(original_lines)):
                    changes.append({
                        "Line": i+1,
                        "Type": "Removed",
                        "Original": original_lines[i][:100] + "..." if len(original_lines[i]) > 100 else original_lines[i],
                        "Improved": ""
                    })
            
            if changes:
                # Create a DataFrame for better table display
                import pandas as pd
                df = pd.DataFrame(changes)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No specific line changes detected")
        
        # Methodology section
        st.markdown("**🧠 Methodology Applied:**")
        with st.container():
            st.markdown(improvement['methodology'])
        
        # Add action buttons for testing and improving
        st.markdown("---")
        st.markdown("**🎯 Next Steps:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Test the improved prompt
            test_key = f"test_improved_{hash(str(improvement))}_{context}_{id(improvement)}"
            if st.button("🧪 Test Improved Prompt", key=test_key, use_container_width=True):
                st.session_state.testing_prompt_id = improvement['improved_prompt']['id']
                st.session_state.test_chat_history = []
                st.toast("🧪 Opening test dialog for improved prompt...", icon="🧪")
                st.rerun()
        
        with col2:
            # Improve the prompt further
            improve_key = f"improve_further_{hash(str(improvement))}_{context}_{id(improvement)}"
            if st.button("✨ Improve Further", key=improve_key, use_container_width=True):
                st.session_state.improving_prompt_id = improvement['improved_prompt']['id']
                st.toast("✨ Opening improvement dialog...", icon="✨")
                st.rerun()
        
        with col3:
            # Acknowledge and continue
            unique_key = f"acknowledge_improvement_{hash(str(improvement))}_{context}_{id(improvement)}"
            if st.button("✅ Acknowledge & Continue", key=unique_key, use_container_width=True):
                del st.session_state.last_improvement
                st.rerun()

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

        bad_output = st.session_state.get('correction_data', {}).get('bad_output', 'Not available')
        
        correction_details = {
            "user_input": user_input,
            "bad_output": bad_output,
            "desired_output": desired_output,
            "critique": critique,
        }
        
        # 1. Save the correction data to the database
        st.session_state.db.add_correction(prompt_id, correction_details)

        # 2. Trigger the improvement, passing the structured dictionary
        new_prompt = await improve_and_save_prompt(prompt_id, correction_details)

        if new_prompt:
            # Store the new prompt's ID to be used by the UI
            st.session_state.testing_prompt_id = new_prompt['id']
            # Reset state for the new test session
            st.session_state.test_chat_history = []
            st.session_state.correction_mode = False
            st.session_state.correction_data = None
            st.toast("✨ New version created and loaded! Please test again.", icon="🚀")

    except Exception as e:
        logger.error(f"Correction and improvement process failed: {e}", exc_info=True)
        st.error(f"Failed to improve prompt: {e}") 