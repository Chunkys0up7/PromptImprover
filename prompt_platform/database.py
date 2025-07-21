"""
Database management and ORM for the Prompt Platform.

This module provides SQLAlchemy-based database operations for prompts,
versions, and training examples with comprehensive data validation.
"""
import logging
import json
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

# Import our comprehensive schemas
from .schemas import (
    PromptSchema, ExampleSchema, validate_prompt_data, 
    validate_example_data, validate_training_data_format
)

logger = logging.getLogger(__name__)

Base = declarative_base()

# --- Database Models ---

class Prompt(Base):
    """SQLAlchemy model for prompts with comprehensive validation"""
    __tablename__ = 'prompts'
    
    id = Column(String, primary_key=True)
    lineage_id = Column(String, nullable=False, index=True)
    parent_id = Column(String, nullable=True)
    task = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    training_data = Column(Text, nullable=False, default='[]')
    improvement_request = Column(Text, nullable=True)
    generation_process = Column(Text, nullable=True)
    created_at = Column(Float, nullable=False)
    model = Column(String, nullable=True)
    
    # Relationship to examples
    examples = relationship("Example", back_populates="prompt", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary with validation"""
        data = {
            'id': self.id,
            'lineage_id': self.lineage_id,
            'parent_id': self.parent_id,
            'task': self.task,
            'prompt': self.prompt,
            'version': self.version,
            'training_data': self.training_data,
            'improvement_request': self.improvement_request,
            'generation_process': self.generation_process,
            'created_at': self.created_at,
            'model': self.model
        }
        # Validate the data using our schema
        validated = PromptSchema(**data)
        return validated.dict()

class Example(Base):
    """SQLAlchemy model for training examples with validation"""
    __tablename__ = 'examples'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(String, ForeignKey('prompts.id'), nullable=False)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    critique = Column(Text, nullable=True)
    
    # Relationship to prompt
    prompt = relationship("Prompt", back_populates="examples")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary with validation"""
        data = {
            'id': self.id,
            'prompt_id': self.prompt_id,
            'input_text': self.input_text,
            'output_text': self.output_text,
            'created_at': self.created_at,
            'critique': self.critique
        }
        # Validate the data using our schema
        validated = ExampleSchema(**data)
        return validated.dict()

# --- Database Manager ---

class PromptDB:
    """Database manager with comprehensive validation and error handling"""
    
    def __init__(self, database_url: str = None):
        """Initialize database with validation"""
        if database_url is None:
            database_url = "sqlite:///prompts.db"
        
        self.engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized with URL: {database_url}")
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def save_prompt(self, prompt_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save prompt with comprehensive validation and return saved data"""
        try:
            # Validate prompt data using our schema
            validated_data = validate_prompt_data(prompt_data)
            
            with self.session_scope() as session:
                # Check if prompt already exists
                existing = session.query(Prompt).filter(Prompt.id == validated_data.id).first()
                
                if existing:
                    # Update existing prompt
                    for key, value in validated_data.dict().items():
                        if key != 'id':  # Don't update the ID
                            setattr(existing, key, value)
                    logger.info(f"Updated existing prompt: {validated_data.id}")
                    return existing.to_dict()
                else:
                    # Create new prompt
                    prompt = Prompt(**validated_data.dict())
                    session.add(prompt)
                    session.flush()  # Ensure the ID is generated
                    logger.info(f"Created new prompt: {validated_data.id}")
                    return prompt.to_dict()
                
        except Exception as e:
            logger.error(f"Failed to save prompt: {e}")
            return None
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get prompt by ID with validation"""
        try:
            with self.session_scope() as session:
                prompt = session.query(Prompt).filter(Prompt.id == prompt_id).first()
                
                if prompt:
                    return prompt.to_dict()
                return None
                
        except Exception as e:
            logger.error(f"Failed to get prompt {prompt_id}: {e}")
            return None
    
    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts with validation"""
        try:
            with self.session_scope() as session:
                prompts = session.query(Prompt).order_by(Prompt.created_at.desc()).all()
                return [prompt.to_dict() for prompt in prompts]
                
        except Exception as e:
            logger.error(f"Failed to get all prompts: {e}")
            return []
    
    def get_prompts_by_lineage(self, lineage_id: str) -> List[Dict[str, Any]]:
        """Get all prompts in a lineage with validation"""
        try:
            with self.session_scope() as session:
                prompts = session.query(Prompt).filter(
                    Prompt.lineage_id == lineage_id
                ).order_by(Prompt.version.asc()).all()
                
                return [prompt.to_dict() for prompt in prompts]
                
        except Exception as e:
            logger.error(f"Failed to get prompts for lineage {lineage_id}: {e}")
            return []
    
    def delete_prompt_lineage(self, lineage_id: str) -> bool:
        """Delete entire prompt lineage"""
        try:
            with self.session_scope() as session:
                prompts = session.query(Prompt).filter(Prompt.lineage_id == lineage_id).all()
                
                for prompt in prompts:
                    session.delete(prompt)
                
                logger.info(f"Deleted lineage {lineage_id} with {len(prompts)} prompts")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete lineage {lineage_id}: {e}")
            return False
    
    def add_example(self, example_data: Dict[str, Any]) -> bool:
        """Add training example with validation"""
        try:
            # Validate example data using our schema
            validated_data = validate_example_data(example_data)
            
            with self.session_scope() as session:
                example = Example(**validated_data.dict())
                session.add(example)
                logger.info(f"Added example for prompt: {validated_data.prompt_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add example: {e}")
            return False
    
    def get_examples(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get training examples for a prompt with validation"""
        try:
            with self.session_scope() as session:
                examples = session.query(Example).filter(
                    Example.prompt_id == prompt_id
                ).order_by(Example.created_at.asc()).all()
                
                return [example.to_dict() for example in examples]
                
        except Exception as e:
            logger.error(f"Failed to get examples for prompt {prompt_id}: {e}")
            return []
    
    def delete_example(self, example_id: int) -> bool:
        """Delete training example"""
        try:
            with self.session_scope() as session:
                example = session.query(Example).filter(Example.id == example_id).first()
                
                if example:
                    session.delete(example)
                    logger.info(f"Deleted example: {example_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete example {example_id}: {e}")
            return False
    
    # --- Dashboard Aggregation Methods ---
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        try:
            with self.session_scope() as session:
                # Get basic counts
                total_prompts = session.query(Prompt).count()
                total_examples = session.query(Example).count()
                total_lineages = session.query(Prompt.lineage_id).distinct().count()
                
                # Get average examples per prompt
                example_counts = session.query(
                    func.count(Example.id).label('count')
                ).group_by(Example.prompt_id).subquery()
                avg_examples = session.query(func.avg(example_counts.c.count)).scalar() or 0
                
                # Get recent activity (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_prompts = session.query(Prompt).filter(Prompt.created_at >= week_ago.timestamp()).count()
                recent_examples = session.query(Example).filter(Example.created_at >= week_ago).count()
                
                return {
                    'total_prompts': total_prompts,
                    'total_examples': total_examples,
                    'total_lineages': total_lineages,
                    'avg_examples_per_prompt': round(float(avg_examples), 2),
                    'recent_prompts': recent_prompts,
                    'recent_examples': recent_examples
                }
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {
                'total_prompts': 0,
                'total_examples': 0,
                'total_lineages': 0,
                'avg_examples_per_prompt': 0,
                'recent_prompts': 0,
                'recent_examples': 0
            }
    
    def get_prompt_performance_stats(self, prompt_id: str) -> Dict[str, Any]:
        """Get performance statistics for a specific prompt"""
        try:
            with self.session_scope() as session:
                # Get prompt details
                prompt = session.query(Prompt).filter(Prompt.id == prompt_id).first()
                if not prompt:
                    return {}
                
                # Get examples for this prompt
                examples = session.query(Example).filter(Example.prompt_id == prompt_id).all()
                
                # Get lineage information
                lineage_prompts = session.query(Prompt).filter(Prompt.lineage_id == prompt.lineage_id).all()
                
                # Calculate statistics
                total_examples = len(examples)
                avg_example_length = sum(len(ex.output_text) for ex in examples) / total_examples if total_examples > 0 else 0
                
                # Get recent examples (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_examples = session.query(Example).filter(
                    Example.prompt_id == prompt_id,
                    Example.created_at >= week_ago
                ).count()
                
                return {
                    'prompt_id': prompt_id,
                    'lineage_id': prompt.lineage_id,
                    'version': prompt.version,
                    'total_examples': total_examples,
                    'avg_example_length': round(avg_example_length, 2),
                    'recent_examples': recent_examples,
                    'lineage_size': len(lineage_prompts),
                    'created_at': prompt.created_at,
                    'improvement_request': prompt.improvement_request
                }
        except Exception as e:
            logger.error(f"Failed to get prompt performance stats for {prompt_id}: {e}")
            return {}
    
    def get_recent_prompts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent prompts for dashboard"""
        try:
            with self.session_scope() as session:
                prompts = session.query(Prompt).order_by(
                    Prompt.created_at.desc()
                ).limit(limit).all()
                
                return [prompt.to_dict() for prompt in prompts]
                
        except Exception as e:
            logger.error(f"Failed to get recent prompts: {e}")
            return []
    
    def get_top_prompts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top prompts by version count"""
        try:
            with self.session_scope() as session:
                # Get prompts with the most versions in their lineage
                subquery = session.query(
                    Prompt.lineage_id,
                    func.count(Prompt.id).label('version_count'),
                    func.max(Prompt.version).label('latest_version')
                ).group_by(Prompt.lineage_id).subquery()
                
                top_lineages = session.query(
                    Prompt.lineage_id,
                    Prompt.task,
                    Prompt.created_at,
                    subquery.c.version_count,
                    subquery.c.latest_version
                ).join(
                    subquery, Prompt.lineage_id == subquery.c.lineage_id
                ).order_by(
                    subquery.c.version_count.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'lineage_id': lineage.lineage_id,
                        'task': lineage.task,
                        'created_at': lineage.created_at,
                        'version_count': lineage.version_count,
                        'latest_version': lineage.latest_version
                    }
                    for lineage in top_lineages
                ]
        except Exception as e:
            logger.error(f"Failed to get top prompts: {e}")
            return []
    
    def get_top_prompts_by_versions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top prompts by version count (alias for get_top_prompts)"""
        return self.get_top_prompts(limit)
    
    def count_prompts_by_date(self, days: int = 30) -> List[Dict[str, Any]]:
        """Count prompts created by date for trend analysis"""
        try:
            with self.session_scope() as session:
                # Get prompts created in the last N days
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Query prompts by date
                results = session.query(
                    func.date(func.datetime(Prompt.created_at, 'unixepoch')).label('date'),
                    func.count(Prompt.id).label('count')
                ).filter(
                    Prompt.created_at >= start_date.timestamp()
                ).group_by(
                    func.date(func.datetime(Prompt.created_at, 'unixepoch'))
                ).order_by(
                    func.date(func.datetime(Prompt.created_at, 'unixepoch'))
                ).all()
                
                return [
                    {
                        'date': result.date,
                        'count': result.count
                    }
                    for result in results
                ]
        except Exception as e:
            logger.error(f"Failed to count prompts by date: {e}")
            return []
    
    def count_examples_by_date(self, days: int = 30) -> List[Dict[str, Any]]:
        """Count examples created by date for trend analysis"""
        try:
            with self.session_scope() as session:
                # Get examples created in the last N days
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Query examples by date
                results = session.query(
                    func.date(Example.created_at).label('date'),
                    func.count(Example.id).label('examples')
                ).filter(
                    Example.created_at >= start_date
                ).group_by(
                    func.date(Example.created_at)
                ).order_by(
                    func.date(Example.created_at)
                ).all()
                
                return [
                    {
                        'date': result.date,
                        'examples': result.examples
                    }
                    for result in results
                ]
        except Exception as e:
            logger.error(f"Failed to count examples by date: {e}")
            return []
    
    def get_prompt_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get prompt creation trends"""
        try:
            with self.session_scope() as session:
                # Get prompts created in the last N days
                cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
                
                trends = session.query(
                    func.date(func.datetime(Prompt.created_at, 'unixepoch')).label('date'),
                    func.count(Prompt.id).label('count')
                ).filter(
                    Prompt.created_at >= cutoff_date
                ).group_by(
                    func.date(func.datetime(Prompt.created_at, 'unixepoch'))
                ).order_by(
                    func.date(func.datetime(Prompt.created_at, 'unixepoch'))
                ).all()
                
                return [
                    {'date': str(trend.date), 'count': trend.count}
                    for trend in trends
                ]
                
        except Exception as e:
            logger.error(f"Failed to get prompt trends: {e}")
            return []
    
    def get_example_growth(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get training example growth trends"""
        try:
            with self.session_scope() as session:
                # Get examples created in the last N days
                cutoff_date = datetime.now() - timedelta(days=days)
                
                growth = session.query(
                    func.date(Example.created_at).label('date'),
                    func.count(Example.id).label('count')
                ).filter(
                    Example.created_at >= cutoff_date
                ).group_by(
                    func.date(Example.created_at)
                ).order_by(
                    func.date(Example.created_at)
                ).all()
                
                return [
                    {'date': str(growth_item.date), 'count': growth_item.count}
                    for growth_item in growth
                ]
                
        except Exception as e:
            logger.error(f"Failed to get example growth: {e}")
            return []
    
    # --- Utility Methods ---
    
    def validate_training_data(self, training_data: Union[str, List[Dict[str, str]]]) -> bool:
        """Validate training data format"""
        try:
            validate_training_data_format(training_data)
            return True
        except Exception as e:
            logger.error(f"Training data validation failed: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            import shutil
            import os
            
            # Get database file path
            if self.engine.url.drivername == 'sqlite':
                db_path = self.engine.url.database
                if db_path == ':memory:':
                    raise ValueError("Cannot backup in-memory database")
                
                # Create backup
                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backed up to: {backup_path}")
                return True
            else:
                logger.warning("Backup not implemented for non-SQLite databases")
                return False
                
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """Clean up old data (prompts and examples older than specified days)"""
        try:
            cutoff_timestamp = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            with self.session_scope() as session:
                # Delete old prompts
                old_prompts = session.query(Prompt).filter(
                    Prompt.created_at < cutoff_timestamp
                ).all()
                
                deleted_count = len(old_prompts)
                
                for prompt in old_prompts:
                    session.delete(prompt)
                
                logger.info(f"Cleaned up {deleted_count} old prompts")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0 