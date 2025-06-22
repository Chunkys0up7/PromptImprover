import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from prompt_platform.prompt_generator import PromptGenerator
from prompt_platform.database import db
import uuid
import time

pytestmark = pytest.mark.asyncio

@pytest.fixture
def sample_prompt_data():
    """Provides a sample prompt dictionary for testing."""
    lineage_id = str(uuid.uuid4())
    return {
        "id": str(uuid.uuid4()),
        "lineage_id": lineage_id,
        "parent_id": None,
        "task": "Test Task",
        "prompt": "This is a test prompt.",
        "version": 1,
        "created_at": time.time(),
        "model": "test-model"
    }

@pytest.fixture
def mock_api_client():
    """Fixture to provide a mock APIClient."""
    return AsyncMock()

@pytest.fixture
def mock_db():
    """Fixture to provide a mock PromptDB."""
    return MagicMock()

@pytest.fixture
def prompt_generator():
    """Fixture to provide a PromptGenerator instance."""
    with patch('prompt_platform.prompt_generator.get_dspy_lm', return_value=MagicMock()):
        return PromptGenerator()

@pytest.fixture
def sample_prompt_for_opt(test_db):
    """Provides a sample prompt saved in the test DB for optimization tests."""
    prompt_data = {
        "id": "opt-test-123",
        "lineage_id": "lineage-123",
        "task": "Optimization Task",
        "prompt": "Initial prompt to be optimized.",
        "version": 1,
        "training_data": [
            {"input": "test input", "output": "expected output"}
        ]
    }
    test_db.save_prompt(prompt_data)
    return prompt_data

@pytest.mark.asyncio
async def test_generate_initial_prompt(prompt_generator, mock_api_client):
    """Tests the generation of a new prompt."""
    mock_api_client.get_chat_completion.return_value = "This is a test prompt with {{input}}."
    result = await prompt_generator.generate_initial_prompt("test task", mock_api_client)
    
    assert result['task'] == "test task"
    assert result['prompt'] == "This is a test prompt with {{input}}."
    assert "lineage_id" in result

@pytest.mark.asyncio
async def test_improve_prompt(prompt_generator, mock_api_client, mock_db):
    """Tests improving an existing prompt."""
    prompt_id = "test_prompt_id"
    original_prompt = {
        "id": prompt_id,
        "prompt": "Original prompt",
        "task": "Original task",
        "lineage_id": "lineage123",
        "version": 1,
        "training_data": []
    }
    mock_db.get_prompt.return_value = original_prompt
    mock_api_client.get_chat_completion.return_value = "This is the improved prompt."

    result = await prompt_generator.improve_prompt(prompt_id, "Make it better", mock_api_client, mock_db)

    mock_db.get_prompt.assert_called_once_with(prompt_id)
    assert result['prompt'] == "This is the improved prompt."
    assert result['parent_id'] == prompt_id
    assert result['version'] == 2

@pytest.mark.asyncio
async def test_improve_prompt_not_found(prompt_generator, mock_api_client, mock_db):
    """Tests that improve_prompt raises ValueError if the prompt is not found."""
    prompt_id = "non_existent_id"
    mock_db.get_prompt.return_value = None

    with pytest.raises(ValueError, match=f"Original prompt with ID {prompt_id} not found."):
        await prompt_generator.improve_prompt(prompt_id, "Make it better", mock_api_client, mock_db)

@pytest.mark.asyncio
async def test_optimize_prompt_no_training_data(prompt_generator):
    """Tests that optimization is skipped if there is no training data."""
    prompt_data = {"id": "1", "prompt": "test", "training_data": "[]"}
    
    with pytest.raises(ValueError, match="Optimization requires at least one training example."):
        await prompt_generator.optimize_prompt(prompt_data)

def test_create_prompt_data(prompt_generator):
    """
    Tests that prompt data can be created with proper validation.
    """
    # Arrange
    prompt_data = {
        "prompt": "Test prompt",
        "task": "Test Task",
        "lineage_id": "test-lineage",
        "version": 1
    }

    # Act
    result = prompt_generator._create_prompt_data(**prompt_data)

    # Assert
    assert result['task'] == "Test Task"
    assert result['prompt'] == "Test prompt"
    assert result['version'] == 1
    assert 'id' in result
