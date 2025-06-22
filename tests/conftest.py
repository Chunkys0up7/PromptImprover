import pytest
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from prompt_platform.database import Base, PromptDB
from contextlib import contextmanager

# Load environment variables
load_dotenv()

@pytest.fixture(scope="session")
def api_key():
    """Fixture to provide API key."""
    return os.getenv("API_TOKEN")

@pytest.fixture(scope="session")
def db_url():
    """Fixture to provide database URL."""
    return "sqlite:///test_prompt_storage.db"

@pytest.fixture(scope="session")
def test_db(db_url):
    """Fixture to initialize test database."""
    from prompt_platform.database import PromptDB
    db = PromptDB(db_url)
    # Clean up any existing data
    with db.Session() as session:
        session.query(PromptDB).delete()
        session.commit()
    return db

@pytest.fixture(scope="function")
def test_db():
    """
    Pytest fixture to provide a temporary, in-memory SQLite database
    for isolated testing of database operations.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db_instance = PromptDB()
    
    # Replace the production session with a test session
    db_instance.Session = TestingSessionLocal

    yield db_instance

    Base.metadata.drop_all(engine)
