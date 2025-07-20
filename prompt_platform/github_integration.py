"""
GitHub integration module for committing prompts to repositories.

This module provides functionality to:
- Connect to GitHub repositories
- Commit prompts with proper formatting
- Handle authentication and repository management
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import streamlit as st
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class GitHubIntegration:
    """Handles GitHub integration for prompt management."""
    
    def __init__(self):
        """Initialize GitHub integration."""
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.default_owner = os.getenv('GITHUB_OWNER')
        self.default_repo = os.getenv('GITHUB_REPO')
        self.enabled = os.getenv('GITHUB_ENABLED', 'false').lower() == 'true'
        self.project_root = Path(__file__).parent.parent
        
    def detect_current_repo(self) -> Optional[Dict[str, str]]:
        """Detect the current project's GitHub repository."""
        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                remote_url = result.stdout.strip()
                
                # Parse GitHub URL
                if 'github.com' in remote_url:
                    # Handle different URL formats
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
            logger.warning(f"Could not detect current repository: {e}")
            return None
    
    def create_prompts_folder(self, owner: str, repo: str) -> bool:
        """Create a prompts folder in the repository if it doesn't exist."""
        try:
            from github import Github
            
            g = Github(self.github_token)
            repository = g.get_repo(f"{owner}/{repo}")
            
            # Use the repository's default branch
            branch = repository.default_branch
            
            # Check if prompts folder exists
            try:
                repository.get_contents("prompts", ref=branch)
                logger.info("Prompts folder already exists")
                return True
            except:
                # Create prompts folder
                repository.create_file(
                    path="prompts/.gitkeep",
                    message="Create prompts folder for prompt management",
                    content="# This file ensures the prompts folder is tracked by git\n# Prompts will be stored here as markdown files",
                    branch=branch
                )
                logger.info("Created prompts folder")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create prompts folder: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if GitHub integration is enabled."""
        return self.enabled
        
    def is_configured(self) -> bool:
        """Check if GitHub integration is properly configured."""
        return bool(self.enabled and self.github_token and self.default_owner and self.default_repo)
    
    def get_repository_info(self) -> Dict[str, str]:
        """Get current repository configuration."""
        return {
            'owner': self.default_owner,
            'repo': self.default_repo,
            'configured': self.is_configured()
        }
    
    def format_prompt_for_github(self, prompt_data: Dict[str, Any]) -> str:
        """Format prompt data for GitHub commit."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# {prompt_data.get('task', 'Untitled Prompt')}

**Version:** {prompt_data.get('version', 1)}  
**Created:** {prompt_data.get('created_at', timestamp)}  
**Lineage ID:** {prompt_data.get('lineage_id', 'N/A')}

## Prompt

```
{prompt_data.get('prompt', '')}
```

## Generation Process

{prompt_data.get('generation_process', 'No generation process recorded.')}

## Training Data

