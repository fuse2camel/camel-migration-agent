"""
Git Agent - Manages source code repository operations
Refactored to separate agent and task creation from crew execution
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from crewai import Agent, Task
from crewai.tools import tool
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.git_tools import (
    clone_repository,
    create_branch,
    commit_changes,
    push_changes,
    get_repository_info
)
from config.llm_config import get_llm


class GitAgent:
    """
    Agent responsible for Git repository management
    Only creates agents and tasks, does not execute crews
    """

    def __init__(self):
        """Initialize the Git Agent with LLM and tools"""
        self.llm = get_llm()
        self.agent = self._create_agent()
        self.workspace_path = None

    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompts',
            'git_agent_prompt.txt'
        )

        with open(prompt_path, 'r') as f:
            system_prompt = f.read()

        return Agent(
            role='Source Code Manager',
            goal='Handle Git repository operations for the migration workflow',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                self.clone_repo_tool,
                self.create_branch_tool,
                self.commit_changes_tool,
                self.push_changes_tool,
                self.get_repo_info_tool
            ]
        )

    @tool("Clone Repository")
    def clone_repo_tool(self, repo_url: str, target_path: str, branch: str = None) -> str:
        """
        Clone a Git repository.

        Args:
            repo_url: URL of the repository
            target_path: Local path to clone to
            branch: Optional branch to checkout

        Returns:
            JSON string with operation result
        """
        result = clone_repository(repo_url, target_path, branch)
        return json.dumps(result, indent=2)

    @tool("Create Branch")
    def create_branch_tool(self, repo_path: str, branch_name: str) -> str:
        """
        Create a new branch in the repository.

        Args:
            repo_path: Path to the repository
            branch_name: Name of the new branch

        Returns:
            JSON string with operation result
        """
        result = create_branch(repo_path, branch_name, checkout=True)
        return json.dumps(result, indent=2)

    @tool("Commit Changes")
    def commit_changes_tool(self, repo_path: str, commit_message: str) -> str:
        """
        Commit all changes in the repository.

        Args:
            repo_path: Path to the repository
            commit_message: Commit message

        Returns:
            JSON string with operation result
        """
        result = commit_changes(repo_path, commit_message)
        return json.dumps(result, indent=2)

    @tool("Push Changes")
    def push_changes_tool(self, repo_path: str, branch_name: str = None) -> str:
        """
        Push changes to the remote repository.

        Args:
            repo_path: Path to the repository
            branch_name: Optional branch name to push

        Returns:
            JSON string with operation result
        """
        result = push_changes(repo_path, branch_name=branch_name)
        return json.dumps(result, indent=2)

    @tool("Get Repository Info")
    def get_repo_info_tool(self, repo_path: str) -> str:
        """
        Get information about a repository.

        Args:
            repo_path: Path to the repository

        Returns:
            JSON string with repository information
        """
        result = get_repository_info(repo_path)
        return json.dumps(result, indent=2)

    def create_initiate_task(
        self,
        repository_url: str,
        branch_name: str = "feature/camel4-migration",
        workspace_dir: str = "/tmp/camel-migration"
    ) -> Task:
        """
        Create task for initiating the migration workflow.

        Args:
            repository_url: URL of the repository to migrate
            branch_name: Name for the migration branch
            workspace_dir: Directory to clone the repository to

        Returns:
            CrewAI Task for workflow initiation
        """
        # Store workspace path for later use
        self.workspace_path = workspace_dir
        
        return Task(
            description=f"""
            Initiate the migration workflow:
            1. Clone the repository from: {repository_url}
            2. Clone it to: {workspace_dir}
            3. Create a new branch named: {branch_name}
            4. Get and report the repository information

            Ensure all operations complete successfully.
            """,
            expected_output="A report with the cloned repository path and branch information",
            agent=self.agent
        )

    def create_finalize_task(
        self,
        source_code_path: str,
        commit_message: str = "Migrate from Apache Camel 2 to Camel 4",
        branch_name: Optional[str] = None
    ) -> Task:
        """
        Create task for finalizing the migration workflow.

        Args:
            source_code_path: Path to the repository with changes
            commit_message: Message for the migration commit
            branch_name: Optional branch name to push

        Returns:
            CrewAI Task for workflow finalization
        """
        return Task(
            description=f"""
            Finalize the migration workflow:
            1. Stage all changes in the repository at: {source_code_path}
            2. Commit changes with message: "{commit_message}"
            3. Push the changes to the remote repository
            4. Report the pushed branch URL

            Ensure all modified files are committed and pushed.
            """,
            expected_output="A report with commit details and pushed branch URL",
            agent=self.agent
        )

    def get_repository_status(self, repo_path: str) -> Dict[str, Any]:
        """
        Get the current status of the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary with repository status information
        """
        try:
            return get_repository_info(repo_path)
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


def git_agent(state):
    """
    Git agent function for LangGraph workflow compatibility.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with git operations completed
    """
    from typing import Dict, Any, List
    
    source_path = state.get("source_path", "").strip()
    branch_name = state.get("branch_name", "feature/fuse2camel")
    
    if not source_path:
        return {"error": "source_path is required for git operations"}
    
    try:
        # Initialize git agent
        agent = GitAgent()
        
        # Check if source path exists and is a git repository
        if not os.path.exists(source_path):
            return {"error": f"Source path does not exist: {source_path}"}
        
        if not os.path.exists(os.path.join(source_path, ".git")):
            return {"error": f"Source path is not a git repository: {source_path}"}
        
        # Get repository status
        repo_status = agent.get_repository_status(source_path)
        
        # Handle branch creation/switching with conflict resolution
        from tools.git_tools import create_branch
        import requests
        import uuid
        
        branch_result = create_branch(source_path, branch_name)
        branch_action_taken = ""
        
        # If branch already exists, prompt user via GUI
        if branch_result.get("status") == "Failure" and "already exists" in branch_result.get("error", ""):
            try:
                # Create prompt for user decision
                prompt_id = str(uuid.uuid4())
                prompt_payload = {
                    "id": prompt_id,
                    "title": "Branch Conflict Resolution",
                    "text": f"Branch '{branch_name}' already exists in the repository. What would you like to do?",
                    "options": ["override", "create-new", "ignore"],
                    "default": "override",
                    "payload": {"branch": branch_name, "repo_path": source_path}
                }
                
                # Send prompt to GUI
                response = requests.post("http://127.0.0.1:8000/create_prompt", json=prompt_payload)
                if response.status_code == 200:
                    # Wait for user decision (with timeout)
                    import time
                    max_wait = 300  # 5 minutes timeout
                    wait_time = 0
                    
                    while wait_time < max_wait:
                        decision_response = requests.get(f"http://127.0.0.1:8000/decision/{prompt_id}")
                        if decision_response.status_code == 200:
                            decision_data = decision_response.json()
                            if decision_data.get("status") == "resolved":
                                choice = decision_data.get("choice", "override")
                                
                                if choice == "create-new":
                                    new_branch_name = decision_data.get("new_branch_name", f"{branch_name}-new")
                                    branch_result = create_branch(source_path, new_branch_name)
                                    branch_name = new_branch_name
                                    branch_action_taken = f"Created new branch: {new_branch_name}"
                                    branch_result = {"status": "Success", "message": branch_action_taken}
                                elif choice == "override":
                                    # Force switch to existing branch
                                    from tools.git_tools import switch_branch
                                    switch_result = switch_branch(source_path, branch_name)
                                    branch_result = {"status": "Success", "message": f"Switched to existing branch: {branch_name}"}
                                    branch_action_taken = f"Switched to existing branch: {branch_name}"
                                else:  # ignore
                                    from tools.git_tools import switch_branch
                                    switch_result = switch_branch(source_path, branch_name)
                                    branch_result = {"status": "Success", "message": f"Using existing branch: {branch_name}"}
                                    branch_action_taken = f"Using existing branch: {branch_name} (ignored conflict)"
                                
                                # Clean up the prompt after decision
                                try:
                                    requests.delete(f"http://127.0.0.1:8000/prompt/{prompt_id}")
                                except:
                                    pass
                                break
                        
                        time.sleep(2)
                        wait_time += 2
                    
                    if wait_time >= max_wait:
                        # Default to override if no response
                        from tools.git_tools import switch_branch
                        switch_result = switch_branch(source_path, branch_name)
                        branch_result = {"status": "Success", "message": f"Switched to existing branch: {branch_name} (timeout default)"}
                        branch_action_taken = f"Switched to existing branch: {branch_name} (timeout default)"
                        
            except Exception as gui_error:
                print(f"GUI prompt failed: {gui_error}")
                # Fallback to switching to existing branch
                from tools.git_tools import switch_branch
                switch_result = switch_branch(source_path, branch_name)
                branch_result = {"status": "Success", "message": f"Switched to existing branch: {branch_name} (GUI fallback)"}
                branch_action_taken = f"Switched to existing branch: {branch_name} (GUI fallback)"
        
        tasks_completed = list(state.get("tasks_completed", []))
        tasks_completed.extend([
            "Git agent initialized",
            f"Repository validated at: {source_path}",
            f"Branch '{branch_name}' ready for migration",
            branch_action_taken if branch_action_taken else "Branch operation completed"
        ])
        
        artifacts = dict(state.get("artifacts", {}))
        artifacts.update({
            "git_repo_path": source_path,
            "migration_branch": branch_name,
            "repository_status": repo_status,
            "branch_creation": branch_result,
            "branch_action": branch_action_taken
        })
        
        return {
            "tasks_completed": tasks_completed,
            "artifacts": artifacts
        }
        
    except Exception as e:
        return {"error": f"Git agent failed: {str(e)}"}