#!/usr/bin/env python3
"""
Setup script for GitHub integration with current project.
"""
import os
import sys
import subprocess
from pathlib import Path
import getpass

def detect_current_repo():
    """Detect the current project's GitHub repository."""
    project_root = Path(__file__).parent.parent
    
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            
            if 'github.com' in remote_url:
                if remote_url.startswith('https://github.com/'):
                    parts = remote_url.replace('https://github.com/', '').split('/')
                elif remote_url.startswith('git@github.com:'):
                    parts = remote_url.replace('git@github.com:', '').split('/')
                else:
                    return None
                
                if len(parts) >= 2:
                    owner = parts[0]
                    repo = parts[1].replace('.git', '')
                    return {
                        'owner': owner,
                        'repo': repo,
                        'url': remote_url
                    }
        
        return None
        
    except Exception as e:
        print(f"❌ Could not detect repository: {e}")
        return None

def create_prompts_folder(token, owner, repo):
    """Create prompts folder in the repository."""
    try:
        from github import Github
        
        g = Github(token)
        repository = g.get_repo(f"{owner}/{repo}")
        
        # Check if prompts folder exists
        try:
            repository.get_contents("prompts")
            print("✅ Prompts folder already exists")
            return True
        except:
            # Create prompts folder
            repository.create_file(
                path="prompts/.gitkeep",
                message="Create prompts folder for prompt management",
                content="# This file ensures the prompts folder is tracked by git\n# Prompts will be stored here as markdown files"
            )
            print("✅ Created prompts folder")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create prompts folder: {e}")
        return False

def setup_github_integration():
    """Setup GitHub integration for the current project."""
    print("🚀 GitHub Integration Setup")
    print("=" * 50)
    
    # Detect current repository
    current_repo = detect_current_repo()
    
    if not current_repo:
        print("❌ No GitHub repository detected.")
        print("   Make sure you're in a git repository with a GitHub remote.")
        return False
    
    print(f"🎯 Detected repository: {current_repo['owner']}/{current_repo['repo']}")
    
    # Get GitHub token
    print("\n🔑 GitHub Personal Access Token")
    print("   Create one at: https://github.com/settings/tokens")
    print("   Required permissions: repo")
    
    token = getpass.getpass("Enter your GitHub token: ").strip()
    
    if not token:
        print("❌ No token provided.")
        return False
    
    # Test token and create prompts folder
    print("\n📁 Creating prompts folder...")
    if create_prompts_folder(token, current_repo['owner'], current_repo['repo']):
        print("✅ Prompts folder ready!")
    else:
        print("❌ Failed to create prompts folder.")
        return False
    
    # Update .env file
    env_file = project_root / '.env'
    
    if not env_file.exists():
        env_file.touch()
    
    # Read current .env content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update or add GitHub configuration
    github_config = {
        'GITHUB_ENABLED': 'true',
        'GITHUB_TOKEN': token,
        'GITHUB_OWNER': current_repo['owner'],
        'GITHUB_REPO': current_repo['repo']
    }
    
    updated_lines = []
    github_section_found = False
    
    for line in lines:
        if line.strip().startswith('GITHUB_'):
            github_section_found = True
            key = line.split('=')[0].strip()
            if key in github_config:
                updated_lines.append(f"{key}={github_config[key]}\n")
                del github_config[key]
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add any remaining GitHub config
    if github_config:
        if not github_section_found:
            updated_lines.append("\n# GitHub Integration\n")
        
        for key, value in github_config.items():
            updated_lines.append(f"{key}={value}\n")
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"\n✅ GitHub integration configured!")
    print(f"📁 Updated: {env_file}")
    print(f"🔗 Repository: {current_repo['owner']}/{current_repo['repo']}")
    print(f"📂 Prompts folder: prompts/")
    
    print("\n🚀 Next steps:")
    print("1. Restart the Streamlit app")
    print("2. Generate prompts and commit them to GitHub")
    print("3. View your prompts at: https://github.com/{}/{}/tree/main/prompts".format(
        current_repo['owner'], current_repo['repo']
    ))
    
    return True

def main():
    """Main function."""
    global project_root
    project_root = Path(__file__).parent.parent
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("GitHub Integration Setup")
        print("=" * 30)
        print("This script configures GitHub integration for the current project.")
        print("\nUsage:")
        print("  python scripts/setup_github.py")
        print("\nRequirements:")
        print("  - Git repository with GitHub remote")
        print("  - GitHub Personal Access Token with repo permissions")
        return
    
    setup_github_integration()

if __name__ == "__main__":
    main() 