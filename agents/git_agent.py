
"""
Git Agent - Manages source code repository operations
"""

# import json
# import os
# import sys
# from typing import Dict, Any, Optional
# from crewai import Agent, Task, Crew
# from crewai_tools import tool
# from pathlib import Path
#
# # Add parent directory to path for imports
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#
# from tools.git_tools import (
#     clone_repository,
#     create_branch,
#     commit_changes,
#     push_changes,
#     get_repository_info
# )
# from config.llm_config import get_llm
#
#
# class GitAgent:
#     """
#     Agent responsible for Git repository management
#     """
#
#     def __init__(self):
#         """Initialize the Git Agent with LLM and tools"""
#         self.llm = get_llm()
#         self.agent = self._create_agent()
#         self.workspace_path = None
#
#     def _create_agent(self) -> Agent:
#         """Create the CrewAI agent"""
#         # Load system prompt
#         prompt_path = os.path.join(
#             os.path.dirname(os.path.dirname(__file__)),
#             'prompts',
#             'git_agent_prompt.txt'
#         )
#
#         with open(prompt_path, 'r') as f:
#             system_prompt = f.read()
#
#         return Agent(
#             role='Source Code Manager',
#             goal='Handle Git repository operations for the migration workflow',
#             backstory=system_prompt,
#             verbose=True,
#             allow_delegation=False,
#             llm=self.llm,
#             tools=[
#                 self.clone_repo_tool,
#                 self.create_branch_tool,
#                 self.commit_changes_tool,
#                 self.push_changes_tool,
#                 self.get_repo_info_tool
#             ]
#         )
#
#     @tool("Clone Repository")
#     def clone_repo_tool(self, repo_url: str, target_path: str, branch: str = None) -> str:
#         """
#         Clone a Git repository.
#
#         Args:
#             repo_url: URL of the repository
#             target_path: Local path to clone to
#             branch: Optional branch to checkout
#
#         Returns:
#             JSON string with operation result
#         """
#         result = clone_repository(repo_url, target_path, branch)
#         return json.dumps(result, indent=2)
#
#     @tool("Create Branch")
#     def create_branch_tool(self, repo_path: str, branch_name: str) -> str:
#         """
#         Create a new branch in the repository.
#
#         Args:
#             repo_path: Path to the repository
#             branch_name: Name of the new branch
#
#         Returns:
#             JSON string with operation result
#         """
#         result = create_branch(repo_path, branch_name, checkout=True)
#         return json.dumps(result, indent=2)
#
#     @tool("Commit Changes")
#     def commit_changes_tool(self, repo_path: str, commit_message: str) -> str:
#         """
#         Commit all changes in the repository.
#
#         Args:
#             repo_path: Path to the repository
#             commit_message: Commit message
#
#         Returns:
#             JSON string with operation result
#         """
#         result = commit_changes(repo_path, commit_message)
#         return json.dumps(result, indent=2)
#
#     @tool("Push Changes")
#     def push_changes_tool(self, repo_path: str, branch_name: str = None) -> str:
#         """
#         Push changes to the remote repository.
#
#         Args:
#             repo_path: Path to the repository
#             branch_name: Optional branch name to push
#
#         Returns:
#             JSON string with operation result
#         """
#         result = push_changes(repo_path, branch_name=branch_name)
#         return json.dumps(result, indent=2)
#
#     @tool("Get Repository Info")
#     def get_repo_info_tool(self, repo_path: str) -> str:
#         """
#         Get information about a repository.
#
#         Args:
#             repo_path: Path to the repository
#
#         Returns:
#             JSON string with repository information
#         """
#         result = get_repository_info(repo_path)
#         return json.dumps(result, indent=2)
#
#     def initiate_workflow(
#         self,
#         repository_url: str,
#         branch_name: str = "feature/camel4-migration",
#         workspace_dir: str = "/tmp/camel-migration"
#     ) -> Dict[str, Any]:
#         """
#         Initiate the migration workflow by cloning and preparing the repository.
#
#         Args:
#             repository_url: URL of the repository to migrate
#             branch_name: Name for the migration branch
#             workspace_dir: Directory to clone the repository to
#
#         Returns:
#             Dictionary with operation results
#         """
#         # Create task for initiating workflow
#         initiate_task = Task(
#             description=f"""
#             Initiate the migration workflow:
#             1. Clone the repository from: {repository_url}
#             2. Clone it to: {workspace_dir}
#             3. Create a new branch named: {branch_name}
#             4. Get and report the repository information
#
#             Ensure all operations complete successfully.
#             """,
#             expected_output="A report with the cloned repository path and branch information",
#             agent=self.agent
#         )
#
#         # Create crew and execute
#         crew = Crew(
#             agents=[self.agent],
#             tasks=[initiate_task],
#             verbose=True
#         )
#
#         try:
#             # Execute the workflow
#             result = crew.kickoff()
#
#             # Store workspace path for later use
#             self.workspace_path = workspace_dir
#
#             # Get actual repository info
#             repo_info = get_repository_info(workspace_dir)
#
#             return {
#                 "status": "Success",
#                 "workflow_stage": "initiate",
#                 "local_path": workspace_dir,
#                 "repository_url": repository_url,
#                 "branch_name": branch_name,
#                 "repository_info": repo_info,
#                 "message": f"Successfully initiated workflow with repository cloned to {workspace_dir}"
#             }
#
#         except Exception as e:
#             return {
#                 "status": "Failure",
#                 "workflow_stage": "initiate",
#                 "error": str(e),
#                 "message": f"Failed to initiate workflow: {str(e)}"
#             }
#
#     def finalize_workflow(
#         self,
#         source_code_path: str,
#         commit_message: str = "Migrate from Apache Camel 2 to Camel 4",
#         branch_name: Optional[str] = None
#     ) -> Dict[str, Any]:
#         """
#         Finalize the migration workflow by committing and pushing changes.
#
#         Args:
#             source_code_path: Path to the repository with changes
#             commit_message: Message for the migration commit
#             branch_name: Optional branch name to push
#
#         Returns:
#             Dictionary with operation results
#         """
#         # Create task for finalizing workflow
#         finalize_task = Task(
#             description=f"""
#             Finalize the migration workflow:
#             1. Stage all changes in the repository at: {source_code_path}
#             2. Commit changes with message: "{commit_message}"
#             3. Push the changes to the remote repository
#             4. Report the pushed branch URL
#
#             Ensure all modified files are committed and pushed.
#             """,
#             expected_output="A report with commit details and pushed branch URL",
#             agent=self.agent
#         )
#
#         # Create crew and execute
#         crew = Crew(
#             agents=[self.agent],
#             tasks=[finalize_task],
#             verbose=True
#         )
#
#         try:
#             # Execute the workflow
#             result = crew.kickoff()
#
#             # Get actual commit and push results
#             commit_result = commit_changes(source_code_path, commit_message)
#             push_result = push_changes(source_code_path, branch_name=branch_name)
#
#             return {
#                 "status": "Success",
#                 "workflow_stage": "finalize",
#                 "commit_result": commit_result,
#                 "push_result": push_result,
#                 "pushed_branch_url": push_result.get("pushed_branch_url", ""),
#                 "message": f"Successfully finalized workflow with changes pushed to remote"
#             }
#
#         except Exception as e:
#             return {
#                 "status": "Failure",
#                 "workflow_stage": "finalize",
#                 "error": str(e),
#                 "message": f"Failed to finalize workflow: {str(e)}"
#             }

