import os
import logging
import json
import asyncio
import dspy
import uuid
from functools import lru_cache

from .config import DspyConfig, get_dspy_lm
from .schemas import Prompt as PromptSchema
from .database import PromptDB # Import the class, not the instance

logger = logging.getLogger(__name__)

class BasicModule(dspy.Module):
    """A basic DSPy module for few-shot optimization."""
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.ChainOfThought("input -> output")

    def forward(self, input):
        return self.generate_answer(input=input)

class PromptGenerator:
    """
    Handles prompt generation, improvement, and optimization logic using DSPy.
    """
    def __init__(self):
        try:
            self.dspy_lm = get_dspy_lm()
            self.is_configured = True
            logger.info("PromptGenerator configured successfully with DSPy.")
        except ValueError as e:
            self.dspy_lm = None
            self.is_configured = False
            logger.warning(f"DSPy configuration failed: {e}. Optimization will be disabled.")

    def _create_prompt_data(self, task: str, prompt: str, parent_id: str = None, lineage_id: str = None, version: int = 1, training_data: list = []) -> dict:
        """Creates a structured dictionary for a new prompt, validating with Pydantic."""
        if not lineage_id:
            lineage_id = str(uuid.uuid4())
            
        validated_prompt = PromptSchema(
            task=task,
            prompt=prompt,
            parent_id=parent_id,
            lineage_id=lineage_id,
            version=version,
            training_data=training_data
        )
        return validated_prompt.model_dump()

    async def _generate_with_fallback(self, api_client, messages, fallback_prompt):
        """Helper to call the API and return a fallback on failure."""
        try:
            return await api_client.get_chat_completion(messages)
        except Exception:
            logger.warning("API call failed, returning fallback prompt.")
            return fallback_prompt

    async def generate_initial_prompt(self, task: str, api_client: 'APIClient') -> dict:
        """Creates an initial prompt by calling the API with a meta-prompt."""
        system_message = "You are an expert prompt engineer. Create a detailed, effective prompt template for the given task. The prompt must include the placeholder '{{input}}' for user input."
        user_message = f"Task: Create a prompt for an AI assistant that can {task}."
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
        fallback_prompt = f"Act as an expert on {task}. Respond to the following: {{input}}"
        
        prompt_text = await self._generate_with_fallback(api_client, messages, fallback_prompt)
        return self._create_prompt_data(task=task, prompt=prompt_text)

    async def improve_prompt(self, prompt_id: str, task_description: str, api_client: 'APIClient', db: 'PromptDB') -> dict:
        """Improves an existing prompt and creates a new version in the same lineage."""
        logger.info(f"Improving prompt {prompt_id} with task: '{task_description}'")

        original_prompt_data = db.get_prompt(prompt_id)
        if not original_prompt_data:
            raise ValueError(f"Original prompt with ID {prompt_id} not found.")

        system_message = "You are a world-class expert in prompt engineering. Refine the following prompt based on the user's instruction. Output ONLY the new prompt text."
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Refine this prompt:\n---\n{original_prompt_data['prompt']}\n---\n\nInstruction: '{task_description}'. Output only the new prompt."}
        ]
        
        improved_text = await api_client.get_chat_completion(messages)
        
        return self._create_prompt_data(
            task=task_description,
            prompt=improved_text,
            parent_id=original_prompt_data['id'],
            lineage_id=original_prompt_data['lineage_id'],
            version=original_prompt_data.get('version', 0) + 1,
            training_data=original_prompt_data.get('training_data', [])
        )

    async def optimize_prompt(self, existing_prompt_data: dict) -> dict:
        """Optimizes a prompt using DSPy and its training data."""
        logger.info(f"Starting DSPy optimization for prompt ID: {existing_prompt_data.get('id')}")
        if not self.is_configured:
            raise ValueError("DSPy is not configured.")

        training_data_str = existing_prompt_data.get("training_data", "[]")
        training_data = json.loads(training_data_str)

        if not training_data:
            raise ValueError("Optimization requires at least one training example.")

        trainset = [dspy.Example(**item).with_inputs("input") for item in training_data]

        config = dict(
            max_bootstrapped_demos=DspyConfig.MAX_DEMOS,
            max_labeled_demos=DspyConfig.MAX_DEMOS
        )

        teleprompter = dspy.BootstrapFewShot(metric=dspy.evaluate.answer_exact_match, **config)
        optimized_module = await asyncio.to_thread(teleprompter.compile, BasicModule(), trainset=trainset)

        new_prompt_text = optimized_module.generate_answer.raw_instructions
        
        return self._create_prompt_data(
            task=f"Optimized: {existing_prompt_data['task']}",
            prompt=new_prompt_text,
            parent_id=existing_prompt_data['id'],
            lineage_id=existing_prompt_data['lineage_id'],
            version=existing_prompt_data.get('version', 0) + 1,
            training_data=training_data
        )

# Singleton instance
prompt_generator = PromptGenerator() 