"""
        
        # Add training data if available
        if prompt_data.get('training_data'):
            try:
                training_data = json.loads(prompt_data['training_data'])
                if training_data:
                    content += "### Examples\n\n"
                    for i, example in enumerate(training_data, 1):
                        content += f"**Example {i}:**\n"
                        content += f"- Input: `{example.get('input', 'N/A')}`\n"
                        content += f"- Output: `{example.get('output', 'N/A')}`\n\n"
                else:
                    content += "No training examples available.\n"
            except json.JSONDecodeError:
                content += "Training data format error.\n"
        else:
            content += "No training data available.\n"
        
        return content
    
    def commit_prompt_to_github(self, prompt_data: Dict[str, Any], 
                               owner: Optional[str] = None, 
                               repo: Optional[str] = None,
                               branch: Optional[str] = None) -> Dict[str, Any]:
        """Commit a prompt to GitHub repository."""
        if not self.is_configured():
            return {
                'success': False,
                'error': 'GitHub integration not configured. Please set GITHUB_TOKEN, GITHUB_OWNER, and GITHUB_REPO environment variables.'
            }
        
        try:
            # Import PyGithub
            from github import Github
            
            # Use provided values or defaults
            owner = owner or self.default_owner
            repo = repo or self.default_repo
            
            # Initialize GitHub client
            g = Github(self.github_token)
            
            # Get repository
            repository = g.get_repo(f"{owner}/{repo}")
            
            # Detect default branch if not provided
            if not branch:
                branch = repository.default_branch
                logger.info(f"Using default branch: {branch}")
            
            # Format the prompt content
            content = self.format_prompt_for_github(prompt_data)
            
            # Create filename
            task_name = prompt_data.get('task', 'untitled_prompt')
            safe_task_name = "".join(c for c in task_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_task_name = safe_task_name.replace(' ', '_').lower()
            filename = f"prompts/{safe_task_name}_v{prompt_data.get('version', 1)}.md"
            
            # Commit message
            commit_message = f"Add prompt: {prompt_data.get('task', 'Untitled')} (v{prompt_data.get('version', 1)})"
            
            try:
                # Try to create the file
                result = repository.create_file(
                    path=filename,
                    message=commit_message,
                    content=content,
                    branch=branch
                )
                
                logger.info(f"Successfully committed to GitHub: {filename}")
                
                return {
                    'success': True,
                    'message': f'Prompt committed to GitHub: {filename}',
                    'filename': filename,
                    'url': result['content'].html_url,
                    'sha': result['content'].sha
                }
                
            except Exception as e:
                error_message = str(e).lower()
                if "already exists" in error_message or "sha" in error_message:
                    # File already exists, update it
                    try:
                        # Get the current file
                        file = repository.get_contents(filename, ref=branch)
                        
                        # Check if content is actually different
                        if file.content == content:
                            return {
                                'success': True,
                                'message': f'Prompt already exists on GitHub: {filename}',
                                'filename': filename,
                                'url': file.html_url,
                                'sha': file.sha,
                                'note': 'No changes needed - file is already up to date'
                            }
                        
                        # Update the file
                        result = repository.update_file(
                            path=filename,
                            message=f"Update {commit_message}",
                            content=content,
                            sha=file.sha,
                            branch=branch
                        )
                        
                        logger.info(f"Successfully updated on GitHub: {filename}")
                        
                        return {
                            'success': True,
                            'message': f'Prompt updated on GitHub: {filename}',
                            'filename': filename,
                            'url': result['content'].html_url,
                            'sha': result['content'].sha
                        }
                        
                    except Exception as update_error:
                        logger.error(f"Failed to update file on GitHub: {update_error}")
                        return {
                            'success': False,
                            'error': f'Failed to update file on GitHub: {str(update_error)}'
                        }
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"Failed to commit to GitHub: {e}")
            
            # Provide more user-friendly error messages
            error_str = str(e).lower()
            if "sha" in error_str and "wasn't supplied" in error_str:
                user_message = "This prompt has already been committed to GitHub with the same content. No changes needed."
            elif "already exists" in error_str:
                user_message = "This prompt already exists on GitHub. The system will update it if there are changes."
            elif "not found" in error_str:
                user_message = "Repository or branch not found. Please check your GitHub configuration."
            elif "unauthorized" in error_str or "401" in error_str:
                user_message = "GitHub authentication failed. Please check your GitHub token."
            elif "forbidden" in error_str or "403" in error_str:
                user_message = "Access denied. Please check your GitHub permissions."
            else:
                user_message = f"GitHub error: {str(e)}"
            
            return {
                'success': False,
                'error': user_message
            }
    
    def get_github_settings_ui(self) -> Dict[str, Any]:
        """Render GitHub settings UI and return configuration."""
        st.subheader("🔗 GitHub Integration")
        
        # Main toggle for GitHub integration
        github_enabled = st.toggle(
            "Enable GitHub Integration",
            value=self.enabled,
            help="Turn GitHub integration on/off. When disabled, all GitHub features will be hidden."
        )
        
        # Update the enabled state
        self.enabled = github_enabled
        os.environ['GITHUB_ENABLED'] = str(github_enabled).lower()
        
        if not github_enabled:
            st.info("💡 GitHub integration is disabled. Enable it above to configure repository settings.")
            return {
                'enabled': False,
                'configured': False
            }
        
        # Detect current repository
        current_repo = self.detect_current_repo()
        
        if current_repo:
            st.success(f"🎯 **Current Repository Detected:** {current_repo['owner']}/{current_repo['repo']}")
            
            # Auto-configure option
            if st.button("🚀 Use Current Repository", key="use_current_repo"):
                self.default_owner = current_repo['owner']
                self.default_repo = current_repo['repo']
                os.environ['GITHUB_OWNER'] = current_repo['owner']
                os.environ['GITHUB_REPO'] = current_repo['repo']
                
                # Create prompts folder
                if self.github_token:
                    if self.create_prompts_folder(current_repo['owner'], current_repo['repo']):
                        st.success("✅ Prompts folder created/verified in repository!")
                    else:
                        st.warning("⚠️ Could not create prompts folder. Check your token permissions.")
                
                st.success("✅ Current repository configured!")
                st.rerun()
        
        # Show configuration status
        if not self.is_configured():
            st.warning("⚠️ GitHub integration enabled but not fully configured. Configure below.")
        else:
            st.success("✅ GitHub integration is enabled and configured!")
        
        # GitHub configuration
        with st.expander("⚙️ GitHub Configuration", expanded=not self.is_configured()):
            github_token = st.text_input(
                "GitHub Personal Access Token",
                value=self.github_token or "",
                type="password",
                help="Create a token at https://github.com/settings/tokens with repo permissions"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                owner = st.text_input(
                    "Repository Owner",
                    value=self.default_owner or "",
                    help="GitHub username or organization name"
                )
            
            with col2:
                repo_name = st.text_input(
                    "Repository Name",
                    value=self.default_repo or "",
                    help="Name of the repository to commit to"
                )
            
            branch = st.text_input(
                "Branch",
                value="main",
                help="Branch to commit to (default: main)"
            )
            
            # Prompts folder management
            if st.button("📁 Create/Verify Prompts Folder", key="create_prompts_folder"):
                if github_token and owner and repo_name:
                    if self.create_prompts_folder(owner, repo_name):
                        st.success("✅ Prompts folder created/verified!")
                    else:
                        st.error("❌ Failed to create prompts folder. Check permissions.")
                else:
                    st.error("❌ Please configure GitHub token and repository first.")
            
            if st.button("🔗 Test Connection", key="test_github"):
                if github_token and owner and repo_name:
                    st.success("✅ GitHub configuration looks good!")
                    return {
                        'enabled': True,
                        'token': github_token,
                        'owner': owner,
                        'repo': repo_name,
                        'branch': branch,
                        'configured': True
                    }
                else:
                    st.error("❌ Please fill in all required fields.")
                    return {'enabled': True, 'configured': False}
        
        return {
            'enabled': True,
            'token': github_token or self.github_token,
            'owner': owner or self.default_owner,
            'repo': repo_name or self.default_repo,
            'branch': branch,
            'configured': bool(github_token and owner and repo_name)
        }

def commit_prompt_with_github_option(prompt_data: Dict[str, Any]) -> bool:
    """Show GitHub commit option and handle the commit process."""
    github_integration = GitHubIntegration()
    
    # Don't show anything if GitHub is disabled
    if not github_integration.is_enabled():
        return False
    
    st.markdown("---")
    st.subheader("📤 Commit to GitHub")
    
    # Check if GitHub is configured
    if not github_integration.is_configured():
        st.info("💡 Want to save your prompts to GitHub? Configure GitHub integration in the Settings tab.")
        return False
    
    # Show commit option
    repo_info = github_integration.get_repository_info()
    st.success(f"✅ Connected to: {repo_info['owner']}/{repo_info['repo']}")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💾 Your prompt can be committed to GitHub for version control and sharing.")
    
    with col2:
        if st.button("🚀 Commit to GitHub", key="commit_github", use_container_width=True):
            with st.spinner("Committing to GitHub..."):
                result = github_integration.commit_prompt_to_github(prompt_data)
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                    if 'url' in result:
                        st.markdown(f"🔗 [View on GitHub]({result['url']})")
                    return True
                else:
                    st.error(f"❌ {result['error']}")
                    return False
    
    return False 