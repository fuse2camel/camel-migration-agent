from __future__ import annotations
from typing import Dict, Any, List, TypedDict
class State(TypedDict, total=False):
    source_path: str
    branch_name: str
    tasks_completed: List[str]
    artifacts: Dict[str, Any]
    error: str
    ok: bool
def coordinator(state: State) -> State:
    src = state.get("source_path", "").strip()
    if not src: return {"error": "source_path is required"}
    tasks = list(state.get("tasks_completed", [])); tasks.append("Coordinator received source path")
    return {"tasks_completed": tasks}
