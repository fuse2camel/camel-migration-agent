from __future__ import annotations
import argparse, json, logging, sys, time, os
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from agents.coordinator_agent import coordinator
from agents.git_agent import git_agent
from tools.event_logger import logger
from config.settings import DEFAULT_BRANCH_NAME
class State(TypedDict, total=False):
    source_path: str
    branch_name: str
    tasks_completed: List[str]
    artifacts: Dict[str, Any]
    error: str
    ok: bool
def _timed(node_fn, phase_name):
    def _inner(state: State) -> State:
        t0 = time.time()
        logger.emit(phase=phase_name, status="start", message="starting", meta={"keys": list(state.keys())}, t_start=t0, t_end=None, duration_ms=None)
        # honor GUI demo setting (yellow hold)
        try:
            import json as _json
            _cfg_path = "./artifacts/gui_settings.json"
            _secs = 0
            if os.path.exists(_cfg_path):
                with open(_cfg_path) as _f:
                    _secs = float(_json.load(_f).get("demo_yellow_secs", 0))
            if _secs > 0: time.sleep(min(max(_secs, 0), 10))
        except Exception:
            pass
        out = node_fn(state); t1 = time.time()
        ok = "error" not in out or not out.get("error")
        logger.emit(phase=phase_name, status=("success" if ok else "error"), message=(out.get("error","completed")), meta={"artifacts": out.get("artifacts")}, t_start=t0, t_end=t1, duration_ms=int((t1-t0)*1000))
        return out
    return _inner
def reporter(state: State) -> State:
    ok = "error" not in state or not state.get("error"); return {"ok": ok}
def build_graph():
    g = StateGraph(State)
    g.add_node("coordinator", _timed(coordinator, "coordinator"))
    g.add_node("git_agent",  _timed(git_agent,  "git_agent"))
    g.add_node("reporter",   _timed(reporter,   "reporter"))
    g.set_entry_point("coordinator"); g.add_edge("coordinator", "git_agent")
    def route_after_git(state: State): return "reporter"
    g.add_conditional_edges("git_agent", route_after_git, {"reporter": "reporter"})
    g.add_edge("reporter", END); return g.compile()
def parse_args(argv: list[str]):
    p = argparse.ArgumentParser(description="Phase 1–3 Orchestrator (LangGraph)")
    p.add_argument("--source-path", required=True)
    p.add_argument("--branch", default=DEFAULT_BRANCH_NAME)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)
def main(argv: list[str]) -> int:
    args = parse_args(argv); logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    app = build_graph()
    init: State = {"source_path": args.source_path, "branch_name": args.branch, "tasks_completed": [], "artifacts": {}}
    final: State = app.invoke(init)
    summary = {"success": bool(final.get("ok")), "message": ("Phase 1–3 completed successfully" if final.get("ok") else final.get("error","Failed")), "tasks_completed": final.get("tasks_completed", []), "artifacts": final.get("artifacts", {})}
    print(json.dumps(summary, indent=2)); return 0 if summary["success"] else 1
if __name__ == "__main__":
    import sys; sys.exit(main(sys.argv[1:]))
