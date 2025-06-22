import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from prompt_platform.database import PromptDB, Base, Prompt as PromptModel
from prompt_platform.schemas import Prompt as PromptSchema

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def prompt_db(db_session):
    """Fixture to provide a PromptDB instance with a clean database."""
    return PromptDB(TestingSessionLocal)

def test_save_and_get_prompt(prompt_db):
    """
    Tests that a prompt can be saved to and retrieved from the database.
    """
    lineage_id = str(uuid.uuid4())
    prompt_data = PromptSchema(
        lineage_id=lineage_id,
        task="Test task",
        prompt="This is a test prompt with {{input}}.",
        version=1,
    )
    
    # Save the prompt
    prompt_db.save_prompt(prompt_data)
    
    # Retrieve the prompt
    all_prompts = prompt_db.get_all_prompts()
    assert len(all_prompts) == 1
    retrieved_prompt_model = all_prompts[0]

    assert retrieved_prompt_model is not None
    assert retrieved_prompt_model['lineage_id'] == lineage_id
    assert retrieved_prompt_model['task'] == "Test task"
    
    # Use the public get method
    retrieved_prompt_dict = prompt_db.get_prompt(retrieved_prompt_model['id'])
    assert retrieved_prompt_dict['prompt'] == "This is a test prompt with {{input}}."

def test_get_all_prompts(prompt_db):
    """
    Tests retrieving all prompts from the database.
    """
    # Create and save two different prompts
    prompt1 = PromptSchema(lineage_id=str(uuid.uuid4()), task="Task 1", prompt="Prompt 1")
    prompt2 = PromptSchema(lineage_id=str(uuid.uuid4()), task="Task 2", prompt="Prompt 2")
    
    prompt_db.save_prompt(prompt1)
    prompt_db.save_prompt(prompt2)
    
    all_prompts = prompt_db.get_all_prompts()
    assert len(all_prompts) == 2
    tasks = {p['task'] for p in all_prompts}
    assert tasks == {"Task 1", "Task 2"}

def test_delete_lineage(prompt_db):
    """
    Tests that all versions of a prompt with the same lineage_id are deleted.
    """
    lineage_id = str(uuid.uuid4())
    p1 = PromptSchema(lineage_id=lineage_id, version=1, task="A", prompt="P1")
    p2 = PromptSchema(lineage_id=lineage_id, version=2, task="A->B", prompt="P2")
    p3 = PromptSchema(lineage_id=str(uuid.uuid4()), task="C", prompt="P3") # Different lineage

    prompt_db.save_prompt(p1)
    prompt_db.save_prompt(p2)
    prompt_db.save_prompt(p3)

    assert len(prompt_db.get_all_prompts()) == 3
    
    prompt_db.delete_lineage(lineage_id)
    
    remaining_prompts = prompt_db.get_all_prompts()
    assert len(remaining_prompts) == 1
    assert remaining_prompts[0]['task'] == "C" 