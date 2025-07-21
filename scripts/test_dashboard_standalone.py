#!/usr/bin/env python3
"""
Standalone test for dashboard functions without Streamlit dependency.
"""
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_platform.database import PromptDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dashboard_functions_standalone():
    """Test dashboard functions without Streamlit dependency"""
    print("🧪 Testing Dashboard Functions (Standalone)...")
    
    try:
        db = PromptDB()
        
        # Test 1: Performance stats
        print("\n📊 Test 1: Performance Stats")
        stats = db.get_performance_stats()
        if isinstance(stats, dict):
            print(f"✅ Performance stats: {stats}")
        else:
            print(f"❌ Expected dict, got: {type(stats)}")
            return False
        
        # Test 2: Top prompts
        print("\n🏆 Test 2: Top Prompts")
        top_prompts = db.get_top_prompts_by_versions(limit=3)
        if isinstance(top_prompts, list):
            if top_prompts:
                required_fields = ['lineage_id', 'task', 'created_at', 'version_count', 'latest_version']
                missing_fields = [field for field in required_fields if field not in top_prompts[0]]
                if not missing_fields:
                    print(f"✅ Top prompts: {len(top_prompts)} prompts with all fields")
                else:
                    print(f"❌ Missing fields: {missing_fields}")
                    return False
            else:
                print("✅ Top prompts: No prompts found (empty list)")
        else:
            print(f"❌ Expected list, got: {type(top_prompts)}")
            return False
        
        # Test 3: Recent prompts
        print("\n🕒 Test 3: Recent Prompts")
        recent_prompts = db.get_recent_prompts(limit=3)
        if isinstance(recent_prompts, list):
            print(f"✅ Recent prompts: {len(recent_prompts)} prompts")
        else:
            print(f"❌ Expected list, got: {type(recent_prompts)}")
            return False
        
        # Test 4: Trend data
        print("\n📈 Test 4: Trend Data")
        prompt_trends = db.count_prompts_by_date(days=7)
        example_trends = db.count_examples_by_date(days=7)
        if isinstance(prompt_trends, list) and isinstance(example_trends, list):
            print(f"✅ Prompt trends: {len(prompt_trends)} entries")
            print(f"✅ Example trends: {len(example_trends)} entries")
        else:
            print(f"❌ Expected lists, got: {type(prompt_trends)}, {type(example_trends)}")
            return False
        
        print("\n🎉 All dashboard function tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_functions_standalone()
    sys.exit(0 if success else 1) 