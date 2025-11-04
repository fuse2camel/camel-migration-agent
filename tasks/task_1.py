from __future__ import annotations
import argparse, json, logging, sys, time, os
from typing import Dict, Any, List, TypedDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.env_validation import validate_environment
from langgraph.graph import StateGraph, END
from agents.coordinator_agent import coordinator
from agents.jdk_agent import jdk_agent
from agents.git_agent import git_agent
from agents.dependency_agent import dependency_agent
from agents.dsl_conversion_agent import dsl_conversion_agent
from agents.service_refactor_agent import service_refactor_agent
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
    g.add_node("coordinator",        _timed(coordinator,           "coordinator"))
    g.add_node("jdk_agent",         _timed(jdk_agent,            "jdk_agent"))
    g.add_node("git_agent",         _timed(git_agent,            "git_agent"))
    g.add_node("dependency_agent",  _timed(dependency_agent,     "dependency_agent"))
    g.add_node("dsl_conversion_agent", _timed(dsl_conversion_agent, "dsl_conversion_agent"))
    g.add_node("service_refactor_agent", _timed(service_refactor_agent, "service_refactor_agent"))
    g.add_node("reporter",          _timed(reporter,             "reporter"))
    
    g.set_entry_point("coordinator")
    g.add_edge("coordinator", "jdk_agent")
    g.add_edge("jdk_agent", "git_agent")
    g.add_edge("git_agent", "dependency_agent")
    g.add_edge("dependency_agent", "dsl_conversion_agent")
    g.add_edge("dsl_conversion_agent", "service_refactor_agent")
    
    def route_after_refactor(state: State): 
        # Check if there were any errors in the migration process
        if "error" in state:
            return "reporter"
        return "reporter"
    
    g.add_conditional_edges("service_refactor_agent", route_after_refactor, {"reporter": "reporter"})
    g.add_edge("reporter", END)
    return g.compile()
def parse_args(argv: list[str]):
    p = argparse.ArgumentParser(description="Phase 1–3 Orchestrator (LangGraph)")
    p.add_argument("--source-path", required=True)
    p.add_argument("--branch", default=DEFAULT_BRANCH_NAME)
    p.add_argument("--json", action="store_true")
    p.add_argument("--gui-port", type=int, help="Enable GUI updates by sending events to specified port (e.g., 8000)")
    return p.parse_args(argv)
def main(argv: list[str]) -> int:
    # Validate environment variables first
    print("🔍 Validating environment...")
    validate_environment()
    print("✅ Environment validation passed!\n")

    args = parse_args(argv); logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    # Enable GUI updates if port specified
    if args.gui_port:
        os.environ["EVENT_HTTP_ENDPOINT"] = f"http://127.0.0.1:{args.gui_port}/event"
        print(f"📡 GUI updates enabled on port {args.gui_port}")
        print(f"   Open http://127.0.0.1:{args.gui_port} to view dashboard\n")
    app = build_graph()
    init: State = {"source_path": args.source_path, "branch_name": args.branch, "tasks_completed": [], "artifacts": {}}
    final: State = app.invoke(init)
    summary = {"success": bool(final.get("ok")), "message": ("Phase 1–3 completed successfully" if final.get("ok") else final.get("error","Failed")), "tasks_completed": final.get("tasks_completed", []), "artifacts": final.get("artifacts", {})}
    print(json.dumps(summary, indent=2)); return 0 if summary["success"] else 1
if __name__ == "__main__":
    import sys; sys.exit(main(sys.argv[1:]))
