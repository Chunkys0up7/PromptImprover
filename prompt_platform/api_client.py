import os
import logging
from .config import APP_CONFIG
import httpx
from typing import List, Dict
from openai import (
    AsyncOpenAI,
    Timeout,
    APITimeoutError as OpenAITimeoutError, # Rename to avoid conflict
    APIConnectionError,
    BadRequestError,
    AuthenticationError,
    RateLimitError,
    APIStatusError,
)

logger = logging.getLogger(__name__)

# --- Custom Exceptions ---
class APIConfigurationError(Exception):
    """Raised when the API client is not configured correctly."""
    pass

class APITimeoutError(Exception):
    """Raised when an API request times out."""
    pass

class APIAuthError(Exception):
    """Raised for authentication-related errors (401, 403)."""
    pass

class APIResponseError(Exception):
    """Raised for other non-successful API responses."""
    pass


class APIClient:
    """A client to interact with the Perplexity API via the OpenAI SDK."""
    def __init__(self):
        self.api_key = APP_CONFIG["api_token"]
        self.base_url = APP_CONFIG["api_base_url"]
        
        if not self.api_key:
            raise APIConfigurationError("API_TOKEN is missing. Cannot initialize APIClient.")

        try:
            # Configure separate connect and read timeouts for robustness
            timeout_config = Timeout(
                connect=APP_CONFIG.get("connect_timeout", 10),
                read=APP_CONFIG.get("read_timeout", 30),
                write=APP_CONFIG.get("write_timeout", 30),
                pool=APP_CONFIG.get("pool_timeout", 10)
            )
            self.client = AsyncOpenAI(
                api_key=self.api_key, 
                base_url=self.base_url,
                timeout=timeout_config
            )
            self.is_configured = True
            logger.info("APIClient initialized successfully for Perplexity.")
        except ValueError as e:
            logger.error(f"Timeout configuration error: {e}", exc_info=True)
            self.client = None
            self.is_configured = False
            raise APIConfigurationError(
                "Failed to configure timeouts. Specify all four parameters "
                "(connect, read, write, pool) or a default value."
            )
        except Exception as e:
            logger.error(f"Failed to initialize APIClient: {e}", exc_info=True)
            self.client = None
            self.is_configured = False
            raise APIConfigurationError(f"Failed to initialize OpenAI client: {e}")

    async def stream_chat_completion(self, messages: List[Dict[str, str]]):
        """Streams a chat completion response from the API."""
        if not self.is_configured:
            raise APIConfigurationError("API Client is not configured.")

        try:
            stream = await self.client.chat.completions.create(
                model=APP_CONFIG["default_model"],
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except OpenAITimeoutError as e:
            logger.error(f"API request timed out: {e}", exc_info=True)
            raise APITimeoutError(f"Request timed out: {e}") from e
        except APIConnectionError as e:
            logger.error(f"API connection error: {e}", exc_info=True)
            raise APIResponseError(f"Failed to connect to API: {e}") from e
        except BadRequestError as e:
            logger.error(f"Invalid request to API: {e}", exc_info=True)
            raise APIResponseError(f"Invalid request: {e.param}") from e
        except AuthenticationError as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            raise APIAuthError(f"Authentication failed. Check your API token.") from e
        except RateLimitError as e:
            logger.error(f"API rate limit exceeded: {e}", exc_info=True)
            raise APIResponseError("API rate limit exceeded. Please try again later.") from e
        except APIStatusError as e:
            logger.error(f"API returned non-200 status: {e.status_code} {e.response}", exc_info=True)
            raise APIResponseError(f"API returned an error: {e.status_code}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during chat completion: {e}", exc_info=True)
            raise APIResponseError(f"An unexpected error occurred: {e}") from e

    async def get_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Gets a chat completion from the Perplexity API."""
        if not self.is_configured:
            raise APIConfigurationError("API client is not configured. Check API_TOKEN.")
        
        logger.debug("Calling get_chat_completion with %d messages.", len(messages))
        try:
            response = await self.client.chat.completions.create(
                model=APP_CONFIG["default_model"],
                messages=messages,
            )
            content = response.choices[0].message.content or ""
            logger.debug("API response successfully received: %r", content[:100] + "...")
            return content
        except OpenAITimeoutError as e:
            logger.error("API request timed out: %s", e, exc_info=True)
            raise APITimeoutError(f"Request timed out after {APP_CONFIG.get('read_timeout', 30)}s.") from e
        except APIConnectionError as e:
            logger.error(f"API connection error: {e}", exc_info=True)
            raise APIResponseError(f"Failed to connect to API: {e}") from e
        except BadRequestError as e:
            logger.error(f"Invalid request to API: {e.message}", exc_info=True)
            raise APIResponseError(f"Invalid request: {e.param if e.param else 'unknown'}") from e
        except AuthenticationError as e:
            logger.error("Authentication error: %s", e, exc_info=True)
            raise APIAuthError("Authentication failed. Check your API token.") from e
        except RateLimitError as e:
            logger.error(f"API rate limit exceeded: {e}", exc_info=True)
            raise APIResponseError("API rate limit exceeded. Please try again later.") from e
        except APIStatusError as e:
            logger.error("API request failed with status %d: %s", e.response.status_code, e.response.text, exc_info=True)
            raise APIResponseError(f"API Error: {e.response.status_code} - {e.response.text}") from e
        except Exception as e:
            logger.error("An unexpected error occurred during chat completion: %s", e, exc_info=True)
            raise APIResponseError(f"An unexpected error occurred: {e}") from e 