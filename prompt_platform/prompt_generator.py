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
    
    - Initial generation: Uses AI-powered prompt engineering
    - Prompt improvement: Uses systematic prompt engineering principles
    - Optimization: Uses DSPy framework for few-shot learning
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
        system_message = """You are an expert prompt engineer specializing in systematic prompt design. Your task is to write a high-quality prompt template that will be used to instruct a powerful AI assistant.

Follow this systematic approach:

1. **Task Analysis**: Break down the user's request into core components
2. **Role Definition**: Determine the appropriate AI role and expertise needed
3. **Context Setting**: Establish the right context and constraints
4. **Instruction Clarity**: Create clear, actionable instructions
5. **Output Formatting**: Specify desired output structure if relevant
6. **Quality Assurance**: Ensure the prompt is specific, measurable, and achievable

Your response should include:
- The final prompt template with '{input}' placeholder
- A brief explanation of your approach and reasoning"""
        
        user_message = f"""The AI assistant needs to perform the following task: **{task}**

Please analyze this task and create an effective prompt template following systematic prompt engineering principles.

Consider:
- What specific role should the AI take?
- What context or background information is needed?
- What are the key instructions for the task?
- How should the output be structured?
- What constraints or guidelines should be applied?

Provide your response in this format:

**Prompt Template:**
[Your prompt template with {input} placeholder]

**Design Process:**
[Brief explanation of your approach and reasoning]"""
        
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
        fallback_prompt = f"Act as an expert on {task}. Respond to the following: {{input}}"
        
        response = await self._generate_with_fallback(api_client, messages, fallback_prompt)
        
        # Parse the response to extract prompt and process explanation
        prompt_text, process_explanation = self._parse_generation_response(response, task)
        
        # Store the process explanation in the prompt data
        prompt_data = self._create_prompt_data(task=task, prompt=prompt_text)
        prompt_data['generation_process'] = process_explanation
        
        return prompt_data

    def _parse_generation_response(self, response: str, task: str) -> tuple[str, str]:
        """Parses the AI response to extract the prompt template and process explanation."""
        # Try to extract the prompt template and process explanation
        if "**Prompt Template:**" in response and "**Design Process:**" in response:
            # Split by the markers
            parts = response.split("**Prompt Template:**")
            if len(parts) > 1:
                prompt_part = parts[1].split("**Design Process:**")[0].strip()
                process_part = parts[1].split("**Design Process:**")[1].strip() if "**Design Process:**" in parts[1] else ""
                
                # Clean up the prompt template
                prompt_text = prompt_part.strip()
                if prompt_text.startswith("["):
                    prompt_text = prompt_text[1:]
                if prompt_text.endswith("]"):
                    prompt_text = prompt_text[:-1]
                
                return prompt_text, process_part
        elif "**Design Process:**" in response:
            # Try to extract just the process explanation
            process_part = response.split("**Design Process:**")[1].strip()
            # Use a simple fallback prompt
            fallback_prompt = f"Act as an expert on {task}. Respond to the following: {{input}}"
            return fallback_prompt, process_part
        else:
            # If no structured response, treat the whole thing as the prompt
            return response.strip(), "Generated using systematic prompt engineering principles with task analysis and role definition."

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