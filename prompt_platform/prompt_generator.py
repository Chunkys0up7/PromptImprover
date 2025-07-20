import os
import logging
import json
import asyncio
import dspy
import uuid
from functools import lru_cache
from typing import Any, Callable

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

    async def improve_prompt_with_dspy(self, prompt_id: int, task_description: dict, api_client: 'APIClient', db: 'PromptDB') -> dict:
        """
        Improves a prompt using DSPy's systematic optimization approach.
        
        This follows the DSPy methodology:
        1. Define the task and evaluate current performance
        2. Collect training data and define metrics
        3. Leverage DSPy optimizers
        4. Iterate and refine
        """
        original_prompt_data = db.get_prompt(prompt_id)
        if not original_prompt_data:
            raise ValueError(f"Original prompt with ID {prompt_id} not found.")

        logger.info(f"Starting DSPy improvement process for prompt {prompt_id}")
        
        # Step 1: Define the task and evaluate current performance
        task_signature = self._define_task_signature(original_prompt_data, task_description)
        
        # Step 2: Collect training data and define metrics
        training_data = self._prepare_training_data(original_prompt_data, task_description)
        evaluation_metric = self._define_evaluation_metric(task_description)
        
        # Step 3: Choose appropriate DSPy optimizer based on data size
        optimizer = self._select_optimizer(len(training_data))
        
        # Step 4: Run DSPy optimization
        improved_prompt = await self._run_dspy_optimization(
            task_signature, training_data, evaluation_metric, optimizer, original_prompt_data['prompt']
        )
        
        # Step 5: Create improved prompt data
        return self._create_prompt_data(
            task=original_prompt_data['task'],
            prompt=improved_prompt,
            parent_id=original_prompt_data['id'],
            lineage_id=original_prompt_data['lineage_id'],
            version=original_prompt_data.get('version', 0) + 1,
            training_data=training_data,
            improvement_request=f"DSPy optimization: {task_description.get('critique', 'Systematic improvement')}"
        )

    def _define_task_signature(self, prompt_data: dict, task_description: dict) -> dspy.Signature:
        """Define the DSPy signature for the task."""
        # Create a dynamic signature based on the task
        class TaskSignature(dspy.Signature):
            """Generate a response based on the user's input using the optimized prompt."""
            input = dspy.InputField(desc="User input for the task")
            output = dspy.OutputField(desc="Expected output based on the prompt")
        
        return TaskSignature

    def _prepare_training_data(self, prompt_data: dict, task_description: dict) -> list:
        """Prepare training data for DSPy optimization."""
        training_data = []
        
        # Add existing training data if available
        existing_data = prompt_data.get('training_data', [])
        if isinstance(existing_data, str):
            try:
                existing_data = json.loads(existing_data)
            except:
                existing_data = []
        
        training_data.extend(existing_data)
        
        # Add the current feedback as training data
        if isinstance(task_description, dict):
            feedback_example = {
                "input": task_description.get('user_input', ''),
                "output": task_description.get('desired_output', '')
            }
            training_data.append(feedback_example)
        
        # Ensure we have at least some training data
        if not training_data:
            # Create a basic example from the task
            training_data.append({
                "input": "example input",
                "output": "expected output based on the prompt"
            })
        
        return training_data

    def _define_evaluation_metric(self, task_description: dict) -> callable:
        """Define the evaluation metric for DSPy optimization."""
        if isinstance(task_description, dict) and task_description.get('critique'):
            # Use a custom metric that considers the specific feedback
            def custom_metric(gold, pred, trace=None):
                # Basic exact match with some flexibility
                if isinstance(gold, str) and isinstance(pred, str):
                    return gold.lower().strip() == pred.lower().strip()
                return False
            return custom_metric
        else:
            # Default to exact match
            return dspy.evaluate.answer_exact_match

    def _select_optimizer(self, data_size: int) -> Any:
        """Select the appropriate DSPy optimizer based on data size."""
        if data_size < 10:
            # For limited examples, use BootstrapFewShot
            logger.info(f"Using BootstrapFewShot for {data_size} examples")
            return dspy.BootstrapFewShot(
                metric=dspy.evaluate.answer_exact_match,
                max_bootstrapped_demos=min(data_size, 5),
                max_labeled_demos=min(data_size, 5)
            )
        elif data_size < 50:
            # For moderate data, use BootstrapFewShotWithRandomSearch
            logger.info(f"Using BootstrapFewShotWithRandomSearch for {data_size} examples")
            return dspy.BootstrapFewShotWithRandomSearch(
                metric=dspy.evaluate.answer_exact_match,
                max_bootstrapped_demos=min(data_size // 2, 10),
                max_labeled_demos=min(data_size // 2, 10),
                num_candidate_programs=3,
                num_threads=1
            )
        else:
            # For larger datasets, use MIPROv2
            logger.info(f"Using MIPROv2 for {data_size} examples")
            return dspy.MIPROv2(
                metric=dspy.evaluate.answer_exact_match,
                max_bootstrapped_demos=min(data_size // 4, 20),
                max_labeled_demos=min(data_size // 4, 20),
                num_candidate_programs=5,
                num_threads=2
            )

    async def _run_dspy_optimization(self, signature: dspy.Signature, training_data: list, 
                                   evaluation_metric: Callable, optimizer: Any, original_prompt: str) -> str:
        """Run DSPy optimization and extract the optimized prompt."""
        try:
            class OptimizedModule(dspy.Module):
                def __init__(self):
                    super().__init__()
                    self.generate_answer = dspy.ChainOfThought(signature)
                
                def forward(self, input):
                    return self.generate_answer(input=input)
            
            # Convert training data to DSPy examples
            trainset = []
            for item in training_data:
                if isinstance(item, dict) and 'input' in item and 'output' in item:
                    example = dspy.Example(input=item['input'], output=item['output'])
                    # Set the inputs properly for DSPy
                    example = example.with_inputs(input=item['input'])
                    trainset.append(example)
            
            if not trainset:
                raise ValueError("No valid training examples found")
            
            # Run optimization
            logger.info(f"Running DSPy optimization with {len(trainset)} examples")
            optimized_module = await asyncio.to_thread(
                optimizer.compile, 
                OptimizedModule(), 
                trainset=trainset
            )
            
            # Extract the optimized prompt - handle different DSPy module types
            try:
                # Try multiple methods to extract the optimized prompt
                optimized_prompt = None
                
                # Method 1: Try to get from signature instructions
                if hasattr(optimized_module.generate_answer, 'signature'):
                    signature = optimized_module.generate_answer.signature
                    if hasattr(signature, 'instructions'):
                        optimized_prompt = signature.instructions
                
                # Method 2: Try to get from the module's docstring
                if not optimized_prompt and hasattr(optimized_module.generate_answer, '__doc__'):
                    doc = optimized_module.generate_answer.__doc__
                    if doc and doc.strip() and "Generate a response" not in doc:
                        optimized_prompt = doc
                
                # Method 3: Try to get from the signature's docstring
                if not optimized_prompt and hasattr(optimized_module.generate_answer, 'signature'):
                    signature = optimized_module.generate_answer.signature
                    if hasattr(signature, '__doc__'):
                        doc = signature.__doc__
                        if doc and doc.strip() and "Generate a response" not in doc:
                            optimized_prompt = doc
                
                # Method 4: Try to get from the module's raw_instructions (if available)
                if not optimized_prompt and hasattr(optimized_module.generate_answer, 'raw_instructions'):
                    optimized_prompt = optimized_module.generate_answer.raw_instructions
                
                # If we still don't have a prompt, use the original
                if not optimized_prompt or optimized_prompt.strip() == "":
                    logger.warning("Could not extract optimized prompt from DSPy module, using original")
                    optimized_prompt = original_prompt
                
                # Clean up the prompt if it's just the default docstring
                if optimized_prompt and "Generate a response based on the user's input using the optimized prompt." in optimized_prompt:
                    logger.warning("Extracted prompt is default docstring, using original")
                    optimized_prompt = original_prompt
                    
            except Exception as e:
                logger.warning(f"Could not extract optimized prompt: {e}")
                # Use the original prompt as fallback
                optimized_prompt = original_prompt
            
            # Ensure the prompt has the required placeholder
            if '{input}' not in optimized_prompt:
                optimized_prompt += "\n\nInput: {input}"
            
            logger.info("DSPy optimization completed successfully")
            return optimized_prompt
            
        except Exception as e:
            logger.error(f"DSPy optimization failed: {e}", exc_info=True)
            # Fallback to basic improvement
            raise ValueError(f"DSPy optimization failed: {e}")

    async def improve_prompt(self, prompt_id: int, task_description: dict, api_client: 'APIClient', db: 'PromptDB') -> dict:
        """
        Improves an existing prompt using DSPy when possible, falls back to basic improvement.
        """
        try:
            # Try DSPy improvement first
            return await self.improve_prompt_with_dspy(prompt_id, task_description, api_client, db)
        except Exception as e:
            logger.warning(f"DSPy improvement failed, falling back to basic improvement: {e}")
            # Fallback to the original improvement method
            return await self._improve_prompt_basic(prompt_id, task_description, api_client, db)

    async def _improve_prompt_basic(self, prompt_id: int, task_description: dict, api_client: 'APIClient', db: 'PromptDB') -> dict:
        """Original basic improvement method as fallback."""
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