import pytest
from prompt_platform.ui_actions import handle_save_example
from prompt_platform.database import PromptDB
import streamlit as st
import uuid
import time

@pytest.fixture
def db():
    db = PromptDB()
    yield db

@pytest.fixture(autouse=True)
def setup_session_state(db):
    st.session_state.db = db
    yield
    st.session_state.clear()

def test_handle_save_example_adds_example(db):
    prompt_id = str(uuid.uuid4())
    prompt_data = {
        'id': prompt_id,
        'lineage_id': 'test-lineage',
        'parent_id': None,
        'task': 'Test prompt',
        'prompt': 'Say hello to {input}',
        'version': 1,
        'training_data': [],
        'improvement_request': None,
        'generation_process': None,
        'created_at': time.time(),
        'model': None
    }
    db.save_prompt(prompt_data)
    input_text = 'World'
    output_text = 'Hello, World!'
    critique = 'Should be more formal.'
    handle_save_example(prompt_id, input_text, output_text, critique)
    examples = db.get_examples(prompt_id)
    assert len(examples) == 1
    assert examples[0]['input_text'] == input_text
    assert examples[0]['output_text'] == output_text
    assert examples[0]['critique'] == critique 

def test_handle_save_example_triggers_improvement(monkeypatch, db):
    prompt_id = str(uuid.uuid4())
    prompt_data = {
        'id': prompt_id,
        'lineage_id': 'test-lineage',
        'parent_id': None,
        'task': 'Test prompt',
        'prompt': 'Say hello to {input}',
        'version': 1,
        'training_data': [],
        'improvement_request': None,
        'generation_process': None,
        'created_at': time.time(),
        'model': None
    }
    db.save_prompt(prompt_data)
    input_texts = ['World', 'Alice', 'Bob']
    output_texts = ['Hello, World!', 'Hello, Alice!', 'Hello, Bob!']
    critiques = ['Should be more formal.', 'Add a greeting.', 'Use exclamation mark.']
    toasts = []
    # Patch st.toast to capture messages
    monkeypatch.setattr(st, 'toast', lambda msg, icon=None: toasts.append(msg))
    # Patch run_async to no-op
    monkeypatch.setattr('prompt_platform.ui_actions.run_async', lambda coro: None)
    for i in range(3):
        handle_save_example(prompt_id, input_texts[i], output_texts[i], critiques[i])
    examples = db.get_examples(prompt_id)
    assert len(examples) == 3
    # The last toast should indicate DSPy improvement trigger
    assert any('Triggering DSPy optimization' in t for t in toasts) 