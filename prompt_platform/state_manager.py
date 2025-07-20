"""
Centralized state management for the Prompt Platform.

This module provides a clean interface for managing all session state variables
and dialog states, eliminating scattered state manipulation throughout the codebase.
"""
from typing import Any, Dict, Optional, List
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class PromptPlatformState:
    """Centralized state management for the Prompt Platform"""
    
    def __init__(self):
        self._initialize_state()
    
    def _initialize_state(self):
        """Initialize all required session state variables with defaults"""
        defaults = {
            # Chat and testing state
            'test_chat_history': [],
            'test_prompt_id': None,
            'testing_prompt_id': None,
            'review_chat_history': [],
            
            # Dialog states
            'improving_prompt_id': None,
            'viewing_lineage_id': None,
            'dialog_states': {},
            
            # Prompt management
            'pending_prompt_review': None,
            'newly_generated_prompt': None,
            'last_improvement': None,
            'improvement_request': None,
            
            # Performance and metrics
            'app_performance_metrics': {},
            'cache_invalidation_count': 0,
            
            # Request tracking
            'request_id_var': None,
            'uuid': None
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logger.debug(f"Initialized session state: {key} = {default_value}")
    
    def set_active_dialog(self, dialog_type: str, prompt_id: str = None):
        """Manage dialog state with proper cleanup to prevent conflicts"""
        self.clear_all_dialogs()
        if prompt_id:
            st.session_state[f'{dialog_type}_prompt_id'] = prompt_id
        st.session_state.dialog_states[dialog_type] = True
        logger.info(f"Set active dialog: {dialog_type} for prompt {prompt_id}")
    
    def clear_all_dialogs(self):
        """Clear all active dialog states to prevent conflicts"""
        dialog_types = ['testing', 'improving', 'viewing_lineage']
        for dialog_type in dialog_types:
            key = f'{dialog_type}_prompt_id'
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.dialog_states = {}
        logger.debug("Cleared all dialog states")
    
    def get_chat_history(self, context: str = 'default') -> List[Dict[str, str]]:
        """Get chat history for specific context"""
        key = f'{context}_chat_history'
        return st.session_state.get(key, [])
    
    def add_chat_message(self, context: str, role: str, content: str):
        """Add message to specific chat context"""
        key = f'{context}_chat_history' 
        if key not in st.session_state:
            st.session_state[key] = []
        st.session_state[key].append({"role": role, "content": content})
        logger.debug(f"Added {role} message to {context} chat history")
    
    def clear_chat_history(self, context: str = 'default'):
        """Clear chat history for specific context"""
        key = f'{context}_chat_history'
        if key in st.session_state:
            st.session_state[key] = []
            logger.debug(f"Cleared {context} chat history")
    
    def set_pending_prompt_review(self, prompt_data: Dict, task: str):
        """Set pending prompt review state"""
        st.session_state.pending_prompt_review = {
            'prompt_data': prompt_data,
            'task': task,
            'needs_review': True
        }
        logger.info("Set pending prompt review")
    
    def clear_pending_prompt_review(self):
        """Clear pending prompt review state"""
        if 'pending_prompt_review' in st.session_state:
            del st.session_state.pending_prompt_review
        logger.debug("Cleared pending prompt review")
    
    def set_newly_generated_prompt(self, prompt_data: Dict, task: str, show_inline: bool = True):
        """Set newly generated prompt state"""
        st.session_state.newly_generated_prompt = {
            'prompt_data': prompt_data,
            'task': task,
            'should_show_inline': show_inline
        }
        logger.info("Set newly generated prompt")
    
    def clear_newly_generated_prompt(self):
        """Clear newly generated prompt state"""
        if 'newly_generated_prompt' in st.session_state:
            del st.session_state.newly_generated_prompt
        logger.debug("Cleared newly generated prompt")
    
    def set_last_improvement(self, improved_prompt: Dict, original_prompt: Dict, improvement_request: str):
        """Set last improvement state for display"""
        st.session_state.last_improvement = {
            'improved_prompt': improved_prompt,
            'original_prompt': original_prompt,
            'improvement_request': improvement_request,
            'timestamp': st.session_state.get('request_id_var', 'unknown')
        }
        logger.info("Set last improvement state")
    
    def clear_last_improvement(self):
        """Clear last improvement state"""
        if 'last_improvement' in st.session_state:
            del st.session_state.last_improvement
        logger.debug("Cleared last improvement state")
    
    def increment_cache_invalidation(self):
        """Increment cache invalidation counter for performance tracking"""
        st.session_state.cache_invalidation_count += 1
        logger.debug(f"Cache invalidation count: {st.session_state.cache_invalidation_count}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'cache_invalidations': st.session_state.cache_invalidation_count,
            'active_dialogs': len(st.session_state.dialog_states),
            'chat_contexts': len([k for k in st.session_state.keys() if k.endswith('_chat_history')]),
            'pending_reviews': 1 if 'pending_prompt_review' in st.session_state else 0
        }
    
    def handle_active_dialogs(self, dialog_manager):
        """Handle active dialogs in priority order"""
        # Priority order: testing > improving > viewing_lineage
        if st.session_state.testing_prompt_id:
            dialog_manager.test_prompt_dialog(st.session_state.testing_prompt_id)
        elif st.session_state.improving_prompt_id:
            dialog_manager.improve_prompt_dialog(st.session_state.improving_prompt_id)
        elif st.session_state.viewing_lineage_id:
            dialog_manager.view_lineage_dialog(st.session_state.viewing_lineage_id) 