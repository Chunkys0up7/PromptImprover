# LLM Provider Integration Guide

This guide provides detailed instructions for switching between different LLM providers in the Prompt Platform, including custom token-based APIs and AWS Bedrock.

## Table of Contents

1. [Current Provider: Perplexity](#current-provider-perplexity)
2. [Custom Token-Based API](#custom-token-based-api)
3. [AWS Bedrock Integration](#aws-bedrock-integration)
4. [OpenAI Integration](#openai-integration)
5. [Anthropic Claude Integration](#anthropic-claude-integration)
6. [Provider Configuration](#provider-configuration)
7. [Environment Variables](#environment-variables)
8. [Testing Your Configuration](#testing-your-configuration)

## Current Provider: Perplexity

The platform currently uses **Perplexity AI** as the default provider.

### Configuration
```bash
# Environment variables for Perplexity
PERPLEXITY_API_KEY=your_perplexity_api_key
LLM_PROVIDER=perplexity
```

### Features
- ✅ **Streaming support** - Real-time response generation
- ✅ **Cost-effective** - Competitive pricing
- ✅ **High quality** - Excellent prompt understanding
- ✅ **Fast responses** - Quick generation times

## Custom Token-Based API

For APIs that require token-based authentication (like your awkward LLM token system), follow this guide:

### 1. Create Custom API Client

Create a new file: `prompt_platform/custom_api_client.py`

```python
"""
Custom API client for token-based LLM providers.
"""
import httpx
import json
import logging
from typing import Generator, Dict, Any, Optional
from .api_client import BaseAPIClient

logger = logging.getLogger(__name__)

class CustomTokenAPIClient(BaseAPIClient):
    """Custom API client for token-based authentication."""
    
    def __init__(self):
        """Initialize custom API client."""
        super().__init__()
        self.base_url = os.getenv('CUSTOM_API_BASE_URL')
        self.auth_url = os.getenv('CUSTOM_AUTH_URL')
        self.client_id = os.getenv('CUSTOM_CLIENT_ID')
        self.client_secret = os.getenv('CUSTOM_CLIENT_SECRET')
        self.access_token = None
        self.token_expires_at = None
        
    def is_configured(self) -> bool:
        """Check if custom API is properly configured."""
        return bool(
            self.base_url and 
            self.auth_url and 
            self.client_id and 
            self.client_secret
        )
    
    def _get_access_token(self) -> Optional[str]:
        """Get access token using client credentials."""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
            
        try:
            auth_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
            
            response = httpx.post(self.auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Set expiration (default to 1 hour if not provided)
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Successfully obtained access token")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to obtain access token: {e}")
            return None
    
    def stream_chat_completion(self, messages: list) -> Generator[str, None, None]:
        """Stream chat completion from custom API."""
        if not self.is_configured():
            raise ValueError("Custom API not configured")
        
        access_token = self._get_access_token()
        if not access_token:
            raise ValueError("Failed to obtain access token")
        
        # Prepare request payload
        payload = {
            'messages': messages,
            'stream': True,
            'model': os.getenv('CUSTOM_MODEL_NAME', 'default-model'),
            'max_tokens': int(os.getenv('CUSTOM_MAX_TOKENS', '1000')),
            'temperature': float(os.getenv('CUSTOM_TEMPERATURE', '0.7'))
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            with httpx.stream('POST', f"{self.base_url}/chat/completions", 
                            json=payload, headers=headers, timeout=60.0) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]  # Remove 'data: ' prefix
                            if data == '[DONE]':
                                break
                            try:
                                json_data = json.loads(data)
                                if 'choices' in json_data and json_data['choices']:
                                    delta = json_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"Error in custom API stream: {e}")
            raise
    
    def chat_completion(self, messages: list) -> str:
        """Non-streaming chat completion from custom API."""
        return ''.join(self.stream_chat_completion(messages))
```

### 2. Environment Variables

```bash
# Custom Token-Based API Configuration
CUSTOM_API_BASE_URL=https://your-api-endpoint.com/api/v1
CUSTOM_AUTH_URL=https://your-auth-endpoint.com/oauth/token
CUSTOM_CLIENT_ID=your_client_id
CUSTOM_CLIENT_SECRET=your_client_secret
CUSTOM_MODEL_NAME=your-model-name
CUSTOM_MAX_TOKENS=1000
CUSTOM_TEMPERATURE=0.7
LLM_PROVIDER=custom_token
```

### 3. Update Configuration

Modify `prompt_platform/config.py`:

```python
# Add to the provider mapping
PROVIDER_MAPPING = {
    'perplexity': 'prompt_platform.api_client.APIClient',
    'custom_token': 'prompt_platform.custom_api_client.CustomTokenAPIClient',
    'bedrock': 'prompt_platform.bedrock_client.BedrockAPIClient',
    'openai': 'prompt_platform.openai_client.OpenAIAPIClient',
    'anthropic': 'prompt_platform.anthropic_client.AnthropicAPIClient'
}
```

## AWS Bedrock Integration

### 1. Install AWS Dependencies

```bash
pip install boto3
```

### 2. Create Bedrock Client

Create `prompt_platform/bedrock_client.py`:

```python
"""
AWS Bedrock API client for the Prompt Platform.
"""
import boto3
import json
import logging
from typing import Generator, Dict, Any
from .api_client import BaseAPIClient

logger = logging.getLogger(__name__)

class BedrockAPIClient(BaseAPIClient):
    """AWS Bedrock API client."""
    
    def __init__(self):
        """Initialize Bedrock client."""
        super().__init__()
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        
        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=self.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
    def is_configured(self) -> bool:
        """Check if Bedrock is properly configured."""
        return bool(
            os.getenv('AWS_ACCESS_KEY_ID') and 
            os.getenv('AWS_SECRET_ACCESS_KEY') and 
            self.model_id
        )
    
    def _format_messages_for_bedrock(self, messages: list) -> str:
        """Format messages for Bedrock Claude format."""
        formatted = ""
        for message in messages:
            role = message['role']
            content = message['content']
            
            if role == 'system':
                formatted += f"System: {content}\n\n"
            elif role == 'user':
                formatted += f"Human: {content}\n\n"
            elif role == 'assistant':
                formatted += f"Assistant: {content}\n\n"
        
        formatted += "Assistant: "
        return formatted
    
    def stream_chat_completion(self, messages: list) -> Generator[str, None, None]:
        """Stream chat completion from Bedrock."""
        if not self.is_configured():
            raise ValueError("Bedrock not configured")
        
        # Format messages for Bedrock
        prompt = self._format_messages_for_bedrock(messages)
        
        # Prepare request body
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": int(os.getenv('BEDROCK_MAX_TOKENS', '1000')),
            "messages": [
                {
                    "role": msg['role'],
                    "content": msg['content']
                }
                for msg in messages
            ],
            "temperature": float(os.getenv('BEDROCK_TEMPERATURE', '0.7'))
        }
        
        try:
            response = self.bedrock_client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            for event in response['body']:
                chunk = json.loads(event['chunk']['bytes'].decode())
                
                if chunk['type'] == 'content_block_delta':
                    if 'text' in chunk['delta']:
                        yield chunk['delta']['text']
                        
        except Exception as e:
            logger.error(f"Error in Bedrock stream: {e}")
            raise
    
    def chat_completion(self, messages: list) -> str:
        """Non-streaming chat completion from Bedrock."""
        return ''.join(self.stream_chat_completion(messages))
```

### 3. Environment Variables for Bedrock

```bash
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_MAX_TOKENS=1000
BEDROCK_TEMPERATURE=0.7
LLM_PROVIDER=bedrock
```

### 4. Available Bedrock Models

```python
# Popular Bedrock Models
BEDROCK_MODELS = {
    'claude-3-sonnet': 'anthropic.claude-3-sonnet-20240229-v1:0',
    'claude-3-haiku': 'anthropic.claude-3-haiku-20240307-v1:0',
    'claude-3-opus': 'anthropic.claude-3-opus-20240229-v1:0',
    'llama-3-8b': 'meta.llama3-8b-instruct-v1:0',
    'llama-3-70b': 'meta.llama3-70b-instruct-v1:0',
    'mistral-7b': 'mistral.mistral-7b-instruct-v0:2',
    'mixtral-8x7b': 'mistral.mixtral-8x7b-instruct-v0:1',
    'titan-express': 'amazon.titan-express-v1',
    'titan-embed': 'amazon.titan-embed-text-v1'
}
```

## OpenAI Integration

### 1. Create OpenAI Client

Create `prompt_platform/openai_client.py`:

```python
"""
OpenAI API client for the Prompt Platform.
"""
import openai
import logging
from typing import Generator, Dict, Any
from .api_client import BaseAPIClient

logger = logging.getLogger(__name__)

class OpenAIAPIClient(BaseAPIClient):
    """OpenAI API client."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        super().__init__()
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_BASE_URL')  # Optional for custom endpoints
        )
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        
    def is_configured(self) -> bool:
        """Check if OpenAI is properly configured."""
        return bool(os.getenv('OPENAI_API_KEY'))
    
    def stream_chat_completion(self, messages: list) -> Generator[str, None, None]:
        """Stream chat completion from OpenAI."""
        if not self.is_configured():
            raise ValueError("OpenAI not configured")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '1000')),
                temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in OpenAI stream: {e}")
            raise
    
    def chat_completion(self, messages: list) -> str:
        """Non-streaming chat completion from OpenAI."""
        return ''.join(self.stream_chat_completion(messages))
```

### 2. Environment Variables for OpenAI

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
LLM_PROVIDER=openai
```

## Anthropic Claude Integration

### 1. Create Anthropic Client

Create `prompt_platform/anthropic_client.py`:

```python
"""
Anthropic Claude API client for the Prompt Platform.
"""
import anthropic
import logging
from typing import Generator, Dict, Any
from .api_client import BaseAPIClient

logger = logging.getLogger(__name__)

class AnthropicAPIClient(BaseAPIClient):
    """Anthropic Claude API client."""
    
    def __init__(self):
        """Initialize Anthropic client."""
        super().__init__()
        self.client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        
    def is_configured(self) -> bool:
        """Check if Anthropic is properly configured."""
        return bool(os.getenv('ANTHROPIC_API_KEY'))
    
    def _convert_messages_format(self, messages: list) -> str:
        """Convert OpenAI format to Anthropic format."""
        system_message = ""
        user_messages = []
        
        for message in messages:
            if message['role'] == 'system':
                system_message = message['content']
            elif message['role'] == 'user':
                user_messages.append(message['content'])
            elif message['role'] == 'assistant':
                # For simplicity, we'll append assistant messages to user messages
                user_messages.append(f"Assistant: {message['content']}")
        
        return system_message, "\n\n".join(user_messages)
    
    def stream_chat_completion(self, messages: list) -> Generator[str, None, None]:
        """Stream chat completion from Anthropic."""
        if not self.is_configured():
            raise ValueError("Anthropic not configured")
        
        system_message, user_message = self._convert_messages_format(messages)
        
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=int(os.getenv('ANTHROPIC_MAX_TOKENS', '1000')),
                temperature=float(os.getenv('ANTHROPIC_TEMPERATURE', '0.7')),
                system=system_message if system_message else None,
                messages=[{"role": "user", "content": user_message}]
            ) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Error in Anthropic stream: {e}")
            raise
    
    def chat_completion(self, messages: list) -> str:
        """Non-streaming chat completion from Anthropic."""
        return ''.join(self.stream_chat_completion(messages))
```

### 2. Environment Variables for Anthropic

```bash
# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=1000
ANTHROPIC_TEMPERATURE=0.7
LLM_PROVIDER=anthropic
```

## Provider Configuration

### 1. Update Configuration File

Modify `prompt_platform/config.py`:

```python
import os
from typing import Dict, Type
from .api_client import BaseAPIClient

# Provider mapping
PROVIDER_MAPPING = {
    'perplexity': 'prompt_platform.api_client.APIClient',
    'custom_token': 'prompt_platform.custom_api_client.CustomTokenAPIClient',
    'bedrock': 'prompt_platform.bedrock_client.BedrockAPIClient',
    'openai': 'prompt_platform.openai_client.OpenAIAPIClient',
    'anthropic': 'prompt_platform.anthropic_client.AnthropicAPIClient'
}

def get_provider_class() -> Type[BaseAPIClient]:
    """Get the appropriate API client class based on configuration."""
    provider = os.getenv('LLM_PROVIDER', 'perplexity').lower()
    
    if provider not in PROVIDER_MAPPING:
        logger.warning(f"Unknown provider '{provider}', falling back to perplexity")
        provider = 'perplexity'
    
    module_path, class_name = PROVIDER_MAPPING[provider].rsplit('.', 1)
    
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import {PROVIDER_MAPPING[provider]}: {e}")
        # Fallback to default
        from .api_client import APIClient
        return APIClient
```

### 2. Update API Client Factory

Modify `prompt_platform/api_client.py`:

```python
from .config import get_provider_class

def create_api_client() -> BaseAPIClient:
    """Create the appropriate API client based on configuration."""
    client_class = get_provider_class()
    return client_class()
```

## Environment Variables

### Complete Environment Configuration

Create a `.env` file with your preferred provider:

```bash
# =============================================================================
# LLM PROVIDER CONFIGURATION
# =============================================================================

# Choose your provider (perplexity, custom_token, bedrock, openai, anthropic)
LLM_PROVIDER=perplexity

# =============================================================================
# PERPLEXITY AI (Current Default)
# =============================================================================
PERPLEXITY_API_KEY=your_perplexity_api_key

# =============================================================================
# CUSTOM TOKEN-BASED API
# =============================================================================
CUSTOM_API_BASE_URL=https://your-api-endpoint.com/api/v1
CUSTOM_AUTH_URL=https://your-auth-endpoint.com/oauth/token
CUSTOM_CLIENT_ID=your_client_id
CUSTOM_CLIENT_SECRET=your_client_secret
CUSTOM_MODEL_NAME=your-model-name
CUSTOM_MAX_TOKENS=1000
CUSTOM_TEMPERATURE=0.7

# =============================================================================
# AWS BEDROCK
# =============================================================================
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_MAX_TOKENS=1000
BEDROCK_TEMPERATURE=0.7

# =============================================================================
# OPENAI
# =============================================================================
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7
OPENAI_BASE_URL=https://api.openai.com/v1

# =============================================================================
# ANTHROPIC CLAUDE
# =============================================================================
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=1000
ANTHROPIC_TEMPERATURE=0.7

# =============================================================================
# GITHUB INTEGRATION
# =============================================================================
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repo_name
```

## Testing Your Configuration

### 1. Test Script

Create `test_providers.py`:

```python
#!/usr/bin/env python3
"""
Test script for different LLM providers.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_provider(provider_name: str):
    """Test a specific provider."""
    print(f"\n🧪 Testing {provider_name.upper()} provider...")
    
    # Set provider
    os.environ['LLM_PROVIDER'] = provider_name
    
    try:
        from prompt_platform.api_client import create_api_client
        client = create_api_client()
        
        if not client.is_configured():
            print(f"❌ {provider_name} not configured properly")
            return False
        
        # Test message
        messages = [
            {"role": "user", "content": "Hello! Please respond with 'Hello from {provider_name}!'"}
        ]
        
        print("📤 Sending test message...")
        response = client.chat_completion(messages)
        print(f"📥 Response: {response}")
        
        print(f"✅ {provider_name} test successful!")
        return True
        
    except Exception as e:
        print(f"❌ {provider_name} test failed: {e}")
        return False

def main():
    """Test all configured providers."""
    providers = ['perplexity', 'custom_token', 'bedrock', 'openai', 'anthropic']
    
    print("🚀 LLM Provider Test Suite")
    print("=" * 50)
    
    results = {}
    for provider in providers:
        results[provider] = test_provider(provider)
    
    print("\n📊 Test Results:")
    print("=" * 50)
    for provider, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{provider:15} {status}")

if __name__ == "__main__":
    main()
```

### 2. Run Tests

```bash
# Test all providers
python test_providers.py

# Test specific provider
LLM_PROVIDER=bedrock python test_providers.py
```

## Switching Providers

### Quick Switch Commands

```bash
# Switch to Bedrock
export LLM_PROVIDER=bedrock
streamlit run prompt_platform/streamlit_app.py

# Switch to OpenAI
export LLM_PROVIDER=openai
streamlit run prompt_platform/streamlit_app.py

# Switch to Custom Token API
export LLM_PROVIDER=custom_token
streamlit run prompt_platform/streamlit_app.py

# Switch back to Perplexity
export LLM_PROVIDER=perplexity
streamlit run prompt_platform/streamlit_app.py
```

### Provider-Specific Features

| Provider | Streaming | Cost | Speed | Quality | Setup Complexity |
|----------|-----------|------|-------|---------|------------------|
| Perplexity | ✅ | Low | Fast | High | Easy |
| Custom Token | ✅ | Variable | Variable | Variable | Medium |
| AWS Bedrock | ✅ | Low | Fast | High | Medium |
| OpenAI | ✅ | High | Fast | High | Easy |
| Anthropic | ✅ | High | Fast | High | Easy |

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all required packages are installed
2. **Authentication Errors**: Verify API keys and credentials
3. **Rate Limits**: Check provider-specific rate limits
4. **Model Availability**: Ensure the specified model is available in your region

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
streamlit run prompt_platform/streamlit_app.py
```

### Provider-Specific Debugging

```python
# Test provider configuration
from prompt_platform.api_client import create_api_client
client = create_api_client()
print(f"Configured: {client.is_configured()}")
print(f"Provider: {client.__class__.__name__}")
```

This comprehensive guide should help you integrate any LLM provider into the Prompt Platform! 