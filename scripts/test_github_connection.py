#!/usr/bin/env python3
"""
Test script to verify GitHub connection to PromptImprover repository.
"""
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")

def test_github_connection():
    """Test GitHub connection to PromptImprover repository."""
    print("🔗 Testing GitHub Connection to PromptImprover")
    print("=" * 50)
    
    # Check environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    github_owner = os.getenv('GITHUB_OWNER')
    github_repo = os.getenv('GITHUB_REPO')
    github_enabled = os.getenv('GITHUB_ENABLED', 'false').lower() == 'true'
    
    print(f"✅ GitHub Enabled: {github_enabled}")
    print(f"✅ Token Configured: {'Yes' if github_token else 'No'}")
    print(f"✅ Owner: {github_owner}")
    print(f"✅ Repository: {github_repo}")
    
    if not github_enabled:
        print("❌ GitHub integration is disabled. Set GITHUB_ENABLED=true")
        return False
    
    if not github_token:
        print("❌ GitHub token not found. Set GITHUB_TOKEN in .env file")
        return False
    
    if not github_owner or not github_repo:
        print("❌ GitHub owner or repository not configured")
        return False
    
    # Test connection
    try:
        from github import Github
        
        g = Github(github_token)
        repository = g.get_repo(f"{github_owner}/{github_repo}")
        
        print(f"✅ Successfully connected to {github_owner}/{github_repo}")
        print(f"📊 Repository: {repository.name}")
        print(f"📝 Description: {repository.description or 'No description'}")
        print(f"🌟 Stars: {repository.stargazers_count}")
        print(f"🍴 Forks: {repository.forks_count}")
        print(f"🌿 Default Branch: {repository.default_branch}")
        
        # Check if prompts folder exists
        try:
            repository.get_contents("prompts", ref=repository.default_branch)
            print("✅ Prompts folder exists")
        except:
            print("⚠️ Prompts folder does not exist")
            print("   Run the setup script or create it via UI")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("GitHub Connection Test")
        print("=" * 25)
        print("Tests connection to PromptImprover repository.")
        print("\nUsage:")
        print("  python scripts/test_github_connection.py")
        return
    
    success = test_github_connection()
    
    if success:
        print("\n🎉 GitHub integration is working!")
        print("🚀 You can now commit prompts to the repository.")
    else:
        print("\n❌ GitHub integration needs configuration.")
        print("📖 See README.md for setup instructions.")

if __name__ == "__main__":
    main() 