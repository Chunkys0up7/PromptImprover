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
    Handles prompt generation, improvement, and optimization logic.
    
    - Initial generation: Uses Perplexity AI (Sonar Pro)
    - Prompt improvement: Uses Perplexity AI (Sonar Pro) 
    - Optimization: Uses DSPy with Perplexity AI backend
    """
    def __init__(self, db: 'PromptDB'):
        try:
            self.lm = get_dspy_lm()
            dspy.configure(lm=self.lm)
            logger.info("PromptGenerator configured successfully with DSPy.")
        except Exception as e:
            logger.error(f"Failed to configure DSPy: {e}", exc_info=True)
            self.lm = None

    def _create_prompt_data(self, task: str, prompt: str, parent_id: str = None, lineage_id: str = None, version: int = 1, training_data: list = [], improvement_request: str = None) -> dict:
        """Creates a structured dictionary for a new prompt, validating with Pydantic."""
        if not lineage_id:
            lineage_id = str(uuid.uuid4())
            
        validated_prompt = PromptSchema(
            task=task,
            prompt=prompt,
            parent_id=parent_id,
            lineage_id=lineage_id,
            version=version,
            training_data=training_data,
            improvement_request=improvement_request
        )
        return validated_prompt.model_dump()

    async def _generate_with_fallback(self, api_client, messages, fallback_prompt):
        """Helper to call the API and return a fallback on failure."""
        try:
            return await api_client.get_chat_completion(messages)
        except Exception:
            logger.warning("API call failed, returning fallback prompt.")
            return fallback_prompt

    @lru_cache(maxsize=128)
    async def generate_initial_prompt(self, task: str, api_client: 'APIClient') -> dict:
        """Creates an initial prompt by calling the API with a meta-prompt."""
        system_message = "You are an expert prompt engineer. Your task is to write a high-quality prompt template that will be used to instruct a powerful AI assistant."
        user_message = f"The AI assistant needs to perform the following task: **{task}**. Your job is to write the prompt template that will be given to this assistant. The template should contain a placeholder, '{{input}}', which will be replaced with the user's specific request at runtime. The template should directly instruct the AI to perform the task."
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
        fallback_prompt = f"Act as an expert on {task}. Respond to the following: {{input}}"
        
        prompt_text = await self._generate_with_fallback(api_client, messages, fallback_prompt)
        return self._create_prompt_data(task=task, prompt=prompt_text)

    async def improve_prompt(self, prompt_id: int, task_description: dict, api_client: 'APIClient', db: 'PromptDB') -> dict:
        """Improves an existing prompt based on a textual description."""
        original_prompt_data = db.get_prompt(prompt_id)

        if not original_prompt_data:
            raise ValueError(f"Original prompt with ID {prompt_id} not found.")

        # Ensure the prompt uses the correct placeholder before improving it.
        # We only replace the first instance to avoid corrupting examples.
        prompt_text_to_improve = original_prompt_data['prompt'].replace('{{input}}', '{input}', 1)

        system_message = "You are an expert prompt engineer. Your task is to improve a prompt based on user feedback. You will be given a critique of a prompt's performance and the prompt itself. Your job is to rewrite the prompt to be more effective. The final revised prompt must include the placeholder '{input}' for the user's runtime input. IMPORTANT: Do not use the placeholder in examples; describe the input instead. Provide ONLY the improved prompt text as your response, without any extra commentary or formatting."
        
        # Handle both string and dict task_description for backward compatibility
        if isinstance(task_description, str):
            user_message = f"""The current prompt is:
---
{prompt_text_to_improve}
---

It received the following critique:
{task_description}

Please provide the improved prompt.
"""
        else:
            user_message = f"""The current prompt is:
---
{prompt_text_to_improve}
---

It received the following critique:
- User Input: '{task_description.get('user_input', 'Not provided')}'
- Actual (Bad) Output: '{task_description.get('bad_output', 'Not provided')}'
- Desired Output: '{task_description.get('desired_output', 'Not provided')}'
- Critique: '{task_description.get('critique', 'Not provided')}'

Please provide the improved prompt.
"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        logger.info(f"Improving prompt {original_prompt_data['id']} with task: '{task_description}'")
        
        improved_text = await api_client.get_chat_completion(messages)
        
        # Create improvement request text for storage
        if isinstance(task_description, str):
            improvement_request = task_description
        else:
            improvement_request = f"User Input: '{task_description.get('user_input', 'Not provided')}'; Bad Output: '{task_description.get('bad_output', 'Not provided')}'; Desired Output: '{task_description.get('desired_output', 'Not provided')}'; Critique: '{task_description.get('critique', 'Not provided')}'"
        
        return self._create_prompt_data(
            task=original_prompt_data['task'],
            prompt=improved_text,
            parent_id=original_prompt_data['id'],
            lineage_id=original_prompt_data['lineage_id'],
            version=original_prompt_data.get('version', 0) + 1,
            training_data=original_prompt_data.get('training_data', []),
            improvement_request=improvement_request
        )

    async def optimize_prompt(self, existing_prompt_data: dict) -> dict:
        """Optimizes a prompt using DSPy and its training data."""
        logger.info(f"Starting DSPy optimization for prompt ID: {existing_prompt_data.get('id')}")
        if not self.lm:
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
            task=existing_prompt_data['task'],
            prompt=new_prompt_text,
            parent_id=existing_prompt_data['id'],
            lineage_id=existing_prompt_data['lineage_id'],
            version=existing_prompt_data.get('version', 0) + 1,
            training_data=training_data,
            improvement_request="DSPy optimization based on training data"
        ) 