import uuid
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
import time
import json
from datetime import datetime

class Prompt(BaseModel):
    """
    Pydantic model for a single prompt, providing data validation.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lineage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    version: int = 1
    task: str
    prompt: str
    training_data: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)

    @field_validator('training_data', mode='before')
    @classmethod
    def parse_training_data(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('Invalid JSON format for training_data')
        return v

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        extra = 'ignore' # Ignore extra fields during validation 