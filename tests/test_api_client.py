import pytest
from unittest.mock import AsyncMock, patch
from openai import APITimeoutError, AuthenticationError

from prompt_platform.api_client import APIClient, APIConfigurationError, APIAuthError, APITimeoutError as CustomTimeoutError

@pytest.fixture
def mock_app_config():
    """Fixture to provide a mocked APP_CONFIG."""
    return {
        "api_token": "test_token",
        "api_base_url": "https://api.test.com",
        "default_model": "test-model",
        "connect_timeout": 5,
        "read_timeout": 10,
        "write_timeout": 10,
        "pool_timeout": 5,
    }

@patch('prompt_platform.api_client.AsyncOpenAI')
def test_api_client_initialization_success(mock_async_openai, mock_app_config):
    """Tests successful initialization of the APIClient."""
    with patch('prompt_platform.api_client.APP_CONFIG', mock_app_config):
        client = APIClient()
        assert client.is_configured
        mock_async_openai.assert_called_once()

def test_api_client_initialization_no_token():
    """Tests that APIClient raises an error if no API token is provided."""
    with patch('prompt_platform.api_client.APP_CONFIG', {"api_token": None, "api_base_url": "url"}):
        with pytest.raises(APIConfigurationError, match="API_TOKEN is missing"):
            APIClient()

@pytest.mark.asyncio
async def test_get_chat_completion_success(mock_app_config):
    """Tests a successful chat completion call."""
    with patch('prompt_platform.api_client.APP_CONFIG', mock_app_config):
        client = APIClient()
        
        # Mock the response from the OpenAI client
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Hello, world!"
        client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "Say hi"}]
        response = await client.get_chat_completion(messages)
        
        assert response == "Hello, world!"
        client.client.chat.completions.create.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_chat_completion_auth_error(mock_app_config):
    """Tests that an authentication error is correctly handled."""
    with patch('prompt_platform.api_client.APP_CONFIG', mock_app_config):
        client = APIClient()
        client.client.chat.completions.create = AsyncMock(side_effect=AuthenticationError("Invalid token", response=AsyncMock(), body=None))
        
        with pytest.raises(APIAuthError, match="Authentication failed"):
            await client.get_chat_completion([{"role": "user", "content": "test"}])

@pytest.mark.asyncio
async def test_get_chat_completion_timeout_error(mock_app_config):
    """Tests that a timeout error is correctly handled."""
    with patch('prompt_platform.api_client.APP_CONFIG', mock_app_config):
        client = APIClient()
        client.client.chat.completions.create = AsyncMock(side_effect=APITimeoutError("Request timed out"))

        with pytest.raises(CustomTimeoutError, match="Request timed out"):
            await client.get_chat_completion([{"role": "user", "content": "test"}]) 