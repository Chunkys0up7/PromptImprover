#!/usr/bin/env python3
"""
Comprehensive test script to verify dashboard and prompt improvement fixes.
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

async def test_dashboard_fixes():
    """Test all dashboard and prompt improvement functionality"""
    print("🧪 Testing Dashboard and Prompt Improvement Fixes...")
    
    try:
        # Initialize components
        db = PromptDB()
        api_client = APIClient()
        prompt_generator = PromptGenerator(db)
        
        print("✅ Components initialized successfully")
        
        # Test 1: Check all required database methods exist
        print("\n📊 Test 1: Database method availability")
        required_methods = [
            'get_performance_stats',
            'get_prompt_performance_stats', 
            'get_top_prompts_by_versions',
            'count_prompts_by_date',
            'count_examples_by_date'
        ]
        
        for method in required_methods:
            if hasattr(db, method):
                print(f"✅ {method} method exists")
            else:
                print(f"❌ {method} method missing")
                return False
        
        # Test 2: Test performance stats retrieval
        print("\n📈 Test 2: Performance stats retrieval")
        try:
            stats = db.get_performance_stats()
            print("✅ Overall performance stats retrieved")
            print(f"   Stats: {stats}")
        except Exception as e:
            print(f"❌ Performance stats test failed: {e}")
            return False
        
        # Test 3: Test prompt-specific performance stats
        print("\n🎯 Test 3: Prompt-specific performance stats")
        try:
            # Create a test prompt first
            test_prompt_data = {
                'id': 'test-prompt-dashboard',
                'lineage_id': 'test-lineage-dashboard',
                'parent_id': None,
                'task': 'Test task for dashboard',
                'prompt': 'You are a helpful assistant. Please help with: {input}',
                'version': 1,
                'training_data': '[]',
                'improvement_request': None,
                'generation_process': 'Test generation',
                'created_at': 1753055380.0,
                'model': 'test-model'
            }
            
            db.save_prompt(test_prompt_data)
            print("✅ Test prompt saved")
            
            stats = db.get_prompt_performance_stats('test-prompt-dashboard')
            print("✅ Prompt-specific stats retrieved")
            print(f"   Stats: {stats}")
        except Exception as e:
            print(f"❌ Prompt-specific stats test failed: {e}")
            return False
        
        # Test 4: Test trend data methods
        print("\n📊 Test 4: Trend data methods")
        try:
            prompt_trends = db.count_prompts_by_date(days=7)
            example_trends = db.count_examples_by_date(days=7)
            top_prompts = db.get_top_prompts_by_versions(limit=3)
            
            print("✅ Trend data methods work correctly")
            print(f"   Prompt trends: {len(prompt_trends)} entries")
            print(f"   Example trends: {len(example_trends)} entries")
            print(f"   Top prompts: {len(top_prompts)} entries")
        except Exception as e:
            print(f"❌ Trend data test failed: {e}")
            return False
        
        # Test 5: Test string task description in improvement
        print("\n🔧 Test 5: String task description handling")
        try:
            task_description = "Make the prompt more concise and professional"
            improved_prompt = await prompt_generator.improve_prompt(
                'test-prompt-dashboard', 
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
        
        # Test 6: Test dictionary task description in improvement
        print("\n📝 Test 6: Dictionary task description handling")
        try:
            task_description_dict = {
                'task': 'Make the prompt more engaging',
                'user_input': 'Sample input',
                'bad_output': 'Poor response',
                'desired_output': 'Better response',
                'critique': 'Needs to be more engaging'
            }
            
            improved_prompt2 = await prompt_generator.improve_prompt(
                'test-prompt-dashboard', 
                task_description_dict, 
                api_client, 
                db
            )
            
            print("✅ Dictionary task description handled correctly")
            print(f"   Improved: {improved_prompt2['prompt']}")
            
        except Exception as e:
            print(f"❌ Dictionary task description test failed: {e}")
            return False
        
        print("\n🎉 All tests passed! Dashboard and prompt improvement functionality is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_dashboard_fixes())
    sys.exit(0 if success else 1) 