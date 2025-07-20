#!/usr/bin/env python3
"""
Simple script to toggle GitHub integration on/off.
"""
import os
import sys
from pathlib import Path

def toggle_github_integration():
    """Toggle GitHub integration on/off."""
    # Get the project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    
    # Check if .env file exists
    if not env_file.exists():
        print("❌ No .env file found. Creating one...")
        env_file.touch()
    
    # Read current .env content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Check current GitHub enabled status
    current_status = "disabled"
    github_enabled_line = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('GITHUB_ENABLED='):
            current_status = "enabled" if 'true' in line.lower() else "disabled"
            github_enabled_line = i
            break
    
    # Toggle the status
    new_status = "enabled" if current_status == "disabled" else "disabled"
    
    # Update or add the GITHUB_ENABLED line
    new_line = f"GITHUB_ENABLED={new_status}\n"
    
    if github_enabled_line is not None:
        lines[github_enabled_line] = new_line
    else:
        # Add GitHub section if it doesn't exist
        lines.append("\n# GitHub Integration\n")
        lines.append(new_line)
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ GitHub integration {new_status}!")
    print(f"📁 Updated: {env_file}")
    
    if new_status == "enabled":
        print("\n🔧 Next steps:")
        print("1. Set your GitHub token: GITHUB_TOKEN=your_token")
        print("2. Set repository: GITHUB_OWNER=username, GITHUB_REPO=repo_name")
        print("3. Restart the Streamlit app")
    else:
        print("\n💡 GitHub integration is now disabled.")
        print("   All GitHub features will be hidden from the UI.")

def show_status():
    """Show current GitHub integration status."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    
    if not env_file.exists():
        print("❌ No .env file found.")
        return
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    if 'GITHUB_ENABLED=true' in content.lower():
        print("✅ GitHub integration is ENABLED")
    elif 'GITHUB_ENABLED=false' in content.lower():
        print("🔴 GitHub integration is DISABLED")
    else:
        print("❓ GitHub integration status not set (defaults to disabled)")

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        show_status()
    else:
        print("🔄 Toggling GitHub integration...")
        toggle_github_integration()

if __name__ == "__main__":
    main() 