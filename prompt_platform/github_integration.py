"""
Enhanced GitHub Integration for the Prompt Platform.

This module provides comprehensive GitHub integration with conflict resolution,
bidirectional sync, and advanced authentication handling.
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import aiohttp
import aiofiles
from git import Repo, GitCommandError
from git.exc import GitError

from .schemas import PromptSchema, ExampleSchema, validate_prompt_data, validate_example_data
from .error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class SyncDirection(Enum):
    """Sync direction enumeration"""
    PUSH = "push"
    PULL = "pull"
    BIDIRECTIONAL = "bidirectional"

class ConflictResolution(Enum):
    """Conflict resolution strategy"""
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    MANUAL = "manual"
    MERGE = "merge"

@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    direction: SyncDirection
    conflicts_resolved: int = 0
    prompts_synced: int = 0
    examples_synced: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class GitHubIntegration:
    """Enhanced GitHub integration with conflict resolution and bidirectional sync"""
    
    def __init__(self, repo_path: str = None, remote_url: str = None, 
                 auth_token: str = None, branch: str = "main"):
        """Initialize GitHub integration"""
        self.repo_path = repo_path or os.path.join(os.getcwd(), "prompt_repo")
        
        # Check for GitHub configuration in environment variables
        self.auth_token = auth_token or os.getenv("GITHUB_TOKEN")
        
        # Build remote URL from owner and repo if not provided
        if remote_url:
            self.remote_url = remote_url
        elif os.getenv("GITHUB_REPO_URL"):
            self.remote_url = os.getenv("GITHUB_REPO_URL")
        elif os.getenv("GITHUB_OWNER") and os.getenv("GITHUB_REPO"):
            self.remote_url = f"https://github.com/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}.git"
        else:
            self.remote_url = None
            
        self.branch = branch
        self.error_handler = ErrorHandler()
        
        # Ensure repo directory exists
        os.makedirs(self.repo_path, exist_ok=True)
        
        # Initialize or open repository
        self.repo = self._initialize_repository()
        
        logger.info(f"GitHub integration initialized for {self.repo_path}")
    
    def _initialize_repository(self) -> Repo:
        """Initialize or open Git repository"""
        try:
            if os.path.exists(os.path.join(self.repo_path, ".git")):
                # Open existing repository
                repo = Repo(self.repo_path)
                logger.info("Opened existing Git repository")
            else:
                # Initialize new repository
                repo = Repo.init(self.repo_path)
                logger.info("Initialized new Git repository")
                
                # Add remote if provided
                if self.remote_url:
                    self._add_remote(repo, "origin", self.remote_url)
            
            return repo
            
        except GitError as e:
            logger.error(f"Failed to initialize repository: {e}")
            raise
    
    def _add_remote(self, repo: Repo, name: str, url: str):
        """Add remote to repository"""
        try:
            # Remove existing remote if it exists
            try:
                repo.delete_remote(name)
            except:
                pass
            
            # Add new remote
            repo.create_remote(name, url)
            logger.info(f"Added remote '{name}' with URL: {url}")
            
        except GitError as e:
            logger.error(f"Failed to add remote: {e}")
            raise
    
    def _get_auth_url(self, url: str) -> str:
        """Add authentication to URL if token is provided"""
        if self.auth_token and "github.com" in url:
            # Replace https:// with https://token@
            if url.startswith("https://"):
                return url.replace("https://", f"https://{self.auth_token}@")
        return url
    
    async def setup_repository(self, repo_name: str, description: str = None, 
                             private: bool = False) -> bool:
        """Setup a new GitHub repository"""
        try:
            if not self.auth_token:
                raise ValueError("GitHub token is required for repository setup")
            
            # Create repository via GitHub API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"token {self.auth_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                data = {
                    "name": repo_name,
                    "description": description or "Prompt Platform Repository",
                    "private": private,
                    "auto_init": True
                }
                
                async with session.post(
                    "https://api.github.com/user/repos",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 201:
                        repo_data = await response.json()
                        self.remote_url = repo_data["clone_url"]
                        
                        # Update local repository
                        self._add_remote(self.repo, "origin", self.remote_url)
                        
                        logger.info(f"Created GitHub repository: {repo_name}")
                        return True
                    else:
                        error_data = await response.json()
                        raise Exception(f"Failed to create repository: {error_data}")
                        
        except Exception as e:
            logger.error(f"Failed to setup repository: {e}")
            return False
    
    async def sync_prompts(self, prompts: List[Dict[str, Any]], 
                          direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
                          conflict_resolution: ConflictResolution = ConflictResolution.LOCAL_WINS) -> SyncResult:
        """Sync prompts with GitHub repository"""
        result = SyncResult(success=False, direction=direction)
        
        try:
            # Ensure we're on the correct branch
            self._ensure_branch()
            
            if direction in [SyncDirection.PULL, SyncDirection.BIDIRECTIONAL]:
                # Pull latest changes
                await self._pull_latest()
            
            # Handle conflicts if any
            conflicts = await self._detect_conflicts()
            if conflicts:
                result.conflicts_resolved = await self._resolve_conflicts(
                    conflicts, conflict_resolution
                )
            
            # Sync prompts based on direction
            if direction in [SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL]:
                result.prompts_synced = await self._push_prompts(prompts)
            
            if direction in [SyncDirection.PULL, SyncDirection.BIDIRECTIONAL]:
                pulled_prompts = await self._pull_prompts()
                result.prompts_synced += len(pulled_prompts)
            
            # Commit and push changes
            if result.prompts_synced > 0:
                await self._commit_and_push(f"Sync {result.prompts_synced} prompts")
            
            result.success = True
            logger.info(f"Successfully synced {result.prompts_synced} prompts")
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Failed to sync prompts: {e}")
        
        return result
    
    async def sync_examples(self, examples: List[Dict[str, Any]],
                           direction: SyncDirection = SyncDirection.BIDIRECTIONAL) -> SyncResult:
        """Sync training examples with GitHub repository"""
        result = SyncResult(success=False, direction=direction)
        
        try:
            # Ensure we're on the correct branch
            self._ensure_branch()
            
            if direction in [SyncDirection.PULL, SyncDirection.BIDIRECTIONAL]:
                await self._pull_latest()
            
            # Sync examples
            if direction in [SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL]:
                result.examples_synced = await self._push_examples(examples)
            
            if direction in [SyncDirection.PULL, SyncDirection.BIDIRECTIONAL]:
                pulled_examples = await self._pull_examples()
                result.examples_synced += len(pulled_examples)
            
            # Commit and push changes
            if result.examples_synced > 0:
                await self._commit_and_push(f"Sync {result.examples_synced} examples")
            
            result.success = True
            logger.info(f"Successfully synced {result.examples_synced} examples")
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Failed to sync examples: {e}")
        
        return result
    
    def _ensure_branch(self):
        """Ensure we're on the correct branch"""
        try:
            current_branch = self.repo.active_branch.name
            if current_branch != self.branch:
                # Checkout the target branch
                if self.branch in [ref.name for ref in self.repo.references]:
                    self.repo.heads[self.branch].checkout()
                else:
                    # Create new branch
                    new_branch = self.repo.create_head(self.branch)
                    new_branch.checkout()
                
                logger.info(f"Switched to branch: {self.branch}")
                
        except GitError as e:
            logger.error(f"Failed to ensure branch: {e}")
            raise
    
    async def _pull_latest(self):
        """Pull latest changes from remote"""
        try:
            if "origin" in self.repo.remotes:
                origin = self.repo.remotes.origin
                origin.pull()
                logger.info("Pulled latest changes from remote")
            else:
                logger.warning("No remote 'origin' found")
                
        except GitError as e:
            logger.error(f"Failed to pull latest changes: {e}")
            raise
    
    async def _detect_conflicts(self) -> List[Dict[str, Any]]:
        """Detect merge conflicts"""
        conflicts = []
        
        try:
            # Check for merge conflicts
            if self.repo.index.unmerged_blobs():
                for path in self.repo.index.unmerged_blobs():
                    conflicts.append({
                        "path": path,
                        "type": "merge_conflict",
                        "description": f"Merge conflict in {path}"
                    })
            
            # Check for file conflicts (same file modified in different ways)
            if "origin" in self.repo.remotes:
                try:
                    # Compare local and remote versions
                    local_commit = self.repo.head.commit
                    remote_commit = self.repo.remotes.origin.refs[self.branch].commit
                    
                    if local_commit != remote_commit:
                        # Check for divergent changes
                        diff = local_commit.diff(remote_commit)
                        for change in diff:
                            if change.change_type in ['M', 'A', 'D']:
                                conflicts.append({
                                    "path": change.a_path or change.b_path,
                                    "type": "divergent_change",
                                    "description": f"Divergent change in {change.a_path or change.b_path}"
                                })
                except:
                    pass
            
            logger.info(f"Detected {len(conflicts)} conflicts")
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
            return conflicts
    
    async def _resolve_conflicts(self, conflicts: List[Dict[str, Any]], 
                                strategy: ConflictResolution) -> int:
        """Resolve conflicts using specified strategy"""
        resolved_count = 0
        
        try:
            for conflict in conflicts:
                if strategy == ConflictResolution.LOCAL_WINS:
                    # Keep local version
                    await self._resolve_conflict_local_wins(conflict)
                    resolved_count += 1
                    
                elif strategy == ConflictResolution.REMOTE_WINS:
                    # Keep remote version
                    await self._resolve_conflict_remote_wins(conflict)
                    resolved_count += 1
                    
                elif strategy == ConflictResolution.MERGE:
                    # Attempt to merge
                    if await self._resolve_conflict_merge(conflict):
                        resolved_count += 1
                        
                elif strategy == ConflictResolution.MANUAL:
                    # Mark for manual resolution
                    logger.warning(f"Manual resolution required for: {conflict['path']}")
            
            logger.info(f"Resolved {resolved_count} conflicts using {strategy.value} strategy")
            return resolved_count
            
        except Exception as e:
            logger.error(f"Failed to resolve conflicts: {e}")
            return resolved_count
    
    async def _resolve_conflict_local_wins(self, conflict: Dict[str, Any]):
        """Resolve conflict by keeping local version"""
        try:
            if conflict["type"] == "merge_conflict":
                # Remove conflict markers and keep local version
                path = conflict["path"]
                if os.path.exists(path):
                    # Read file and remove conflict markers
                    async with aiofiles.open(path, 'r') as f:
                        content = await f.read()
                    
                    # Remove conflict markers
                    lines = content.split('\n')
                    resolved_lines = []
                    in_conflict = False
                    
                    for line in lines:
                        if line.startswith('<<<<<<<') or line.startswith('=======') or line.startswith('>>>>>>>'):
                            in_conflict = not in_conflict
                        elif not in_conflict:
                            resolved_lines.append(line)
                    
                    # Write resolved content
                    async with aiofiles.open(path, 'w') as f:
                        await f.write('\n'.join(resolved_lines))
                    
                    # Stage the resolved file
                    self.repo.index.add([path])
            
            logger.info(f"Resolved conflict in {conflict['path']} (local wins)")
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict (local wins): {e}")
            raise
    
    async def _resolve_conflict_remote_wins(self, conflict: Dict[str, Any]):
        """Resolve conflict by keeping remote version"""
        try:
            if conflict["type"] == "merge_conflict":
                # Checkout remote version
                path = conflict["path"]
                self.repo.git.checkout('--theirs', path)
                self.repo.index.add([path])
            
            logger.info(f"Resolved conflict in {conflict['path']} (remote wins)")
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict (remote wins): {e}")
            raise
    
    async def _resolve_conflict_merge(self, conflict: Dict[str, Any]) -> bool:
        """Attempt to merge conflicting changes"""
        try:
            # This is a simplified merge strategy
            # In a real implementation, you might want more sophisticated merging
            logger.info(f"Attempting to merge conflict in {conflict['path']}")
            
            # For now, default to local wins for merge conflicts
            await self._resolve_conflict_local_wins(conflict)
            return True
            
        except Exception as e:
            logger.error(f"Failed to merge conflict: {e}")
            return False
    
    async def _push_prompts(self, prompts: List[Dict[str, Any]]) -> int:
        """Push prompts to repository"""
        pushed_count = 0
        
        try:
            prompts_dir = os.path.join(self.repo_path, "prompts")
            os.makedirs(prompts_dir, exist_ok=True)
            
            for prompt in prompts:
                try:
                    # Validate prompt data
                    validated_prompt = validate_prompt_data(prompt)
                    
                    # Create prompt file
                    prompt_file = os.path.join(prompts_dir, f"{validated_prompt.id}.json")
                    async with aiofiles.open(prompt_file, 'w') as f:
                        await f.write(validated_prompt.json(indent=2))
                    
                    # Stage the file
                    self.repo.index.add([prompt_file])
                    pushed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to push prompt {prompt.get('id', 'unknown')}: {e}")
            
            logger.info(f"Pushed {pushed_count} prompts to repository")
            return pushed_count
            
        except Exception as e:
            logger.error(f"Failed to push prompts: {e}")
            return pushed_count
    
    async def _push_examples(self, examples: List[Dict[str, Any]]) -> int:
        """Push examples to repository"""
        pushed_count = 0
        
        try:
            examples_dir = os.path.join(self.repo_path, "examples")
            os.makedirs(examples_dir, exist_ok=True)
            
            for example in examples:
                try:
                    # Validate example data
                    validated_example = validate_example_data(example)
                    
                    # Create example file
                    example_file = os.path.join(examples_dir, f"{validated_example.id}.json")
                    async with aiofiles.open(example_file, 'w') as f:
                        await f.write(validated_example.json(indent=2))
                    
                    # Stage the file
                    self.repo.index.add([example_file])
                    pushed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to push example {example.get('id', 'unknown')}: {e}")
            
            logger.info(f"Pushed {pushed_count} examples to repository")
            return pushed_count
            
        except Exception as e:
            logger.error(f"Failed to push examples: {e}")
            return pushed_count
    
    async def _pull_prompts(self) -> List[Dict[str, Any]]:
        """Pull prompts from repository"""
        prompts = []
        
        try:
            prompts_dir = os.path.join(self.repo_path, "prompts")
            if os.path.exists(prompts_dir):
                for filename in os.listdir(prompts_dir):
                    if filename.endswith('.json'):
                        try:
                            prompt_file = os.path.join(prompts_dir, filename)
                            async with aiofiles.open(prompt_file, 'r') as f:
                                content = await f.read()
                            
                            prompt_data = json.loads(content)
                            validated_prompt = validate_prompt_data(prompt_data)
                            prompts.append(validated_prompt.dict())
                            
                        except Exception as e:
                            logger.error(f"Failed to load prompt from {filename}: {e}")
            
            logger.info(f"Pulled {len(prompts)} prompts from repository")
            return prompts
            
        except Exception as e:
            logger.error(f"Failed to pull prompts: {e}")
            return prompts
    
    async def _pull_examples(self) -> List[Dict[str, Any]]:
        """Pull examples from repository"""
        examples = []
        
        try:
            examples_dir = os.path.join(self.repo_path, "examples")
            if os.path.exists(examples_dir):
                for filename in os.listdir(examples_dir):
                    if filename.endswith('.json'):
                        try:
                            example_file = os.path.join(examples_dir, filename)
                            async with aiofiles.open(example_file, 'r') as f:
                                content = await f.read()
                            
                            example_data = json.loads(content)
                            validated_example = validate_example_data(example_data)
                            examples.append(validated_example.dict())
                            
                        except Exception as e:
                            logger.error(f"Failed to load example from {filename}: {e}")
            
            logger.info(f"Pulled {len(examples)} examples from repository")
            return examples
            
        except Exception as e:
            logger.error(f"Failed to pull examples: {e}")
            return examples
    
    async def _commit_and_push(self, message: str):
        """Commit and push changes"""
        try:
            # Check if there are changes to commit
            if self.repo.is_dirty():
                # Commit changes
                self.repo.index.commit(message)
                logger.info(f"Committed changes: {message}")
                
                # Push to remote
                if "origin" in self.repo.remotes:
                    origin = self.repo.remotes.origin
                    origin.push()
                    logger.info("Pushed changes to remote")
                else:
                    logger.warning("No remote 'origin' found for push")
            else:
                logger.info("No changes to commit")
                
        except GitError as e:
            logger.error(f"Failed to commit and push: {e}")
            raise
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        try:
            status = {
                "repo_path": self.repo_path,
                "branch": self.branch,
                "has_remote": "origin" in self.repo.remotes,
                "is_dirty": self.repo.is_dirty(),
                "last_commit": None,
                "remote_ahead": 0,
                "local_ahead": 0
            }
            
            # Get last commit info
            if self.repo.head.commit:
                status["last_commit"] = {
                    "hash": self.repo.head.commit.hexsha[:8],
                    "message": self.repo.head.commit.message.strip(),
                    "author": str(self.repo.head.commit.author),
                    "date": self.repo.head.commit.committed_datetime.isoformat()
                }
            
            # Check sync status with remote
            if "origin" in self.repo.remotes:
                try:
                    origin = self.repo.remotes.origin
                    origin.fetch()
                    
                    local_commit = self.repo.head.commit
                    remote_commit = origin.refs[self.branch].commit
                    
                    if local_commit != remote_commit:
                        # Count commits ahead/behind
                        status["local_ahead"] = len(list(self.repo.iter_commits(f"{local_commit}..{remote_commit}")))
                        status["remote_ahead"] = len(list(self.repo.iter_commits(f"{remote_commit}..{local_commit}")))
                        
                except GitError:
                    pass
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {"error": str(e)}
    
    async def backup_to_github(self, prompts: List[Dict[str, Any]], 
                              examples: List[Dict[str, Any]]) -> bool:
        """Create a complete backup to GitHub"""
        try:
            # Sync prompts
            prompt_result = await self.sync_prompts(prompts, SyncDirection.PUSH)
            
            # Sync examples
            example_result = await self.sync_examples(examples, SyncDirection.PUSH)
            
            if prompt_result.success and example_result.success:
                logger.info("Successfully backed up to GitHub")
                return True
            else:
                logger.error("Failed to backup to GitHub")
                return False
                
        except Exception as e:
            logger.error(f"Failed to backup to GitHub: {e}")
            return False
    
    async def restore_from_github(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Restore data from GitHub"""
        try:
            # Pull latest changes
            await self._pull_latest()
            
            # Pull prompts and examples
            prompts = await self._pull_prompts()
            examples = await self._pull_examples()
            
            logger.info(f"Restored {len(prompts)} prompts and {len(examples)} examples from GitHub")
            return prompts, examples
            
        except Exception as e:
            logger.error(f"Failed to restore from GitHub: {e}")
            return [], []
    
    # --- UI Methods for Streamlit Integration ---
    
    def get_github_settings_ui(self) -> Dict[str, Any]:
        """Get GitHub settings UI configuration"""
        return {
            "enabled": self.is_enabled(),
            "configured": self.is_configured(),
            "repo_info": self.get_repository_info() if self.is_configured() else None
        }
    
    def is_enabled(self) -> bool:
        """Check if GitHub integration is enabled"""
        return bool(self.auth_token and self.remote_url)
    
    def is_configured(self) -> bool:
        """Check if GitHub integration is properly configured"""
        return bool(self.auth_token and self.remote_url and os.path.exists(self.repo_path))
    
    def get_repository_info(self) -> Dict[str, str]:
        """Get repository information"""
        try:
            if self.remote_url:
                # Extract owner and repo from URL
                if "github.com" in self.remote_url:
                    parts = self.remote_url.split("github.com/")[-1].replace(".git", "").split("/")
                    if len(parts) >= 2:
                        return {
                            "owner": parts[0],
                            "repo": parts[1],
                            "url": self.remote_url
                        }
            return {"owner": "unknown", "repo": "unknown", "url": self.remote_url or ""}
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            return {"owner": "error", "repo": "error", "url": ""} 