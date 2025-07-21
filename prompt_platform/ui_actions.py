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

        example_data = {
            'prompt_id': prompt_id,
            'input_text': input_text,
            'output_text': output_text,
            'critique': critique
        }
        st.session_state.db.add_example(example_data)
        
        # Check if we have enough examples to trigger improvement
        examples = st.session_state.db.get_examples(prompt_id)
        if len(examples) >= 3:  # Trigger improvement after 3 examples
            st.toast("🎯 Enough examples collected! Triggering DSPy optimization...", icon="🚀")
            # Trigger improvement asynchronously
            run_async(improve_and_save_prompt(prompt_id, f"Optimize based on {len(examples)} training examples"))
        else:
            toast_message = "✅ Example saved!"
            if critique:
                toast_message = "✅ Corrected example saved!"
            st.toast(f"{toast_message} ({len(examples)}/3 examples for optimization)")
        
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
        
        # Check if save was successful
        if not saved_prompt:
            raise Exception("Failed to save improved prompt")

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

        # Update the newly generated prompt state to point to the improved version
        st.session_state.newly_generated_prompt = {
            'prompt_data': saved_prompt,
            'improvement_request': task_desc,
            'original_prompt_id': prompt_id
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
        methodology = "**🔄 DSPy-Powered Iterative Refinement Methodology**\n\n"
        methodology += "**Framework:** DSPy Systematic Optimization + AI-Powered Enhancement\n\n"
        methodology += "**Process Steps:**\n\n"
        methodology += "• **📊 Task Definition & Evaluation**\n"
        methodology += "  - Defined DSPy signature for input/output behavior\n"
        methodology += "  - Evaluated current prompt performance\n"
        methodology += "  - Identified improvement opportunities\n\n"
        methodology += "• **📋 Training Data Collection**\n"
        methodology += "  - Integrated user feedback as training examples\n"
        methodology += "  - Leveraged existing training data\n"
        methodology += "  - Ensured data quality and relevance\n\n"
        methodology += "• **🎯 DSPy Optimizer Selection**\n"
        methodology += "  - Chose appropriate optimizer based on data size\n"
        methodology += "  - Configured evaluation metrics\n"
        methodology += "  - Applied systematic optimization strategies\n\n"
        methodology += "• **⚡ DSPy Optimization Execution**\n"
        methodology += "  - Ran iterative prompt optimization\n"
        methodology += "  - Applied few-shot learning techniques\n"
        methodology += "  - Generated optimized prompt instructions\n\n"
        methodology += "• **📈 Version Control & Lineage**\n"
        methodology += "  - Created new version with full history\n"
        methodology += "  - Maintained training data continuity\n"
        methodology += "  - Enabled continuous improvement cycle\n\n"
        methodology += "**DSPy Benefits:**\n"
        methodology += "- Systematic approach to prompt optimization\n"
        methodology += "- Data-driven improvement based on examples\n"
        methodology += "- Robust optimization strategies for different data sizes\n"
        methodology += "- Fallback to basic improvement if DSPy fails\n\n"
        methodology += "**Note:** This process combines DSPy's systematic optimization with traditional prompt engineering for maximum effectiveness."
        return methodology
    else:
        # Text-based improvement
        methodology = "**🧠 DSPy-Powered Prompt Engineering Methodology**\n\n"
        methodology += "**Framework:** DSPy Systematic Optimization + AI-Powered Enhancement\n\n"
        methodology += "**Process Steps:**\n\n"
        methodology += "• **📋 Task Analysis & Signature Definition**\n"
        methodology += "  - Analyzed improvement request for key objectives\n"
        methodology += "  - Defined DSPy signature for input/output mapping\n"
        methodology += "  - Applied systematic prompt engineering principles\n\n"
        methodology += "• **🛡️ Training Data Preparation**\n"
        methodology += "  - Collected relevant training examples\n"
        methodology += "  - Integrated user feedback as training data\n"
        methodology += "  - Ensured data quality and task alignment\n\n"
        methodology += "• **🚀 DSPy Optimizer Selection**\n"
        methodology += "  - Selected appropriate optimizer based on data size\n"
        methodology += "  - Configured evaluation metrics for optimization\n"
        methodology += "  - Applied systematic optimization strategies\n\n"
        methodology += "• **⚡ DSPy Optimization Execution**\n"
        methodology += "  - Ran iterative prompt optimization using DSPy\n"
        methodology += "  - Applied few-shot learning and reasoning\n"
        methodology += "  - Generated optimized prompt instructions\n\n"
        methodology += "• **📊 Version Tracking & Continuity**\n"
        methodology += "  - Created new version with full lineage history\n"
        methodology += "  - Maintained training data for future optimization\n"
        methodology += "  - Enabled continuous improvement and audit trail\n\n"
        methodology += "**DSPy Optimization Strategies:**\n"
        methodology += "- **BootstrapFewShot**: For limited examples (<10)\n"
        methodology += "- **BootstrapFewShotWithRandomSearch**: For moderate data (10-50)\n"
        methodology += "- **MIPROv2**: For larger datasets (50+ examples)\n\n"
        methodology += "**Note:** This systematic approach ensures robust, data-driven prompt optimization with fallback to basic improvement if needed."
        return methodology

def display_improvement_results(context="default"):
    """Display the results of the latest prompt improvement using native Streamlit components."""
    if 'last_improvement' not in st.session_state:
        return
    
    improvement = st.session_state.last_improvement
    
    # Add null checks to prevent TypeError
    if not improvement or not isinstance(improvement, dict):
        st.warning("No improvement results available.")
        return
    
    # Check if required keys exist
    required_keys = ['improvement_request', 'improved_prompt', 'original_prompt', 'methodology']
    missing_keys = [key for key in required_keys if key not in improvement]
    if missing_keys:
        st.error(f"Improvement data is incomplete. Missing: {', '.join(missing_keys)}")
        return
    
    with st.expander("🎯 **Latest Improvement Results**", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**📝 Improvement Request:**")
            improvement_request = improvement.get('improvement_request')
            if improvement_request and isinstance(improvement_request, dict):
                st.info(f"**User Input:** {improvement_request.get('user_input', 'N/A')}")
                st.info(f"**Desired Output:** {improvement_request.get('desired_output', 'N/A')}")
                st.info(f"**Critique:** {improvement_request.get('critique', 'N/A')}")
            elif improvement_request:
                st.info(str(improvement_request))
            else:
                st.info("No improvement request details available.")
        
        with col2:
            st.markdown("**📊 Version Info:**")
            improved_prompt = improvement.get('improved_prompt', {})
            if improved_prompt:
                version = improved_prompt.get('version', 'N/A')
                lineage_id = improved_prompt.get('lineage_id', 'N/A')
                st.metric("Version", version)
                if lineage_id and lineage_id != 'N/A':
                    st.metric("Lineage ID", lineage_id[:8] + "...")
                else:
                    st.metric("Lineage ID", "N/A")
            else:
                st.metric("Version", "N/A")
                st.metric("Lineage ID", "N/A")
        
        # Display changes using native Streamlit components
        st.markdown("**🔍 Changes Made:**")
        
        # Original prompt section
        st.markdown("**📝 Original Prompt:**")
        original_prompt = improvement.get('original_prompt', {})
        if original_prompt and original_prompt.get('prompt'):
            with st.container():
                st.code(original_prompt['prompt'], language='text')
        else:
            st.warning("Original prompt not available.")
        
        st.markdown("---")
        
        # Improved prompt section
        st.markdown("**✨ Improved Prompt:**")
        improved_prompt = improvement.get('improved_prompt', {})
        if improved_prompt and improved_prompt.get('prompt'):
            with st.container():
                st.code(improved_prompt['prompt'], language='text')
        else:
            st.warning("Improved prompt not available.")
        
        # Show key changes if available
        if 'diff_html' in improvement and improvement['diff_html']:
            st.markdown("**🔍 Key Changes:**")
            # Extract changes from the diff (simplified approach)
            original_prompt_text = original_prompt.get('prompt', '') if original_prompt else ''
            improved_prompt_text = improved_prompt.get('prompt', '') if improved_prompt else ''
            
            if original_prompt_text and improved_prompt_text:
                original_lines = original_prompt_text.split('\n')
                improved_lines = improved_prompt_text.split('\n')
            
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
        methodology = improvement.get('methodology', 'No methodology information available.')
        with st.container():
            st.markdown(methodology)
        
        # Add action buttons for testing and improving
        st.markdown("---")
        st.markdown("**🎯 Next Steps:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Test the improved prompt
            test_key = f"test_improved_{hash(str(improvement))}_{context}_{id(improvement)}"
            improved_prompt_id = improved_prompt.get('id') if improved_prompt else None
            if st.button("🧪 Test Improved Prompt", key=test_key, use_container_width=True) and improved_prompt_id:
                st.session_state.testing_prompt_id = improved_prompt_id
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