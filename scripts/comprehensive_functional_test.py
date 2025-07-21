#!/usr/bin/env python3
"""
Comprehensive functional test to identify all issues in the Prompt Platform.
"""
import sys
import os
import asyncio
import logging
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_platform.database import PromptDB
from prompt_platform.prompt_generator import PromptGenerator
from prompt_platform.api_client import APIClient
from prompt_platform.dashboard import fetch_top_prompts, fetch_performance_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FunctionalTestSuite:
    """Comprehensive functional test suite"""
    
    def __init__(self):
        self.results = []
        self.errors = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        if success:
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {test_name}: FAILED")
            if details:
                print(f"   {details}")
            self.errors.append(result)
    
    async def run_all_tests(self):
        """Run all functional tests"""
        print("🧪 COMPREHENSIVE FUNCTIONAL TEST SUITE")
        print("=" * 50)
        
        # Initialize components
        try:
            self.db = PromptDB()
            self.api_client = APIClient()
            self.prompt_generator = PromptGenerator(self.db)
            self.log_result("Component Initialization", True, "All components initialized successfully")
        except Exception as e:
            self.log_result("Component Initialization", False, f"Failed: {e}")
            return False
        
        # Test 1: Database Operations
        await self.test_database_operations()
        
        # Test 2: Prompt Generation
        await self.test_prompt_generation()
        
        # Test 3: Prompt Improvement
        await self.test_prompt_improvement()
        
        # Test 4: Dashboard Functions
        await self.test_dashboard_functions()
        
        # Test 5: Data Validation
        await self.test_data_validation()
        
        # Test 6: Error Handling
        await self.test_error_handling()
        
        # Test 7: Integration Tests
        await self.test_integration()
        
        # Summary
        self.print_summary()
        
        return len(self.errors) == 0
    
    async def test_database_operations(self):
        """Test all database operations"""
        print("\n📊 Testing Database Operations...")
        
        # Test 1.1: Save prompt
        try:
            test_prompt = {
                'id': 'test-functional-001',
                'lineage_id': 'test-lineage-001',
                'parent_id': None,
                'task': 'Test functional prompt',
                'prompt': 'You are a helpful assistant: {input}',
                'version': 1,
                'training_data': '[]',
                'improvement_request': None,
                'generation_process': 'Functional test',
                'created_at': datetime.now().timestamp(),
                'model': 'test-model'
            }
            
            saved_prompt = self.db.save_prompt(test_prompt)
            if saved_prompt and isinstance(saved_prompt, dict):
                self.log_result("Database Save Prompt", True, f"Saved prompt: {saved_prompt['id']}")
            else:
                self.log_result("Database Save Prompt", False, f"Expected dict, got: {type(saved_prompt)}")
        except Exception as e:
            self.log_result("Database Save Prompt", False, f"Exception: {e}")
        
        # Test 1.2: Get prompt
        try:
            retrieved_prompt = self.db.get_prompt('test-functional-001')
            if retrieved_prompt and isinstance(retrieved_prompt, dict):
                self.log_result("Database Get Prompt", True, f"Retrieved prompt: {retrieved_prompt['id']}")
            else:
                self.log_result("Database Get Prompt", False, f"Expected dict, got: {type(retrieved_prompt)}")
        except Exception as e:
            self.log_result("Database Get Prompt", False, f"Exception: {e}")
        
        # Test 1.3: Get performance stats
        try:
            stats = self.db.get_performance_stats()
            if isinstance(stats, dict):
                self.log_result("Database Performance Stats", True, f"Stats: {stats}")
            else:
                self.log_result("Database Performance Stats", False, f"Expected dict, got: {type(stats)}")
        except Exception as e:
            self.log_result("Database Performance Stats", False, f"Exception: {e}")
        
        # Test 1.4: Get top prompts
        try:
            top_prompts = self.db.get_top_prompts(limit=3)
            if isinstance(top_prompts, list):
                # Check if all required fields are present
                if top_prompts:
                    required_fields = ['lineage_id', 'task', 'created_at', 'version_count', 'latest_version']
                    missing_fields = [field for field in required_fields if field not in top_prompts[0]]
                    if not missing_fields:
                        self.log_result("Database Top Prompts", True, f"Retrieved {len(top_prompts)} prompts with all fields")
                    else:
                        self.log_result("Database Top Prompts", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_result("Database Top Prompts", True, "No prompts found (empty list)")
            else:
                self.log_result("Database Top Prompts", False, f"Expected list, got: {type(top_prompts)}")
        except Exception as e:
            self.log_result("Database Top Prompts", False, f"Exception: {e}")
    
    async def test_prompt_generation(self):
        """Test prompt generation functionality"""
        print("\n🚀 Testing Prompt Generation...")
        
        try:
            generated_prompt = await self.prompt_generator.generate_initial_prompt(
                "Create a helpful response", 
                self.api_client
            )
            
            if isinstance(generated_prompt, dict) and 'prompt' in generated_prompt:
                self.log_result("Prompt Generation", True, f"Generated prompt: {generated_prompt['prompt'][:50]}...")
            else:
                self.log_result("Prompt Generation", False, f"Expected dict with 'prompt' key, got: {type(generated_prompt)}")
        except Exception as e:
            self.log_result("Prompt Generation", False, f"Exception: {e}")
    
    async def test_prompt_improvement(self):
        """Test prompt improvement functionality"""
        print("\n✨ Testing Prompt Improvement...")
        
        # Create a test prompt for improvement
        test_prompt = {
            'id': 'test-improvement-001',
            'lineage_id': 'test-lineage-002',
            'parent_id': None,
            'task': 'Test improvement prompt',
            'prompt': 'You are a helpful assistant: {input}',
            'version': 1,
            'training_data': '[]',
            'improvement_request': None,
            'generation_process': 'Functional test',
            'created_at': datetime.now().timestamp(),
            'model': 'test-model'
        }
        
        try:
            # Save the test prompt
            saved_prompt = self.db.save_prompt(test_prompt)
            if not saved_prompt:
                self.log_result("Prompt Improvement Setup", False, "Failed to save test prompt")
                return
            
            # Test string task description
            improved_prompt = await self.prompt_generator.improve_prompt(
                'test-improvement-001',
                "Make it more concise",
                self.api_client,
                self.db
            )
            
            if isinstance(improved_prompt, dict) and 'prompt' in improved_prompt:
                self.log_result("Prompt Improvement (String)", True, f"Improved prompt: {improved_prompt['prompt'][:50]}...")
            else:
                self.log_result("Prompt Improvement (String)", False, f"Expected dict with 'prompt' key, got: {type(improved_prompt)}")
                
        except Exception as e:
            self.log_result("Prompt Improvement (String)", False, f"Exception: {e}")
        
        # Test dictionary task description
        try:
            improved_prompt2 = await self.prompt_generator.improve_prompt(
                'test-improvement-001',
                {'task': 'Make it more professional'},
                self.api_client,
                self.db
            )
            
            if isinstance(improved_prompt2, dict) and 'prompt' in improved_prompt2:
                self.log_result("Prompt Improvement (Dict)", True, f"Improved prompt: {improved_prompt2['prompt'][:50]}...")
            else:
                self.log_result("Prompt Improvement (Dict)", False, f"Expected dict with 'prompt' key, got: {type(improved_prompt2)}")
                
        except Exception as e:
            self.log_result("Prompt Improvement (Dict)", False, f"Exception: {e}")
    
    async def test_dashboard_functions(self):
        """Test dashboard functions"""
        print("\n📊 Testing Dashboard Functions...")
        
        # Test fetch_top_prompts
        try:
            top_prompts = fetch_top_prompts()
            if isinstance(top_prompts, list):
                if top_prompts:
                    required_fields = ['lineage_id', 'task', 'created_at', 'version_count', 'latest_version']
                    missing_fields = [field for field in required_fields if field not in top_prompts[0]]
                    if not missing_fields:
                        self.log_result("Dashboard Top Prompts", True, f"Retrieved {len(top_prompts)} prompts")
                    else:
                        self.log_result("Dashboard Top Prompts", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_result("Dashboard Top Prompts", True, "No prompts found")
            else:
                self.log_result("Dashboard Top Prompts", False, f"Expected list, got: {type(top_prompts)}")
        except Exception as e:
            self.log_result("Dashboard Top Prompts", False, f"Exception: {e}")
        
        # Test fetch_performance_stats
        try:
            stats = fetch_performance_stats()
            if isinstance(stats, dict):
                self.log_result("Dashboard Performance Stats", True, f"Stats retrieved: {stats}")
            else:
                self.log_result("Dashboard Performance Stats", False, f"Expected dict, got: {type(stats)}")
        except Exception as e:
            self.log_result("Dashboard Performance Stats", False, f"Exception: {e}")
    
    async def test_data_validation(self):
        """Test data validation"""
        print("\n✅ Testing Data Validation...")
        
        # Test prompt data validation
        try:
            invalid_prompt = {
                'id': 'test-validation',
                'task': 'Test validation',
                # Missing required fields
            }
            
            # This should fail validation
            result = self.db.save_prompt(invalid_prompt)
            if result is None:
                self.log_result("Data Validation", True, "Invalid data properly rejected")
            else:
                self.log_result("Data Validation", False, "Invalid data was accepted")
        except Exception as e:
            self.log_result("Data Validation", True, f"Validation exception caught: {e}")
    
    async def test_error_handling(self):
        """Test error handling"""
        print("\n🛡️ Testing Error Handling...")
        
        # Test getting non-existent prompt
        try:
            result = self.db.get_prompt('non-existent-id')
            if result is None:
                self.log_result("Error Handling - Non-existent Prompt", True, "Properly returned None")
            else:
                self.log_result("Error Handling - Non-existent Prompt", False, "Should return None")
        except Exception as e:
            self.log_result("Error Handling - Non-existent Prompt", False, f"Unexpected exception: {e}")
        
        # Test improving non-existent prompt
        try:
            result = await self.prompt_generator.improve_prompt(
                'non-existent-id',
                "test",
                self.api_client,
                self.db
            )
            self.log_result("Error Handling - Improve Non-existent", False, "Should have raised exception")
        except Exception as e:
            self.log_result("Error Handling - Improve Non-existent", True, f"Properly caught exception: {e}")
    
    async def test_integration(self):
        """Test integration scenarios"""
        print("\n🔗 Testing Integration...")
        
        # Test full workflow: generate -> save -> improve -> save
        try:
            # Generate
            generated = await self.prompt_generator.generate_initial_prompt(
                "Create a greeting", 
                self.api_client
            )
            
            if not generated or not isinstance(generated, dict):
                self.log_result("Integration - Full Workflow", False, "Generation failed")
                return
            
            # Save
            saved = self.db.save_prompt(generated)
            if not saved or not isinstance(saved, dict):
                self.log_result("Integration - Full Workflow", False, "Save failed")
                return
            
            # Improve
            improved = await self.prompt_generator.improve_prompt(
                saved['id'],
                "Make it more formal",
                self.api_client,
                self.db
            )
            
            if not improved or not isinstance(improved, dict):
                self.log_result("Integration - Full Workflow", False, "Improvement failed")
                return
            
            # Save improved
            saved_improved = self.db.save_prompt(improved)
            if not saved_improved or not isinstance(saved_improved, dict):
                self.log_result("Integration - Full Workflow", False, "Save improved failed")
                return
            
            self.log_result("Integration - Full Workflow", True, "Complete workflow successful")
            
        except Exception as e:
            self.log_result("Integration - Full Workflow", False, f"Exception: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['success']])
        failed_tests = len(self.errors)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.errors:
            print("\n❌ FAILED TESTS:")
            for error in self.errors:
                print(f"  - {error['test']}: {error['details']}")
        
        # Save detailed results
        with open('functional_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: functional_test_results.json")

async def main():
    """Run the comprehensive functional test suite"""
    test_suite = FunctionalTestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! System is fully functional.")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED! Issues need to be addressed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 