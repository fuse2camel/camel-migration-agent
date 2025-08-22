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
