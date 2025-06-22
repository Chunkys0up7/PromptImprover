"""
This module contains shared utility functions for the application.
"""
import asyncio
import difflib

def run_async(coro):
    """Run an async coroutine in a running event loop or a new one."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def get_text_diff(text1: str, text2: str) -> str:
    """
    Generates an HTML side-by-side diff for two texts, including styles
    that are compatible with Streamlit's dark theme.
    """
    style = """
    <style>
        table.diff {
            font-family: Courier, monospace;
            border: medium;
            width: 100%;
            border-collapse: collapse;
        }
        .diff_header {
            background-color: #262730; /* Streamlit's dark background */
            color: #FAFAFA; /* Streamlit's dark text color */
            padding: 4px;
            font-weight: bold;
        }
        td.diff_header {
            text-align:right;
        }
        .diff_next {
            background-color: #41434D;
        }
        .diff_add {
            background-color: #0F5132; /* A dark green */
            color: #FAFAFA;
        }
        .diff_chg {
            background-color: #664D03; /* A dark yellow */
            color: #FAFAFA;
        }
        .diff_sub {
            background-color: #58151C; /* A dark red */
            color: #FAFAFA;
        }
        td {
            padding: 2px 4px;
            white-space: pre-wrap;
            word-break: break-all;
            color: #FAFAFA;
        }
        /* Hide the legend table */
        table.diff ~ table {
            display: none;
        }
    </style>
    """
    
    diff = difflib.HtmlDiff(wrapcolumn=80).make_table(
        fromlines=text1.splitlines(), 
        tolines=text2.splitlines(), 
        fromdesc="Original Prompt", 
        todesc="Improved Prompt"
    )
    
    return style + diff