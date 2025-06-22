"""
Prompt Version Manager (in-memory)
- Tracks prompt versions for the session
- Placeholders for future database integration
"""

import time
from typing import List, Dict, Any, Optional
import logging
# from .database import db # No longer needed, db is injected
import streamlit as st

logger = logging.getLogger(__name__)

class VersionManager:
    """
    Manages the version history of prompts, providing methods
    to retrieve and format prompt lineage.
    """
    
    def __init__(self, db):
        self.db = db

    @st.cache_data
    def get_lineage(_self, lineage_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all prompts belonging to a specific lineage, sorted by version.
        This operation is cached to prevent redundant database queries.
        """
        logger.info(f"Fetching lineage for ID: {lineage_id} from database.")
        return _self.db.get_prompts_by_lineage(lineage_id)

    def format_lineage_table(self, lineage_prompts: list) -> str:
        """Formats a list of prompt versions into a Markdown table."""
        if not lineage_prompts:
            return "No lineage found."

        # Sort prompts by version, safely handling missing 'version' keys.
        # Prompts without a version are treated as version 0.
        sorted_prompts = sorted(lineage_prompts, key=lambda p: p.get('version', 0))

        # Create the Markdown table header
        headers = ["Version", "Prompt Snippet", "Created At"]
        table = "| " + " | ".join(headers) + " |\n"
        table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        # Populate the table rows
        for prompt in sorted_prompts:
            version = prompt.get('version', 'N/A')
            snippet = prompt.get('prompt', '')[:80].replace('\n', ' ') + '...'
            created_at = prompt.get('created_at', 'N/A')
            
            row = [
                f"`v{version}`",
                f"`{snippet}`",
                f"`{created_at}`"
            ]
            table += "| " + " | ".join(row) + " |\n"
            
        return table
