from __future__ import annotations
from typing import Tuple
from git import Repo, InvalidGitRepositoryError, NoSuchPathError, GitCommandError
def ensure_branch(source_path: str, branch_name: str) -> Tuple[bool, str, dict]:
    try: repo = Repo(source_path)
    except InvalidGitRepositoryError: return False, "Provided path is not a Git repository. Initialize and commit at least once.", {}
    except NoSuchPathError: return False, f"No such path: {source_path}", {}
    try:
        if branch_name in [h.name for h in repo.heads]:
            repo.git.checkout(branch_name); action = "checked out existing"
        else:
            repo.git.checkout("-b", branch_name); action = "created"
        current_branch = repo.active_branch.name
    except GitCommandError as ge: return False, f"Git error creating/checking out branch: {ge}", {"branch": branch_name}
    except Exception as e: return False, f"Unexpected git error: {e}", {"branch": branch_name}
    return True, f"Successfully {action} branch {branch_name}.", {"branch": branch_name,"current_branch": current_branch,"source_path": source_path,"action": action}
