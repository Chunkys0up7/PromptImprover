import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_performance_stats():
    """Fetches comprehensive performance statistics."""
    return st.session_state.db.get_performance_stats()

@st.cache_data(ttl=300)
def fetch_recent_prompts():
    """Fetches the most recent prompts."""
    return st.session_state.db.get_recent_prompts(limit=5)

@st.cache_data(ttl=300)
def fetch_top_prompts():
    """Fetches prompts with the most versions."""
    return st.session_state.db.get_top_prompts_by_versions(limit=5)

@st.cache_data(ttl=300)
def fetch_prompt_trends():
    """Fetches prompt creation trend data and prepares it for charting."""
    data = st.session_state.db.count_prompts_by_date()
    if not data:
        return pd.DataFrame(columns=['date', 'count']).set_index('date')
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date')

@st.cache_data(ttl=300)
def fetch_example_growth():
    """Fetches training example growth data and prepares it for charting."""
    data = st.session_state.db.count_examples_by_date()
    if not data:
        return pd.DataFrame(columns=['date', 'examples']).set_index('date')
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['examples'] = df['examples'].cumsum()
    return df.set_index('date')

def format_time_ago(timestamp):
    """Formats a timestamp as a human-readable time ago string."""
    if not timestamp:
        return "Unknown"
    
    # Convert timestamp to datetime
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = timestamp
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def render_performance_overview():
    """Renders the main performance overview with enhanced metrics."""
    stats = fetch_performance_stats()
    
    st.markdown("### 📊 Performance Overview")
    
    # Main metrics in a grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Prompts",
            value=stats.get('total_prompts', 0),
            help="Number of unique prompt lineages created"
        )
    
    with col2:
        st.metric(
            label="Total Versions",
            value=stats.get('total_versions', 0),
            help="Total number of prompt versions across all lineages"
        )
    
    with col3:
        st.metric(
            label="Improvement Rate",
            value=f"{stats.get('improvement_rate', 0)}%",
            help="Percentage of prompts that have been improved"
        )
    
    with col4:
        st.metric(
            label="Avg Versions/Prompt",
            value=stats.get('avg_versions_per_prompt', 0),
            help="Average number of versions per prompt lineage"
        )
    
    # Secondary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Training Examples",
            value=stats.get('total_examples', 0),
            help="Total number of training examples saved"
        )
    
    with col2:
        st.metric(
            label="Recent Activity (7d)",
            value=stats.get('recent_prompts_7d', 0),
            help="New prompts created in the last 7 days"
        )
    
    with col3:
        st.metric(
            label="Recent Improvements (7d)",
            value=stats.get('recent_improvements_7d', 0),
            help="Prompts improved in the last 7 days"
        )

def render_recent_activity():
    """Renders recent prompt activity."""
    recent_prompts = fetch_recent_prompts()
    
    st.markdown("### 🕒 Recent Activity")
    
    if recent_prompts:
        for prompt in recent_prompts:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{prompt['task'][:60]}{'...' if len(prompt['task']) > 60 else ''}**")
                    st.caption(f"Version {prompt['version']} • {format_time_ago(prompt['created_at'])}")
                
                with col2:
                    st.markdown(f"**{prompt['version']}**")
                    st.caption("versions")
                
                with col3:
                    if prompt.get('training_data'):
                        training_count = len(prompt['training_data']) if isinstance(prompt['training_data'], list) else 0
                        st.markdown(f"**{training_count}**")
                        st.caption("examples")
                    else:
                        st.markdown("**0**")
                        st.caption("examples")
                
                st.divider()
    else:
        st.info("No recent prompts found. Create your first prompt to see activity here!")

def render_top_prompts():
    """Renders the most improved prompts."""
    top_prompts = fetch_top_prompts()
    
    st.markdown("### 🏆 Most Improved Prompts")
    
    if top_prompts:
        for prompt in top_prompts:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{prompt['task'][:60]}{'...' if len(prompt['task']) > 60 else ''}**")
                    st.caption(f"Latest: v{prompt['latest_version']} • {format_time_ago(prompt['created_at'])}")
                
                with col2:
                    st.markdown(f"**{prompt['version_count']}**")
                    st.caption("versions")
                
                with col3:
                    improvement_emoji = "🚀" if prompt['version_count'] >= 5 else "📈" if prompt['version_count'] >= 3 else "📊"
                    st.markdown(f"{improvement_emoji}")
                    st.caption("status")
                
                st.divider()
    else:
        st.info("No improved prompts yet. Start improving your prompts to see them here!")

def render_trends():
    """Renders trend charts."""
    st.markdown("### 📈 Trends & Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Prompt Creation Trends")
        df_trends = fetch_prompt_trends()
        if not df_trends.empty:
            st.line_chart(df_trends['count'])
        else:
            st.info("No trend data available yet.")
    
    with col2:
        st.markdown("#### Training Example Growth")
        df_examples = fetch_example_growth()
        if not df_examples.empty:
            st.line_chart(df_examples['examples'])
        else:
            st.info("No training data available yet.")

def render_quick_actions():
    """Renders quick action buttons."""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Create New Prompt", use_container_width=True):
            st.switch_page("Generate")
    
    with col2:
        if st.button("📋 Manage Prompts", use_container_width=True):
            st.switch_page("Manage")
    
    with col3:
        if st.button("⚙️ Settings", use_container_width=True):
            st.switch_page("Settings")

def render_dashboard():
    """Renders the enhanced dashboard."""
    st.title("🚀 Prompt Performance Dashboard")
    st.markdown("*Track your prompt engineering progress and performance*")
    
    # Performance overview
    render_performance_overview()
    
    st.divider()
    
    # Recent activity and top prompts in columns
    col1, col2 = st.columns(2)
    
    with col1:
        render_recent_activity()
    
    with col2:
        render_top_prompts()
    
    st.divider()
    
    # Trends
    render_trends()
    
    st.divider()
    
    # Quick actions
    render_quick_actions() 