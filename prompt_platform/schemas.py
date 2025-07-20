"""
Comprehensive data schemas and validation for the Prompt Platform.

This module provides Pydantic models for all data structures used in the application,
ensuring type safety, validation, and consistent data handling.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
import json
import logging

logger = logging.getLogger(__name__)

# --- Base Models ---

class BasePromptModel(BaseModel):
    """Base model for prompt-related data"""
    
    class Config:
        # Allow extra fields for backward compatibility
        extra = "allow"
        # Use enum values for validation
        use_enum_values = True
        # Validate assignment
        validate_assignment = True

# --- Core Prompt Models ---

class PromptSchema(BasePromptModel):
    """Schema for prompt data validation"""
    
    id: str = Field(..., description="Unique identifier for the prompt")
    lineage_id: str = Field(..., description="Lineage identifier for version tracking")
    parent_id: Optional[str] = Field(None, description="Parent prompt ID for versioning")
    task: str = Field(..., min_length=1, max_length=1000, description="Task description")
    prompt: str = Field(..., min_length=1, max_length=10000, description="The actual prompt text")
    version: int = Field(..., ge=1, description="Version number")
    training_data: Union[str, List[Dict[str, str]]] = Field(
        default="[]", 
        description="Training data as JSON string or list of examples"
    )
    improvement_request: Optional[str] = Field(None, description="Improvement request description")
    generation_process: Optional[str] = Field(None, description="Generation process explanation")
    created_at: Union[float, datetime] = Field(..., description="Creation timestamp")
    model: Optional[str] = Field(None, description="Model used for generation")
    
    @validator('training_data', pre=True)
    def validate_training_data(cls, v):
        """Validate and normalize training data"""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if not isinstance(parsed, list):
                    raise ValueError("Training data must be a list")
                return v
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in training_data")
        elif isinstance(v, list):
            # Convert list to JSON string for storage
            return json.dumps(v)
        else:
            raise ValueError("Training data must be a string or list")
    
    @validator('created_at', pre=True)
    def validate_created_at(cls, v):
        """Normalize created_at to float timestamp"""
        if isinstance(v, datetime):
            return v.timestamp()
        elif isinstance(v, (int, float)):
            return float(v)
        else:
            raise ValueError("created_at must be datetime or numeric timestamp")
    
    @validator('task')
    def validate_task(cls, v):
        """Validate task description"""
        if not v or not v.strip():
            raise ValueError("Task description cannot be empty")
        return v.strip()
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate prompt text"""
        if not v or not v.strip():
            raise ValueError("Prompt text cannot be empty")
        return v.strip()

class ExampleSchema(BaseModel):
    """Schema for training example data"""
    
    id: Optional[int] = Field(None, description="Example ID")
    prompt_id: str = Field(..., description="Associated prompt ID")
    input_text: str = Field(..., min_length=1, max_length=5000, description="Input text")
    output_text: str = Field(..., min_length=1, max_length=10000, description="Expected output text")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    critique: Optional[str] = Field(None, description="Optional feedback/critique")
    
    @validator('input_text')
    def validate_input_text(cls, v):
        """Validate input text"""
        if not v or not v.strip():
            raise ValueError("Input text cannot be empty")
        return v.strip()
    
    @validator('output_text')
    def validate_output_text(cls, v):
        """Validate output text"""
        if not v or not v.strip():
            raise ValueError("Output text cannot be empty")
        return v.strip()

# --- API Request/Response Models ---

class PromptGenerationRequest(BaseModel):
    """Schema for prompt generation requests"""
    
    task: str = Field(..., min_length=1, max_length=1000, description="Task description")
    model: Optional[str] = Field(None, description="Model to use for generation")
    context: Optional[str] = Field(None, description="Additional context")
    
    @validator('task')
    def validate_task(cls, v):
        """Validate task description"""
        if not v or not v.strip():
            raise ValueError("Task description cannot be empty")
        return v.strip()

class PromptImprovementRequest(BaseModel):
    """Schema for prompt improvement requests"""
    
    prompt_id: str = Field(..., description="ID of prompt to improve")
    task_description: str = Field(..., min_length=1, max_length=1000, description="Improvement description")
    user_input: Optional[str] = Field(None, description="Example user input")
    bad_output: Optional[str] = Field(None, description="Undesired output")
    desired_output: Optional[str] = Field(None, description="Desired output")
    critique: Optional[str] = Field(None, description="Additional critique")
    
    @validator('task_description')
    def validate_task_description(cls, v):
        """Validate task description"""
        if not v or not v.strip():
            raise ValueError("Task description cannot be empty")
        return v.strip()

class TestPromptRequest(BaseModel):
    """Schema for prompt testing requests"""
    
    prompt_id: str = Field(..., description="ID of prompt to test")
    user_input: str = Field(..., min_length=1, max_length=5000, description="Test input")
    model: Optional[str] = Field(None, description="Model to use for testing")
    
    @validator('user_input')
    def validate_user_input(cls, v):
        """Validate user input"""
        if not v or not v.strip():
            raise ValueError("User input cannot be empty")
        return v.strip()

class TestPromptResponse(BaseModel):
    """Schema for prompt testing responses"""
    
    prompt_id: str = Field(..., description="ID of tested prompt")
    user_input: str = Field(..., description="Original user input")
    assistant_response: str = Field(..., description="AI assistant response")
    model_used: str = Field(..., description="Model used for response")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    tokens_used: Optional[int] = Field(None, description="Tokens used in response")