from __future__ import annotations
from typing import Dict, Any, List, TypedDict
import os, time
from tools.git_utils import ensure_branch
from tools.interactive import InteractiveClient
from tools import jdk_utils
from git import Repo
class State(TypedDict, total=False):
    source_path: str
    branch_name: str
    tasks_completed: List[str]
    artifacts: Dict[str, Any]
    error: str
    ok: bool
def git_agent(state: State) -> State:
    source_path = state.get("source_path", ""); branch_name = state.get("branch_name", "feature/fuse2camel")
    if not os.path.exists(source_path): return {"error": f"Path does not exist: {source_path}"}
    repo = Repo(source_path)
    existing = branch_name in [h.name for h in repo.heads]
    if existing:
        ic = InteractiveClient()
        choice, new_name = ic.choose_branch_action(source_path, branch_name)
        if choice == "create-new":
            branch_name = new_name or (branch_name + "-new")
        elif choice == "override":
            pass
        elif choice == "ignore":
            branch_name = repo.active_branch.name
    ok, msg, data = ensure_branch(source_path, branch_name)
    if not ok: return {"error": msg}
    tasks = list(state.get("tasks_completed", [])); tasks.append("Git agent created/checked out feature branch")
    artifacts = dict(state.get("artifacts", {})); artifacts.update(data)

    # --- Ensure JDK 21 present ---
    found, major, raw = jdk_utils.detect_java_version()
    if not found or (major or 0) < 21:
        ic = InteractiveClient()
        decision = ic.choose_jdk_install(source_path)
        choice = decision.get("choice","skip")
        text = decision.get("text_input",""
        )
        if choice in ("provide-redhat-url","provide-local-archive") and not text:
            return {"error": "JDK 21 required but no URL/path provided."}
        try:
            if choice == "provide-redhat-url":
                java_home = jdk_utils.install_jdk_from_url(text, install_root="./artifacts/jdk21")
            elif choice == "provide-local-archive":
                java_home = jdk_utils.install_jdk_from_local(text, install_root="./artifacts/jdk21")
            else:
                java_home = None
        except Exception as ex:
            return {"error": f"Failed to obtain JDK 21: {ex}"}
        if java_home:
            act = jdk_utils.write_env_activation(java_home)
            ver_txt = jdk_utils.java_bin_version(java_home)
            artifacts.update({"java": {"java_home": java_home, "activation_script": act, "java_version": ver_txt}})
            tasks.append("Ensured JDK 21 (installed/activated script written)")
        else:
            tasks.append("Skipped JDK 21 install per user choice")
    else:
        tasks.append("JDK 21+ already present")
        artifacts.update({"java": {"system_java": True, "detected": raw}})

    return {"tasks_completed": tasks, "artifacts": artifacts}
