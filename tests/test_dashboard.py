import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import streamlit as st

# Make sure the app can find the prompt_platform module
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prompt_platform.dashboard import (
    fetch_kpi_metrics,
    fetch_prompt_trends,
    fetch_example_growth,
    fetch_version_distribution,
    render_kpi_metrics,
    render_dashboard,
)

@pytest.fixture
def mock_db():
    """Fixture to create a mock database object."""
    with patch('prompt_platform.dashboard.db', new_callable=MagicMock) as mock_db_instance:
        yield mock_db_instance

def test_fetch_kpi_metrics(mock_db):
    """Test fetching Key Performance Indicators."""
    mock_db.get_kpi_metrics.return_value = {
        'total_prompts': 10,
        'total_examples': 50,
        'avg_versions': 2.5
    }
    metrics = fetch_kpi_metrics()
    assert metrics['total_prompts'] == 10
    assert metrics['avg_versions'] == 2.5
    mock_db.get_kpi_metrics.assert_called_once()

def test_fetch_prompt_trends(mock_db):
    """Test fetching prompt trend data."""
    mock_data = [{'date': '2023-01-01', 'count': 5}, {'date': '2023-01-02', 'count': 10}]
    mock_db.count_prompts_by_date.return_value = mock_data
    
    df = fetch_prompt_trends()
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.index.name == 'date'
    assert 'count' in df.columns
    assert pd.to_datetime('2023-01-01') in df.index
    mock_db.count_prompts_by_date.assert_called_once()

def test_fetch_prompt_trends_no_data(mock_db):
    """Test fetching prompt trend data when none exists."""
    # Clear the cache for this specific test to avoid interference
    fetch_prompt_trends.clear()
    
    mock_db.count_prompts_by_date.return_value = []
    
    df = fetch_prompt_trends()
    
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    mock_db.count_prompts_by_date.assert_called_once()

def test_fetch_example_growth(mock_db):
    """Test fetching and processing example growth data."""
    mock_data = [{'date': '2023-01-01', 'examples': 10}, {'date': '2023-01-02', 'examples': 15}]
    mock_db.count_examples_by_date.return_value = mock_data

    df = fetch_example_growth()
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    # Test that the cumulative sum is calculated correctly
    assert df.loc[pd.to_datetime('2023-01-02')]['examples'] == 25
    mock_db.count_examples_by_date.assert_called_once()

def test_fetch_version_distribution(mock_db):
    """Test fetching version distribution data."""
    mock_data = [{'lineage_id': 'abc', 'versions': 3}, {'lineage_id': 'def', 'versions': 5}]
    mock_db.count_versions_per_lineage.return_value = mock_data
    
    df = fetch_version_distribution()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.loc['def']['versions'] == 5
    mock_db.count_versions_per_lineage.assert_called_once()

# Basic "smoke tests" for rendering functions to ensure they run without errors.
# These don't check the visual output, just that the functions can be called
# with mocked data without raising exceptions.
@patch('prompt_platform.dashboard.st')
def test_render_kpi_metrics_smoke(mock_st, mock_db):
    """Smoke test for the KPI rendering function."""
    mock_db.get_kpi_metrics.return_value = {}
    try:
        render_kpi_metrics()
    except Exception as e:
        pytest.fail(f"render_kpi_metrics raised an exception: {e}")

@patch('prompt_platform.dashboard.st')
def test_render_dashboard_smoke(mock_st, mock_db):
    """Smoke test for the main dashboard rendering function."""
    mock_db.get_kpi_metrics.return_value = {}
    mock_db.count_prompts_by_date.return_value = []
    mock_db.count_examples_by_date.return_value = []
    mock_db.count_versions_per_lineage.return_value = []
    try:
        # Clear all st.cache_data caches before running
        st.cache_data.clear()
        render_dashboard()
    except Exception as e:
        pytest.fail(f"render_dashboard raised an exception: {e}") 