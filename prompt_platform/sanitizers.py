"""
This module provides functions for sanitizing user inputs.
"""
import re
import bleach
import logging

logger = logging.getLogger(__name__)

def sanitize_text(text: str, allow_basic_formatting: bool = False) -> str:
    """
    Cleans user-provided text to prevent injection attacks (XSS) and remove unwanted HTML.

    Args:
        text: The input string to sanitize.
        allow_basic_formatting: If True, allows a safe subset of HTML tags for basic formatting.

    Returns:
        The sanitized text.
    """
    if not isinstance(text, str):
        logger.warning(f"Sanitizer received non-string input of type {type(text)}. Coercing to string.")
        text = str(text)

    # Define allowed tags if basic formatting is permitted
    allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'p', 'br'] if allow_basic_formatting else []
    
    # Use bleach to strip all other tags and attributes
    sanitized_text = bleach.clean(text, tags=allowed_tags, strip=True)
    
    # Optional: A secondary regex to remove any residual markdown-like characters 
    # if they are not desired. This is more for aesthetic cleanup than security.
    # For now, bleach is sufficient for the security aspect.
    # sanitized_text = re.sub(r'[<>{}\[\]#*|`]', '', sanitized_text)
    
    logger.debug("Sanitized text from '%s' to '%s'", text, sanitized_text)
    return sanitized_text 