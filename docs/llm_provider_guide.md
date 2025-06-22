# LLM Provider Integration Guide

This guide details how to configure the Prompt Engineering Platform to use different Large Language Model (LLM) providers beyond the default Perplexity API.

## 1. Using Any OpenAI-Compatible API

The platform's `APIClient` is built on OpenAI's official Python SDK, making it compatible with any API that follows the OpenAI specification (e.g., Together AI, Anyscale, local models served with LiteLLM).

### Configuration

To switch to a different OpenAI-compatible provider, update your `.env` file with the provider's specific credentials:

```env
# .env

# The API key for the new provider
API_TOKEN="your_provider_api_key"

# The base URL for the provider's API endpoint
API_BASE_URL="https://api.your-provider.com/v1"

# The specific model identifier for the provider's model
DEFAULT_MODEL="provider/model-name"
```

1.  **`API_TOKEN`**: Your new provider's API key.
2.  **`API_BASE_URL`**: The new provider's base endpoint for chat completions.
3.  **`DEFAULT_MODEL`**: The exact model string that the new provider expects. You must also add this model string to the `SUPPORTED_MODELS` dictionary in `prompt_platform/config.py` for it to be validated correctly.

After updating the `.env` file, restart the Streamlit application. No code changes are necessary.

---

## 2. Integrating a Non-OpenAI-Compatible API (e.g., AWS Bedrock)

Integrating providers that use a different SDK and authentication mechanism, like AWS Bedrock, requires code modifications. The following is a recommended strategy for making `api_client.py` extensible.

### Proposed Refactoring Strategy

The core idea is to introduce an abstract base class for the API client and create concrete implementations for each provider.

**Step A: Create an Abstract Base Client**

Define an abstract base class in `api_client.py` that specifies the required interface.

```python
# prompt_platform/api_client.py
from abc import ABC, abstractmethod

class BaseAPIClient(ABC):
    @abstractmethod
    async def get_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        pass

    @abstractmethod
    async def stream_chat_completion(self, messages: List[Dict[str, str]]):
        pass
```

**Step B: Refactor the Existing Client**

Rename the current `APIClient` to `OpenAIClient` and make it inherit from `BaseAPIClient`.

```python
# prompt_platform/api_client.py
class OpenAIClient(BaseAPIClient):
    # All existing code from APIClient goes here...
    # No changes needed to the method implementations.
```

**Step C: Implement a New Client for AWS Bedrock**

Create a new class, `BedrockClient`, that implements the `BaseAPIClient` interface using the `boto3` SDK.

**Prerequisites:**
- Install the `boto3` library: `pip install boto3`
- Configure your AWS credentials (typically via `~/.aws/credentials` or IAM roles).

**Example Implementation:**
```python
# prompt_platform/api_client.py
import boto3
import json

class BedrockClient(BaseAPIClient):
    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name="us-east-1") # Or your region
        self.model_id = APP_CONFIG["default_model"] # e.g., "anthropic.claude-3-sonnet-20240229-v1:0"

    async def get_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        # Bedrock has a different input format
        prompt = messages[-1]['content'] # Simplified for example
        body = json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 4000,
        })
        response = self.client.invoke_model(body=body, modelId=self.model_id)
        response_body = json.loads(response.get('body').read())
        return response_body.get('completion')

    async def stream_chat_completion(self, messages: List[Dict[str, str]]):
        # ... implementation for streaming response ...
        prompt = messages[-1]['content']
        body = json.dumps({"prompt": f"\n\nHuman: {prompt}\n\nAssistant:", "max_tokens_to_sample": 4000})
        response = self.client.invoke_model_with_response_stream(body=body, modelId=self.model_id)
        for event in response.get('body'):
            chunk = json.loads(event['chunk']['bytes'])
            yield chunk['completion']
```

**Step D: Create a Factory Function**

In `config.py` or `api_client.py`, create a factory function that returns the correct client based on the configuration.

```python
# In config.py
def get_llm_api_client():
    """Factory function to get the configured API client."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "bedrock":
        # Make sure to add Bedrock model IDs to SUPPORTED_MODELS
        from .api_client import BedrockClient
        return BedrockClient()
    elif provider == "openai":
        from .api_client import OpenAIClient
        return OpenAIClient()
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
```

Finally, update the application (`streamlit_app.py` and `pages/1_Manager.py`) to call this factory function instead of `APIClient()` directly. This makes the application adaptable to new LLM providers with minimal friction. 