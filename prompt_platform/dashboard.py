import streamlit as st
import pandas as pd
# from .database import db # No longer needed

@st.cache_data
def fetch_kpi_metrics():
    """Fetches key performance indicators from the database."""
    return st.session_state.db.get_kpi_metrics()

@st.cache_data
def fetch_prompt_trends():
    """Fetches prompt creation trend data and prepares it for charting."""
    data = st.session_state.db.count_prompts_by_date()
    if not data:
        return pd.DataFrame(columns=['date', 'count']).set_index('date')
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date')

@st.cache_data
def fetch_example_growth():
    """Fetches training example growth data and prepares it for charting."""
    data = st.session_state.db.count_examples_by_date()
    if not data:
        return pd.DataFrame(columns=['date', 'examples']).set_index('date')
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    # Calculate cumulative sum for growth chart
    df['examples'] = df['examples'].cumsum()
    return df.set_index('date')

@st.cache_data
def fetch_version_distribution():
    """Fetches version distribution data and prepares it for charting."""
    data = st.session_state.db.count_versions_per_lineage()
    if not data:
        return pd.DataFrame(columns=['lineage_id', 'versions']).set_index('lineage_id')
    return pd.DataFrame(data).set_index('lineage_id')

def render_kpi_metrics():
    """Renders the main KPI metrics."""
    st.subheader("📊 Key Performance Indicators")
    metrics = fetch_kpi_metrics()
    cols = st.columns(3)
    cols[0].metric("Total Prompts", metrics.get('total_prompts', 0))
    cols[1].metric("Total Good Examples Saved", metrics.get('total_examples', 0))
    cols[2].metric("Average Versions per Prompt", metrics.get('avg_versions', 0.0))

def render_prompt_trends():
    """Renders the prompt creation trends chart."""
    df = fetch_prompt_trends()
    st.subheader("📈 Prompt Creation Trends")
    if not df.empty:
        st.line_chart(df['count'])
    else:
        st.info("No prompt creation data available yet.")

def render_example_growth():
    """Renders the training example growth chart."""
    df = fetch_example_growth()
    st.subheader("🌱 Training Example Growth")
    if not df.empty:
        st.line_chart(df['examples'])
    else:
        st.info("No training examples have been saved yet.")

def render_version_distribution():
    """Renders the version distribution chart."""
    df = fetch_version_distribution()
    st.subheader("📚 Version Distribution per Lineage")
    if not df.empty:
        st.bar_chart(df['versions'])
    else:
        st.info("No version data available yet.")

def render_dashboard():
    """Renders the full dashboard."""
    st.title("🚀 Prompt Performance Dashboard")
    render_kpi_metrics()
    
    st.divider()
    render_prompt_trends()

    st.divider()
    render_example_growth()
    
    st.divider()
    render_version_distribution() 