# --- Feedback Models ---

class FeedbackSchema(BaseModel):
    """Schema for user feedback on prompt outputs"""
    
    prompt_id: str = Field(..., description="ID of the prompt")
    user_input: str = Field(..., description="Original user input")
    assistant_response: str = Field(..., description="AI assistant response")
    feedback_type: str = Field(..., pattern="^(good|bad)$", description="Type of feedback")
    desired_output: Optional[str] = Field(None, description="Desired output for bad feedback")
    critique: Optional[str] = Field(None, description="Additional critique")
    created_at: Optional[datetime] = Field(None, description="Feedback timestamp")
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        """Validate feedback type"""
        if v not in ['good', 'bad']:
            raise ValueError("Feedback type must be 'good' or 'bad'")
        return v
    
    @validator('desired_output')
    def validate_desired_output(cls, v, values):
        """Validate desired output is provided for bad feedback"""
        if values.get('feedback_type') == 'bad' and not v:
            raise ValueError("Desired output is required for bad feedback")
        return v

# --- Configuration Models ---

class APIConfig(BaseModel):
    """Schema for API configuration"""
    
    api_token: str = Field(..., description="API authentication token")
    api_base_url: str = Field(..., description="API base URL")
    default_model: str = Field(..., description="Default model to use")
    connect_timeout: int = Field(default=10, ge=1, le=60, description="Connection timeout in seconds")
    read_timeout: int = Field(default=30, ge=1, le=300, description="Read timeout in seconds")
    write_timeout: int = Field(default=30, ge=1, le=300, description="Write timeout in seconds")
    pool_timeout: int = Field(default=10, ge=1, le=60, description="Pool timeout in seconds")
    
    @validator('api_token')
    def validate_api_token(cls, v):
        """Validate API token"""
        if not v or not v.strip():
            raise ValueError("API token cannot be empty")
        return v.strip()
    
    @validator('api_base_url')
    def validate_api_base_url(cls, v):
        """Validate API base URL"""
        if not v or not v.strip():
            raise ValueError("API base URL cannot be empty")
        if not v.startswith(('http://', 'https://')):
            raise ValueError("API base URL must start with http:// or https://")
        return v.strip()

class DatabaseConfig(BaseModel):
    """Schema for database configuration"""
    
    database_url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=10, ge=1, le=50, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, le=100, description="Maximum overflow connections")
    pool_recycle: int = Field(default=3600, ge=300, le=7200, description="Pool recycle time in seconds")
    pool_pre_ping: bool = Field(default=True, description="Enable pool pre-ping")
    
    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL"""
        if not v or not v.strip():
            raise ValueError("Database URL cannot be empty")
        return v.strip()

# --- Dashboard Models ---

class PerformanceMetrics(BaseModel):
    """Schema for performance metrics"""
    
    total_prompts: int = Field(..., ge=0, description="Total number of prompts")
    total_examples: int = Field(..., ge=0, description="Total number of training examples")
    total_lineages: int = Field(..., ge=0, description="Total number of prompt lineages")
    avg_versions_per_lineage: float = Field(..., ge=0, description="Average versions per lineage")
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Recent activity data")
    top_prompts: List[Dict[str, Any]] = Field(default_factory=list, description="Top prompts by version count")
    prompt_trends: List[Dict[str, Any]] = Field(default_factory=list, description="Prompt creation trends")
    example_growth: List[Dict[str, Any]] = Field(default_factory=list, description="Training example growth")

# --- Validation Utilities ---

def validate_training_data_format(data: Union[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    """Validate and normalize training data format"""
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            if not isinstance(parsed, list):
                raise ValueError("Training data must be a list")
            return parsed
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in training data")
    elif isinstance(data, list):
        # Validate each example
        for i, example in enumerate(data):
            if not isinstance(example, dict):
                raise ValueError(f"Example {i} must be a dictionary")
            if 'input' not in example or 'output' not in example:
                raise ValueError(f"Example {i} must contain 'input' and 'output' keys")
            if not isinstance(example['input'], str) or not isinstance(example['output'], str):
                raise ValueError(f"Example {i} input and output must be strings")
        return data
    else:
        raise ValueError("Training data must be a string or list")

def validate_prompt_data(data: Dict[str, Any]) -> PromptSchema:
    """Validate prompt data and return validated schema"""
    try:
        return PromptSchema(**data)
    except Exception as e:
        logger.error(f"Prompt data validation failed: {e}")
        raise ValueError(f"Invalid prompt data: {e}")

def validate_example_data(data: Dict[str, Any]) -> ExampleSchema:
    """Validate example data and return validated schema"""
    try:
        return ExampleSchema(**data)
    except Exception as e:
        logger.error(f"Example data validation failed: {e}")
        raise ValueError(f"Invalid example data: {e}")

# --- Export all schemas ---

__all__ = [
    'BasePromptModel',
    'PromptSchema',
    'ExampleSchema',
    'PromptGenerationRequest',
    'PromptImprovementRequest',
    'TestPromptRequest',
    'TestPromptResponse',
    'FeedbackSchema',
    'APIConfig',
    'DatabaseConfig',
    'PerformanceMetrics',
    'validate_training_data_format',
    'validate_prompt_data',
    'validate_example_data'
] 