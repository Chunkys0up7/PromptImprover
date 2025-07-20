#!/usr/bin/env python3
"""
Simple API connection test script.
This helps diagnose authentication and connection issues with the Perplexity API.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_platform.api_client import APIClient, APIConfigurationError, APIAuthError
from prompt_platform.config import APP_CONFIG

async def test_api_connection():
    """Test the API connection with a simple request."""
    print("🔍 Testing API Connection...")
    print(f"API Base URL: {APP_CONFIG['api_base_url']}")
    print(f"Default Model: {APP_CONFIG['default_model']}")
    print(f"API Token: {'*' * (len(APP_CONFIG['api_token']) - 4) + APP_CONFIG['api_token'][-4:] if APP_CONFIG['api_token'] else 'NOT SET'}")
    print()
    
    try:
        # Initialize the API client
        api_client = APIClient()
        print("✅ API Client initialized successfully")
        
        # Test with a simple request
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, API test successful!'"}
        ]
        
        print("🔄 Testing API request...")
        response = await api_client.get_chat_completion(test_messages)
        
        print("✅ API request successful!")
        print(f"Response: {response}")
        
    except APIConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Check your .env file exists")
        print("2. Ensure API_TOKEN is set in your .env file")
        print("3. Verify the API_BASE_URL is correct")
        
    except APIAuthError as e:
        print(f"❌ Authentication Error: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Check if your API token is valid")
        print("2. Verify your Perplexity account is active")
        print("3. Check if you have sufficient credits")
        print("4. Try regenerating your API token")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the test
    asyncio.run(test_api_connection()) 