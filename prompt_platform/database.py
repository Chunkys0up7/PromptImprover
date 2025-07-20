import os
import json
import logging
import time
from contextlib import contextmanager
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Text, 
    inspect, select, func, DateTime, ForeignKey
)
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from jsonschema import validate, ValidationError
from datetime import datetime

from .config import APP_CONFIG
from .schemas import Prompt as PromptSchema

logger = logging.getLogger(__name__)

# --- Database Setup ---
DATABASE_URL = APP_CONFIG.get("database_url", "sqlite:///prompt_storage.db")
Base = declarative_base()

if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_recycle=3600, pool_pre_ping=True)
else:
    # Use StaticPool for SQLite to prevent issues with Streamlit's threading
    from sqlalchemy.pool import StaticPool
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- JSON Schema for Training Data Validation ---
TRAINING_DATA_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {"input": {"type": "string", "minLength": 1}, "output": {"type": "string", "minLength": 1}},
        "required": ["input", "output"],
        "additionalProperties": False
    }
}

# --- Database Models ---
class Example(Base):
    __tablename__ = 'examples'
    id = Column(Integer, primary_key=True)
    prompt_id = Column(String, ForeignKey('prompts.id'), nullable=False)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    critique = Column(Text, nullable=True) # Optional feedback

    prompt = relationship("Prompt", back_populates="examples")

