"""
Centralized error handling and user feedback for the Prompt Platform.

This module provides comprehensive error handling with user-friendly messages
and proper logging for debugging.
"""
import logging
from contextlib import contextmanager
from typing import Optional, Callable, Any
import streamlit as st
import traceback

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling and user feedback"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
    
    @contextmanager
    def handle_errors(self, operation_name: str, show_user_error: bool = True, 
                     fallback_value: Any = None, log_level: str = "ERROR"):
        """Context manager for error handling with user feedback"""
        try:
            yield
        except Exception as e:
            self._log_error(operation_name, e, log_level)
            
            if show_user_error:
                self._show_user_friendly_error(operation_name, e)
            
            if fallback_value is not None:
                return fallback_value
    
    def _log_error(self, operation: str, error: Exception, log_level: str = "ERROR"):
        """Log error with proper formatting"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Increment error count
        error_key = f"{operation}_{error_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log with appropriate level
        log_message = f"Error in {operation}: {error_type} - {error_message}"
        
        if log_level.upper() == "DEBUG":
            self.logger.debug(log_message, exc_info=True)
        elif log_level.upper() == "INFO":
            self.logger.info(log_message, exc_info=True)
        elif log_level.upper() == "WARNING":
            self.logger.warning(log_message, exc_info=True)
        else:  # ERROR
            self.logger.error(log_message, exc_info=True)
    
    def _show_user_friendly_error(self, operation: str, error: Exception):
        """Show user-friendly error messages with helpful context"""
        error_type = type(error).__name__
        
        # Define user-friendly error messages
        error_messages = {
            'DatabaseError': {
                'title': "🗄️ Database Connection Issue",
                'message': "There was a problem connecting to the database. Please try again.",
                'suggestion': "If this persists, check your database configuration."
            },
            'APIConfigurationError': {
                'title': "🔧 API Configuration Error",
                'message': "The API client is not properly configured.",
                'suggestion': "Please check your API settings in the Settings tab."
            },
            'APIAuthError': {
                'title': "🔑 API Authentication Error",
                'message': "Your API token is invalid or expired.",
                'suggestion': "Please update your API token in the Settings tab or check your account balance."
            },
            'APITimeoutError': {
                'title': "⏱️ Request Timeout",
                'message': "The request took too long to complete.",
                'suggestion': "Please try again. If the problem persists, the service may be busy."
            },
            'APIResponseError': {
                'title': "🌐 API Service Error",
                'message': "The API service returned an error.",
                'suggestion': "Please check your API configuration and try again."
            },
            'ValueError': {
                'title': "⚠️ Invalid Input",
                'message': "The provided input is not valid.",
                'suggestion': "Please check your input and try again."
            },
            'ValidationError': {
                'title': "⚠️ Validation Error",
                'message': "The data provided doesn't meet the required format.",
                'suggestion': "Please check your input format and try again."
            },
            'TimeoutError': {
                'title': "⏱️ Operation Timeout",
                'message': "The operation timed out.",
                'suggestion': "Please try again. If the problem persists, try a simpler request."
            },
            'ConnectionError': {
                'title': "🌐 Connection Error",
                'message': "Unable to connect to the service.",
                'suggestion': "Please check your internet connection and try again."
            },
            'AttributeError': {
                'title': "🔧 System Configuration Issue",
                'message': "There's a configuration issue with the system.",
                'suggestion': "Please try refreshing the page. If the problem persists, contact support."
            },
            'TypeError': {
                'title': "🔧 Data Format Issue",
                'message': "There's an issue with the data format.",
                'suggestion': "Please try refreshing the page or restart the application."
            },
            'JSONDecodeError': {
                'title': "📄 Data Format Error",
                'message': "There's an issue with the data format.",
                'suggestion': "Please try refreshing the page or restart the application."
            }
        }
        
        # Get error info
        error_info = error_messages.get(error_type, {
            'title': "❌ Unexpected Error",
            'message': f"An unexpected error occurred in {operation}.",
            'suggestion': "Please try again. If the problem persists, contact support."
        })
        
        # Display error with expandable details
        with st.error(error_info['title']):
            st.write(error_info['message'])
            st.write(f"**Suggestion:** {error_info['suggestion']}")
            
            # Show error details in expander for debugging
            with st.expander("🔍 Error Details (for debugging)", expanded=False):
                st.code(f"""
Error Type: {error_type}
Error Message: {str(error)}
Operation: {operation}
Error Count: {self.error_counts.get(f'{operation}_{error_type}', 1)}
                """)
                
                # Show full traceback in code block
                st.code(traceback.format_exc(), language='python')
    
    def handle_async_operation(self, coro, operation_name: str, timeout: int = 30):
        """Handle async operations with proper error handling"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = asyncio.wait_for(coro, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(f"Operation {operation_name} timed out after {timeout} seconds")
            finally:
                loop.close()
                
        except Exception as e:
            self._log_error(operation_name, e)
            self._show_user_friendly_error(operation_name, e)
            return None
    
    def get_error_summary(self) -> dict:
        """Get summary of errors for monitoring"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': self.error_counts.copy(),
            'most_common_error': max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        }
    
    def clear_error_counts(self):
        """Clear error count tracking"""
        self.error_counts.clear()
        logger.info("Cleared error counts")

def safe_execute(func: Callable, *args, operation_name: str = "operation", 
                fallback_value: Any = None, **kwargs) -> Any:
    """Safely execute a function with error handling"""
    error_handler = ErrorHandler()
    
    with error_handler.handle_errors(operation_name, fallback_value=fallback_value):
        return func(*args, **kwargs)

def show_error_summary():
    """Display error summary in the UI"""
    if 'error_handler' in st.session_state:
        summary = st.session_state.error_handler.get_error_summary()
        
        if summary['total_errors'] > 0:
            st.subheader("⚠️ Error Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Errors", summary['total_errors'])
            
            with col2:
                if summary['most_common_error']:
                    error_type, count = summary['most_common_error']
                    st.metric("Most Common", f"{error_type} ({count})")
            
            # Show error breakdown
            if summary['error_types']:
                st.write("**Error Breakdown:**")
                for error_type, count in summary['error_types'].items():
                    st.write(f"• {error_type}: {count}")
            
            # Clear errors button
            if st.button("Clear Error Counts"):
                st.session_state.error_handler.clear_error_counts()
                st.rerun() 