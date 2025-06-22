# config.py
import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any
import dspy
from functools import lru_cache
from contextvars import ContextVar
import uuid
from pythonjsonlogger import jsonlogger

# Load environment variables first
load_dotenv()
logger = logging.getLogger(__name__)

# --- Correlation ID for Logging ---
request_id_var: ContextVar[str] = ContextVar('request_id', default='unassigned')

class RequestIDFilter(logging.Filter):
    """Injects a request_id from a contextvar into log records."""
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

def setup_logging():
    """Configures logging with a custom filter for request IDs."""
    # Remove any existing handlers to avoid duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])

# Call setup at module load time
setup_logging()

# --- Application Configuration ---
APP_CONFIG = {
    "api_token": os.getenv("API_TOKEN"),
    "api_base_url": os.getenv("API_BASE_URL", "https://api.perplexity.ai"),
    "default_model": os.getenv("DEFAULT_MODEL", "llama-3-sonar-large-32k-online"),
    "connect_timeout": float(os.getenv("CONNECT_TIMEOUT", 10)),
    "read_timeout": float(os.getenv("READ_TIMEOUT", 30)),
    "write_timeout": float(os.getenv("WRITE_TIMEOUT", 30)),
    "pool_timeout": float(os.getenv("POOL_TIMEOUT", 10)),
}

# --- Centralized Model Definitions ---
SUPPORTED_MODELS: Dict[str, str] = {
    'llama-3-sonar-large-32k-online': 'Sonar Large Online',
    'llama-3-sonar-large-32k-chat': 'Sonar Large Chat',
    'llama-3-sonar-small-32k-online': 'Sonar Small Online',
    'llama-3-sonar-small-32k-chat': 'Sonar Small Chat',
    'mistral-7b-instruct': 'Mistral 7B Instruct',
    'sonar-pro': 'Sonar Pro',
}

# --- Error Messages ---
ERROR_MESSAGES: Dict[str, str] = {
    'api_token_missing': 'API_TOKEN is missing from environment variables. The application cannot start.',
    'api_base_url_missing': 'API_BASE_URL is missing. Please check your .env file.',
    'unsupported_model': 'The DEFAULT_MODEL specified in your environment is not in the list of supported models.',
}

@lru_cache(maxsize=None)
def validate_and_load_config() -> Dict[str, Any]:
    """
    Validates critical configuration from environment variables, returning a config dict.
    This is the single source of configuration loading and validation.
    Raises ValueError if a required variable is missing or invalid.
    """
    api_token = os.getenv('API_TOKEN')
    api_base_url = os.getenv('API_BASE_URL', 'https://api.perplexity.ai')
    default_model = os.getenv('DEFAULT_MODEL', next(iter(SUPPORTED_MODELS)))

    if not api_token:
        raise ValueError(ERROR_MESSAGES['api_token_missing'])
    
    if not api_base_url:
        raise ValueError(ERROR_MESSAGES['api_base_url_missing'])
        
    if default_model not in SUPPORTED_MODELS:
        valid_options = ", ".join(f"'{k}'" for k in SUPPORTED_MODELS.keys())
        error = f"{ERROR_MESSAGES['unsupported_model']} Got: '{default_model}'. Please use one of: {valid_options}"
        raise ValueError(error)

    config = {
        "api_token": api_token,
        "api_base_url": api_base_url,
        "default_model": default_model,
        "supported_models": SUPPORTED_MODELS,
        "connect_timeout": int(os.getenv('CONNECT_TIMEOUT', 10)),
        "read_timeout": int(os.getenv('READ_TIMEOUT', 30)),
        "write_timeout": float(os.getenv("WRITE_TIMEOUT", 30)),
        "pool_timeout": float(os.getenv("POOL_TIMEOUT", 10)),
        "log_level": os.getenv('LOG_LEVEL', 'INFO').upper(),
        "debug": os.getenv('DEBUG', 'False').lower() == 'true',
    }
    
    logger.info("✅ Configuration loaded and validated successfully.")
    return config

# This single APP_CONFIG dictionary is used by the rest of the application.
APP_CONFIG = validate_and_load_config()

# --- DSPy Configuration ---
class DspyConfig:
    """Typed configuration for DSPy settings."""
    API_KEY = APP_CONFIG["api_token"]
    API_BASE = APP_CONFIG["api_base_url"]
    MODEL_NAME = APP_CONFIG["default_model"]
    MAX_DEMOS = int(os.getenv("DSPY_MAX_DEMOS", 3))

def get_dspy_lm():
    """Initializes and returns the DSPy language model."""
    if not DspyConfig.API_KEY:
        raise ValueError("API_TOKEN is not set, cannot configure DSPy LM.")
    
    return dspy.OpenAI(
        model=DspyConfig.MODEL_NAME,
        api_key=DspyConfig.API_KEY,
        api_base=DspyConfig.API_BASE
    )