class Prompt(Base):
    __tablename__ = 'prompts'
    id = Column(String, primary_key=True)
    lineage_id = Column(String, nullable=False, index=True)
    parent_id = Column(String, nullable=True)
    task = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    training_data = Column(Text, default='[]')
    improvement_request = Column(Text, nullable=True)  # Store the improvement request
    created_at = Column(Float, default=time.time, index=True)
    model = Column(String, nullable=True)

    examples = relationship("Example", back_populates="prompt", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return PromptSchema.from_orm(self).model_dump()


# --- Main Database Class ---
class PromptDB:
    def __init__(self, session_factory: Optional[sessionmaker] = None):
        Base.metadata.create_all(engine)
        self._session_factory = session_factory or SessionLocal
        self._is_test = session_factory is not None

    @contextmanager
    def session_scope(self) -> Session:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_prompt(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(prompt_data, dict):
            if hasattr(prompt_data, 'model_dump'):
                prompt_data = prompt_data.model_dump()
            else:
                raise ValueError("prompt_data must be a dictionary or a Pydantic model.")
        
        validated_data = PromptSchema(**prompt_data)
        
        with self.session_scope() as session:
            db_data = validated_data.model_dump()
            db_data['training_data'] = json.dumps(db_data['training_data'])
            
            prompt_obj = Prompt(**db_data)
            session.add(prompt_obj)
            session.flush()
            session.refresh(prompt_obj)
            
            saved_dict = prompt_obj.to_dict()

        return saved_dict

    def get_prompt(self, prompt_id: str) -> Optional[dict]:
        with self.session_scope() as session:
            prompt = session.get(Prompt, prompt_id)
            return prompt.to_dict() if prompt else None

    def get_all_prompts(self) -> List[dict]:
        with self.session_scope() as session:
            stmt = select(Prompt).order_by(Prompt.created_at.desc())
            return [p.to_dict() for p in session.scalars(stmt).all()]

    def get_prompts_by_lineage(self, lineage_id: str) -> List[dict]:
        with self.session_scope() as session:
            stmt = (
                select(Prompt)
                .filter_by(lineage_id=lineage_id)
                .order_by(Prompt.version)
            )
            return [p.to_dict() for p in session.scalars(stmt).all()]

    def delete_prompt_lineage(self, lineage_id: str) -> bool:
        with self.session_scope() as session:
            prompts = session.scalars(select(Prompt).filter_by(lineage_id=lineage_id)).all()
            if not prompts:
                return False
            for prompt in prompts:
                session.delete(prompt)
            return True

    def add_training_example(self, prompt_id: str, example: Dict[str, str]) -> bool:
        with self.session_scope() as session:
            prompt = session.get(Prompt, prompt_id)
            if not prompt:
                return False
            
            training_data = json.loads(prompt.training_data or '[]')
            training_data.append(example)
            validate(instance=training_data, schema=TRAINING_DATA_SCHEMA)
            prompt.training_data = json.dumps(training_data, indent=2)
            return True
            
    def add_example(self, prompt_id: str, input_text: str, output_text: str, critique: Optional[str] = None) -> dict:
        """Adds a new training example to the database."""
        with self.session_scope() as session:
            example = Example(
                prompt_id=prompt_id,
                input_text=input_text,
                output_text=output_text,
                critique=critique
            )
            session.add(example)
            session.commit()
            logger.info(f"Added new example for prompt_id {prompt_id} with critique: {bool(critique)}")
            return {
                "id": example.id,
                "prompt_id": example.prompt_id,
                "input_text": example.input_text,
                "output_text": example.output_text,
                "critique": example.critique
            }

    def get_examples(self, prompt_id: int) -> List[dict]:
        """Retrieves all examples for a given prompt."""
        with self.session_scope() as session:
            examples = session.scalars(select(Example).filter_by(prompt_id=prompt_id)).all()
            return [{"id": e.id, "prompt_id": e.prompt_id, "input_text": e.input_text, "output_text": e.output_text, "critique": e.critique} for e in examples]

    def add_correction(self, prompt_id: str, correction_data: Dict[str, str]) -> None:
        """Saves a new correction and its associated data as an Example."""
        self.add_example(
            prompt_id=prompt_id,
            input_text=correction_data['user_input'],
            output_text=correction_data['bad_output'],
            critique=correction_data.get('critique') or correction_data.get('desired_output')
        )

    # --- Dashboard Aggregation Methods ---
    def get_kpi_metrics(self) -> Dict[str, Any]:
        """Calculates key performance indicators for the dashboard."""
        with self.session_scope() as session:
            total_prompts = session.query(Prompt).distinct(Prompt.lineage_id).count()
            total_versions = session.query(Prompt).count()
            total_tests = session.query(Example).count()
            prompts_with_feedback = session.query(Example).distinct(Example.prompt_id).count()
            avg_versions = total_versions / total_prompts if total_prompts > 0 else 0
            feedback_ratio = prompts_with_feedback / total_prompts if total_prompts > 0 else 0
            return {
                "total_prompts": total_prompts,
                "avg_versions": avg_versions,
                "total_tests": total_tests,
                "feedback_ratio": feedback_ratio,
            }

    def count_prompts_by_date(self) -> List[Dict[str, Any]]:
        """Counts the number of prompts created per day."""
        with self.session_scope() as session:
            if session.bind.dialect.name == 'postgresql':
                date_func = func.date_trunc('day', func.to_timestamp(Prompt.created_at))
            else: 
                date_func = func.date(func.datetime(Prompt.created_at, 'unixepoch'))
            stmt = (
                select(date_func.label('date'), func.count(Prompt.id).label('count'))
                .group_by('date')
                .order_by('date')
            )
            return [{'date': row.date, 'count': row.count} for row in session.execute(stmt)]
            
    def count_examples_by_date(self) -> List[Dict[str, Any]]:
        """Counts the cumulative number of training examples added per day."""
        with self.session_scope() as session:
            if session.bind.dialect.name == 'postgresql':
                date_func = func.date_trunc('day', func.to_timestamp(Prompt.created_at))
            else: # Assume SQLite
                date_func = func.date(func.datetime(Prompt.created_at, 'unixepoch'))

            stmt = (
                select(date_func.label('date'), func.sum(func.json_array_length(Prompt.training_data)).label('examples'))
                .where(func.json_array_length(Prompt.training_data) > 0)
                .group_by('date')
                .order_by('date')
            )
            return [{'date': row.date, 'examples': row.examples or 0} for row in session.execute(stmt)]

    def count_versions_per_lineage(self) -> List[Dict[str, Any]]:
        """Counts the number of versions for each prompt lineage."""
        with self.session_scope() as session:
            stmt = (
                select(Prompt.lineage_id, func.count(Prompt.id).label('versions'))
                .group_by(Prompt.lineage_id)
                .order_by(Prompt.lineage_id)
            )
            return [{'lineage_id': row.lineage_id, 'versions': row.versions} for row in session.execute(stmt)] 