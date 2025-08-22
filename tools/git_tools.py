"""
Git Tools for repository management
"""

import os
import git
from typing import Optional, Dict, Any, List
from pathlib import Path


def clone_repository(
    repo_url: str,
    target_path: str,
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clone a Git repository to a local path.
    
    Args:
        repo_url: URL of the repository to clone
        target_path: Local path where to clone the repository
        branch: Optional branch to checkout after cloning
        
    Returns:
        Dictionary with operation status and details
    """
    try:
        # Ensure target directory exists
        os.makedirs(target_path, exist_ok=True)
        
        # Clone the repository
        repo = git.Repo.clone_from(repo_url, target_path)
        
        # Checkout specific branch if provided
        if branch and branch in repo.remotes.origin.refs:
            repo.git.checkout(branch)
        
        return {
            "status": "Success",
            "local_path": target_path,
            "repo_url": repo_url,
            "current_branch": repo.active_branch.name,
            "commit_hash": repo.head.commit.hexsha,
            "message": f"Successfully cloned repository to {target_path}"
        }
    except git.exc.GitCommandError as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Failed to clone repository: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Unexpected error: {str(e)}"
        }


def create_branch(
    repo_path: str,
    branch_name: str,
    checkout: bool = True
) -> Dict[str, Any]:
    """
    Create a new branch in an existing repository.
    
    Args:
        repo_path: Path to the local repository
        branch_name: Name of the new branch
        checkout: Whether to checkout the new branch
        
    Returns:
        Dictionary with operation status and details
    """
    try:
        repo = git.Repo(repo_path)
        
        # Check if branch already exists
        if branch_name in [b.name for b in repo.branches]:
            return {
                "status": "Failure",
                "error": f"Branch {branch_name} already exists",
                "message": f"Branch {branch_name} already exists in the repository"
            }
        
        # Create new branch
        new_branch = repo.create_head(branch_name)
        
        # Checkout if requested
        if checkout:
            new_branch.checkout()
        
        return {
            "status": "Success",
            "branch_name": branch_name,
            "checked_out": checkout,
            "current_branch": repo.active_branch.name,
            "message": f"Successfully created branch {branch_name}"
        }
    except git.exc.GitCommandError as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Failed to create branch: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Unexpected error: {str(e)}"
        }


def commit_changes(
    repo_path: str,
    commit_message: str,
    files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Commit changes in a repository.
    
    Args:
        repo_path: Path to the local repository
        commit_message: Commit message
        files: Optional list of specific files to commit (None = all changes)
        
    Returns:
        Dictionary with operation status and details
    """
    try:
        repo = git.Repo(repo_path)
        
        # Stage files
        if files:
            for file in files:
                repo.index.add([file])
        else:
            # Stage all changes
            repo.git.add(A=True)
        
        # Check if there are changes to commit
        if not repo.index.diff("HEAD") and not repo.untracked_files:
            return {
                "status": "Success",
                "message": "No changes to commit",
                "changes": False
            }
        
        # Commit changes
        commit = repo.index.commit(commit_message)
        
        # Get list of changed files
        changed_files = [item.a_path for item in commit.diff(commit.parents[0])] if commit.parents else []
        
        return {
            "status": "Success",
            "commit_hash": commit.hexsha,
            "commit_message": commit_message,
            "author": str(commit.author),
            "changed_files": changed_files,
            "changes": True,
            "message": f"Successfully committed changes: {commit.hexsha[:7]}"
        }
    except git.exc.GitCommandError as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Failed to commit changes: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Unexpected error: {str(e)}"
        }


def push_changes(
    repo_path: str,
    remote_name: str = "origin",
    branch_name: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Push changes to remote repository.
    
    Args:
        repo_path: Path to the local repository
        remote_name: Name of the remote (default: origin)
        branch_name: Branch to push (None = current branch)
        force: Whether to force push
        
    Returns:
        Dictionary with operation status and details
    """
    try:
        repo = git.Repo(repo_path)
        
        # Get branch to push
        if branch_name:
            if branch_name not in [b.name for b in repo.branches]:
                return {
                    "status": "Failure",
                    "error": f"Branch {branch_name} does not exist",
                    "message": f"Branch {branch_name} not found in repository"
                }
            branch = repo.branches[branch_name]
        else:
            branch = repo.active_branch
            branch_name = branch.name
        
        # Push to remote
        push_info = repo.remotes[remote_name].push(
            refspec=f"{branch_name}:{branch_name}",
            force=force
        )[0]
        
        # Construct the URL to the pushed branch
        remote_url = repo.remotes[remote_name].url
        if remote_url.endswith('.git'):
            remote_url = remote_url[:-4]
        
        # Convert SSH URL to HTTPS for web access
        if remote_url.startswith('git@'):
            remote_url = remote_url.replace('git@', 'https://').replace(':', '/')
        
        pushed_branch_url = f"{remote_url}/tree/{branch_name}"
        
        return {
            "status": "Success",
            "branch_name": branch_name,
            "remote_name": remote_name,
            "pushed_branch_url": pushed_branch_url,
            "summary": push_info.summary,
            "message": f"Successfully pushed {branch_name} to {remote_name}"
        }
    except git.exc.GitCommandError as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Failed to push changes: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Unexpected error: {str(e)}"
        }


def get_repository_info(repo_path: str) -> Dict[str, Any]:
    """
    Get information about a repository.
    
    Args:
        repo_path: Path to the local repository
        
    Returns:
        Dictionary with repository information
    """
    try:
        repo = git.Repo(repo_path)
        
        # Get remote URLs
        remotes = {}
        for remote in repo.remotes:
            remotes[remote.name] = remote.url
        
        # Get branch list
        branches = [b.name for b in repo.branches]
        
        # Get recent commits
        recent_commits = []
        for commit in list(repo.iter_commits(max_count=5)):
            recent_commits.append({
                "hash": commit.hexsha[:7],
                "author": str(commit.author),
                "message": commit.message.strip(),
                "date": commit.committed_datetime.isoformat()
            })
        
        return {
            "status": "Success",
            "current_branch": repo.active_branch.name,
            "branches": branches,
            "remotes": remotes,
            "is_dirty": repo.is_dirty(),
            "untracked_files": repo.untracked_files,
            "recent_commits": recent_commits
        }
    except Exception as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Failed to get repository info: {str(e)}"
        }
