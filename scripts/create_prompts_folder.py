#!/usr/bin/env python3
"""
Create prompts folder in the PromptImprover repository.
"""
import os
from dotenv import load_dotenv
from github import Github

# Load environment variables
load_dotenv()

def create_prompts_folder():
    """Create prompts folder in the repository."""
    print("📁 Creating Prompts Folder in PromptImprover")
    print("=" * 50)
    
    # Get configuration
    github_token = os.getenv('GITHUB_TOKEN')
    github_owner = os.getenv('GITHUB_OWNER')
    github_repo = os.getenv('GITHUB_REPO')
    
    if not all([github_token, github_owner, github_repo]):
        print("❌ Missing GitHub configuration")
        return False
    
    try:
        # Connect to GitHub
        g = Github(github_token)
        repository = g.get_repo(f"{github_owner}/{github_repo}")
        
        print(f"✅ Connected to {github_owner}/{github_repo}")
        
        # Use the repository's default branch
        branch = repository.default_branch
        print(f"🌿 Using default branch: {branch}")
        
        # Check if prompts folder already exists
        try:
            repository.get_contents("prompts", ref=branch)
            print("✅ Prompts folder already exists")
            return True
        except:
            print("📁 Creating prompts folder...")
        
        # Create prompts folder with .gitkeep file
        content = """# This file ensures the prompts folder is tracked by git
# Prompts will be stored here as markdown files
# 
# Each prompt file will contain:
# - Prompt text
# - Metadata (version, model, etc.)
# - Generation process
# - Training examples
"""
        
        repository.create_file(
            path="prompts/.gitkeep",
            message="Create prompts folder for prompt management",
            content=content,
            branch=branch
        )
        
        print("✅ Prompts folder created successfully!")
        print(f"🔗 View at: https://github.com/{github_owner}/{github_repo}/tree/{branch}/prompts")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create prompts folder: {e}")
        return False

if __name__ == "__main__":
    create_prompts_folder() 