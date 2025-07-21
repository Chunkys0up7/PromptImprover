#!/usr/bin/env python3
"""
Script to create test data for the Prompt Platform.
This script adds training examples to existing prompts to make them ready for DSPy improvement.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_platform.database import PromptDB
import uuid
import time

def create_test_training_examples():
    """Add test training examples to existing prompts"""
    db = PromptDB()
    
    # Get all prompts
    prompts = db.get_all_prompts()
    
    if not prompts:
        print("No prompts found in database. Please create some prompts first.")
        return
    
    print(f"Found {len(prompts)} prompts in database.")
    
    # Sample training examples for different types of prompts
    training_examples = {
        "greeting": [
            {"input": "Hello", "output": "Hi there! How can I help you today?", "critique": "Friendly and welcoming"},
            {"input": "Good morning", "output": "Good morning! I hope you're having a great day. What can I assist you with?", "critique": "Professional and warm"},
            {"input": "Hey", "output": "Hey! What's up? How can I be of service?", "critique": "Casual and approachable"}
        ],
        "email": [
            {"input": "Write a professional email", "output": "Subject: [Clear, descriptive subject line]\n\nDear [Recipient Name],\n\n[Opening paragraph with context and purpose]\n\n[Main content with details and action items]\n\n[Closing paragraph with next steps]\n\nBest regards,\n[Your Name]", "critique": "Clear structure and professional tone"},
            {"input": "Email to boss", "output": "Subject: [Specific topic or request]\n\nHi [Boss's Name],\n\nI hope this email finds you well. I wanted to discuss [specific topic] regarding [context].\n\n[Detailed explanation with supporting information]\n\nI would appreciate your guidance on [specific question or request].\n\nThank you for your time.\n\nBest regards,\n[Your Name]", "critique": "Respectful and specific"},
            {"input": "Follow-up email", "output": "Subject: Follow-up: [Previous topic]\n\nHi [Name],\n\nI hope you're doing well. I wanted to follow up on our conversation about [topic] from [date/time].\n\n[Brief reminder of key points discussed]\n\n[Specific next steps or questions]\n\nI look forward to hearing from you.\n\nBest regards,\n[Your Name]", "critique": "Professional and concise"}
        ],
        "story": [
            {"input": "Write a short story", "output": "Once upon a time, in a world not so different from our own, there lived a character who faced an extraordinary challenge. Through determination and courage, they discovered that the greatest adventures often begin with a single step into the unknown.", "critique": "Engaging opening and meaningful message"},
            {"input": "Sci-fi story", "output": "In the year 2157, aboard the starship Nebula, Captain Sarah Chen stared at the mysterious signal emanating from the uncharted sector. The crew's discovery would change humanity's understanding of the universe forever.", "critique": "Sets up intrigue and futuristic elements"},
            {"input": "Mystery story", "output": "Detective Marcus Reed examined the cryptic note left at the crime scene. The message contained a riddle that would lead him down a path of deception and revelation, where nothing was as it seemed.", "critique": "Creates suspense and mystery"}
        ],
        "code": [
            {"input": "Python function", "output": "def calculate_fibonacci(n):\n    \"\"\"Calculate the nth Fibonacci number\"\"\"\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)", "critique": "Clear, recursive implementation"},
            {"input": "JavaScript function", "output": "function reverseString(str) {\n    return str.split('').reverse().join('');\n}", "critique": "Concise and efficient"},
            {"input": "SQL query", "output": "SELECT name, email, created_at\nFROM users\nWHERE status = 'active'\nORDER BY created_at DESC;", "critique": "Clear and well-structured"}
        ]
    }
    
    examples_added = 0
    
    for prompt in prompts:
        prompt_id = prompt['id']
        task = prompt['task'].lower()
        
        # Determine which training examples to use based on task
        examples_to_add = []
        if any(word in task for word in ['greet', 'hello', 'hi', 'welcome']):
            examples_to_add = training_examples['greeting']
        elif any(word in task for word in ['email', 'mail', 'message']):
            examples_to_add = training_examples['email']
        elif any(word in task for word in ['story', 'narrative', 'tale']):
            examples_to_add = training_examples['story']
        elif any(word in task for word in ['code', 'function', 'program', 'script']):
            examples_to_add = training_examples['code']
        else:
            # Default to greeting examples for unknown tasks
            examples_to_add = training_examples['greeting']
        
        # Check if prompt already has examples
        existing_examples = db.get_examples(prompt_id)
        if len(existing_examples) >= 3:
            print(f"Prompt '{prompt['task']}' already has {len(existing_examples)} examples - skipping")
            continue
        
        # Add examples
        for example in examples_to_add:
            example_data = {
                'prompt_id': prompt_id,
                'input_text': example['input'],
                'output_text': example['output'],
                'critique': example['critique']
            }
            
            if db.add_example(example_data):
                examples_added += 1
                print(f"Added example to '{prompt['task']}': {example['input']} -> {example['output'][:50]}...")
            else:
                print(f"Failed to add example to '{prompt['task']}'")
    
    print(f"\n✅ Added {examples_added} training examples to prompts.")
    print("Prompts with 3+ examples are now ready for DSPy improvement!")

if __name__ == "__main__":
    create_test_training_examples() 