"""
Modern CSS styles for the Prompt Platform.

This module provides organized, maintainable CSS styles that work with
the Streamlit theme configuration and support modern UI patterns.
"""

def load_custom_styles():
    """Load modular CSS styles with modern design patterns"""
    return """
    /* Modern CSS using Streamlit 1.39+ key-based styling */
    
    /* Main header styling */
    .main-header { 
        font-size: 2.5rem; 
        font-weight: 700; 
        color: var(--primary-color, #667eea); 
        text-align: center; 
        margin-bottom: 2rem; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        background-clip: text;
    }
    
    /* Enhanced button styling with modern gradients */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color, #667eea) 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: var(--base-radius, 8px);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.25);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Primary action buttons - more specific selectors */
    .stButton > button[data-testid*="test_"]:not(:disabled),
    .stButton > button[data-testid*="improve_"]:not(:disabled) {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        border: 2px solid #3b82f6 !important;
        font-weight: 700 !important;
    }
    
    .stButton > button[data-testid*="test_"]:not(:disabled):hover,
    .stButton > button[data-testid*="improve_"]:not(:disabled):hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Secondary action buttons */
    .stButton > button[data-testid*="optimize_"]:not(:disabled),
    .stButton > button[data-testid*="lineage_"]:not(:disabled),
    .stButton > button[data-testid*="commit_"]:not(:disabled) {
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important;
        border: 2px solid #6b7280 !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[data-testid*="optimize_"]:not(:disabled):hover,
    .stButton > button[data-testid*="lineage_"]:not(:disabled):hover,
    .stButton > button[data-testid*="commit_"]:not(:disabled):hover {
        background: linear-gradient(135deg, #4b5563 0%, #374151 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(107, 114, 128, 0.4) !important;
    }
    
    /* Destructive action button */
    .stButton > button[data-testid*="delete_"]:not(:disabled) {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        border: 2px solid #ef4444 !important;
        font-weight: 600 !important;
        color: white !important;
    }
    
    .stButton > button[data-testid*="delete_"]:not(:disabled):hover {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important;
    }
    
    /* Disabled buttons */
    .stButton > button:disabled {
        background: linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%) !important;
        border-color: #d1d5db !important;
        color: #6b7280 !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
        opacity: 0.6 !important;
    }
    
    /* Prompt container styling */
    .prompt-container { 
        border: 1px solid var(--border-color, #e5e7eb); 
        border-radius: 0.75rem; 
        padding: 1.5rem; 
        margin: 1rem 0; 
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }
    
    .prompt-container:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transform: translateY(-1px);
    }
    
    /* Button group styling */
    .prompt-actions { 
        margin: 1rem 0; 
    }
    
    .prompt-actions .stButton { 
        margin: 0.25rem !important;
        display: inline-block !important;
    }
    
    .prompt-actions .stButton > button { 
        margin: 0.25rem 0; 
        font-size: 0.9rem; 
        min-height: 2.5rem; 
        border-radius: 0.375rem; 
        transition: all 0.2s ease; 
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* Visual separators */
    .prompt-separator { 
        border-top: 2px solid var(--border-color, #e5e7eb); 
        margin: 1rem 0; 
        opacity: 0.6; 
    }
    
    /* Focus states for accessibility */
    .stButton > button:focus {
        outline: 2px solid var(--primary-color, #3b82f6) !important;
        outline-offset: 2px !important;
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .main-header {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .prompt-container {
            background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
            border-color: #374151;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        }
    }
    
    /* Responsive design */
    @container (max-width: 768px) {
        .prompt-container {
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .main-header {
            font-size: 2rem;
        }
        
        .stButton > button {
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
        }
    }
    
    /* Animation for loading states */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    /* Enhanced form styling */
    .stForm > div {
        border-radius: var(--base-radius, 8px);
        border: 1px solid var(--border-color, #e5e7eb);
        padding: 1rem;
        background: var(--secondary-background-color, #f8fafc);
    }
    
    /* Code block styling */
    .stCodeBlock {
        border-radius: var(--base-radius, 8px);
        border: 1px solid var(--border-color, #e5e7eb);
        background: var(--code-background-color, #f8fafc);
    }
    
    /* Metric styling */
    .stMetric {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: var(--base-radius, 8px);
        padding: 1rem;
        border: 1px solid var(--border-color, #e5e7eb);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--base-radius, 8px);
        background: var(--secondary-background-color, #f8fafc);
        border: 1px solid var(--border-color, #e5e7eb);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-color, #667eea);
        color: white;
    }
    """

def load_dark_mode_styles():
    """Load dark mode specific styles"""
    return """
    /* Dark mode overrides */
    [data-theme="dark"] {
        --primary-color: #4f46e5;
        --secondary-color: #7c3aed;
        --background-color: #111827;
        --secondary-background-color: #1f2937;
        --text-color: #f9fafb;
        --border-color: #374151;
        --code-background-color: #1f2937;
    }
    
    [data-theme="dark"] .main-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    [data-theme="dark"] .prompt-container {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border-color: #374151;
    }
    
    [data-theme="dark"] .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    }
    """

def load_animation_styles():
    """Load animation and transition styles"""
    return """
    /* Smooth transitions for all interactive elements */
    * {
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Hover animations */
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Loading spinner animation */
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .loading-spinner {
        animation: spin 1s linear infinite;
    }
    
    /* Fade in animation for new content */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    """ 