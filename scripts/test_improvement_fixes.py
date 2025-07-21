#!/usr/bin/env python3
"""
Test script to verify prompt improvement fixes.
"""
import sys
import os
import asyncio
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_platform.database import PromptDB
from prompt_platform.prompt_generator import PromptGenerator
from prompt_platform.api_client import APIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_improvement_fixes():
    """Test the prompt improvement functionality"""
    print("🧪 Testing Prompt Improvement Fixes...")
    
    try:
        # Initialize components
        db = PromptDB()
        api_client = APIClient()
        prompt_generator = PromptGenerator(db)
        
        print("✅ Components initialized successfully")
        
        # Test 1: Check if get_prompt_performance_stats method exists
        print("\n📊 Test 1: Database method availability")
        if hasattr(db, 'get_prompt_performance_stats'):
            print("✅ get_prompt_performance_stats method exists")
        else:
            print("❌ get_prompt_performance_stats method missing")
            return False
        
        # Test 2: Test with string task description
        print("\n🔧 Test 2: String task description handling")
        try:
            # Create a test prompt first
            test_prompt_data = {
                'id': 'test-prompt-improvement',
                'lineage_id': 'test-lineage',
                'parent_id': None,
                'task': 'Test task for improvement',
                'prompt': 'You are a helpful assistant. Please help with: {input}',
                'version': 1,
                'training_data': '[]',
                'improvement_request': None,
                'generation_process': 'Test generation',
                'created_at': 1753055380.0,
                'model': 'test-model'
            }
            
            # Save the test prompt
            db.save_prompt(test_prompt_data)
            print("✅ Test prompt saved")
            
            # Test improvement with string task description
            task_description = "Make the prompt more concise"
            improved_prompt = await prompt_generator.improve_prompt(
                'test-prompt-improvement', 
                task_description, 
                api_client, 
                db
            )
            
            print("✅ String task description handled correctly")
            print(f"   Original: {test_prompt_data['prompt']}")
            print(f"   Improved: {improved_prompt['prompt']}")
            
        except Exception as e:
            print(f"❌ String task description test failed: {e}")
            return False
        
        # Test 3: Test with dictionary task description
        print("\n📝 Test 3: Dictionary task description handling")
        try:
            task_description_dict = {'task': 'Make the prompt more professional'}
            improved_prompt2 = await prompt_generator.improve_prompt(
                'test-prompt-improvement', 
                task_description_dict, 
                api_client, 
                db
            )
            
            print("✅ Dictionary task description handled correctly")
            print(f"   Improved: {improved_prompt2['prompt']}")
            
        except Exception as e:
            print(f"❌ Dictionary task description test failed: {e}")
            return False
        
        # Test 4: Test performance stats
        print("\n📈 Test 4: Performance stats retrieval")
        try:
            stats = db.get_prompt_performance_stats('test-prompt-improvement')
            print("✅ Performance stats retrieved successfully")
            print(f"   Stats: {stats}")
        except Exception as e:
            print(f"❌ Performance stats test failed: {e}")
            return False
        
        print("\n🎉 All tests passed! Prompt improvement functionality is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_improvement_fixes())
    sys.exit(0 if success else 1) 