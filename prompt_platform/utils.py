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
        .diff-container {
            font-family: 'Courier New', monospace;
            background-color: #262730;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
        }
        .diff-section {
            margin-bottom: 16px;
        }
        .diff-label {
            font-weight: bold;
            color: #FAFAFA;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .diff-content {
            background-color: #1e1e1e;
            border-radius: 4px;
            padding: 12px;
            border-left: 4px solid #6c757d;
            white-space: pre-wrap;
            word-break: break-word;
            color: #e9ecef;
            font-size: 13px;
            line-height: 1.4;
        }
        .diff-added {
            background-color: #1a3a1a;
            border-left-color: #28a745;
            color: #d4edda;
        }
        .diff-removed {
            background-color: #3a1a1a;
            border-left-color: #dc3545;
            color: #f8d7da;
        }
        .diff-changed {
            background-color: #3a2f1a;
            border-left-color: #ffc107;
            color: #fff3cd;
        }
    </style>
    """
    
    # Create a cleaner diff display
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    
    html_parts = [style, '<div class="diff-container">']
    
    # Original section
    html_parts.append('<div class="diff-section">')
    html_parts.append('<div class="diff-label">📝 Original Prompt:</div>')
    html_parts.append('<div class="diff-content">')
    html_parts.append(text1)
    html_parts.append('</div></div>')
    
    # Improved section
    html_parts.append('<div class="diff-section">')
    html_parts.append('<div class="diff-label">✨ Improved Prompt:</div>')
    html_parts.append('<div class="diff-content">')
    html_parts.append(text2)
    html_parts.append('</div></div>')
    
    # Show specific changes if there are any
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            changes.append(f"Lines {i1+1}-{i2}: Replaced with new content")
        elif tag == 'delete':
            changes.append(f"Lines {i1+1}-{i2}: Removed")
        elif tag == 'insert':
            changes.append(f"Lines {j1+1}-{j2}: Added")
    
    if changes:
        html_parts.append('<div class="diff-section">')
        html_parts.append('<div class="diff-label">🔍 Key Changes:</div>')
        html_parts.append('<div class="diff-content">')
        for change in changes:
            html_parts.append(f'• {change}<br>')
        html_parts.append('</div></div>')
    
    html_parts.append('</div>')
    
    return ''.join(html_parts)