from __future__ import annotations
import argparse, json, os, sys, time, threading, webbrowser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.env_validation import validate_environment
def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Coordinator runner: start GUI then run Phase 1–3")
    p.add_argument("--source-path", required=True, help="Local path to the Git repository")
    p.add_argument("--branch", default=os.environ.get("DEFAULT_BRANCH_NAME", "feature/fuse2camel"),
                   help="Branch name to create/checkout")
    p.add_argument("--port", type=int, default=8000, help="GUI port (default: 8000)")
    p.add_argument("--no-browser", action="store_true", help="Do not open the dashboard in a browser")
    return p.parse_args(argv)
def _gui_is_up(port: int) -> bool:
    try:
        import requests
        r = requests.get(f"http://127.0.0.1:{port}/events", timeout=0.5)
        return r.status_code == 200
    except Exception:
        return False
def _start_gui_in_thread(port: int):
    import uvicorn
    from gui.server import app
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(60):
        if _gui_is_up(port):
            return
        time.sleep(0.1)
    raise RuntimeError("GUI server failed to start")
def main(argv: list[str]) -> int:
    # Validate environment variables first
    print("🔍 Validating environment...")
    validate_environment()
    print("✅ Environment validation passed!\n")
    
    args = parse_args(argv)
    os.environ["EVENT_HTTP_ENDPOINT"] = f"http://127.0.0.1:{args.port}/event"
    if not _gui_is_up(args.port):
        _start_gui_in_thread(args.port)
    if not args.no_browser:
        try: webbrowser.open(f"http://127.0.0.1:{args.port}/", new=2)
        except Exception: pass
    from tasks.task_1 import build_graph
    app = build_graph()
    init = {"source_path": args.source_path, "branch_name": args.branch, "tasks_completed": [], "artifacts": {}}
    final = app.invoke(init)
    from tools.report import generate_pdf_report
    events_path = "./artifacts/events.jsonl"
    pdf_path = os.path.join(init['source_path'], f"migration-report-{int(time.time())}.pdf")
    summary = {"success": bool(final.get("ok")), "message": ("Phase 1–3 completed successfully" if final.get("ok") else final.get("error", "Failed")), "tasks_completed": final.get("tasks_completed", []), "artifacts": final.get("artifacts", {})}
    try:
        generate_pdf_report(pdf_path, init['source_path'], summary, events_path)
        summary.setdefault('artifacts', {})['report_pdf'] = pdf_path
    except Exception as ex:
        summary.setdefault('artifacts', {})['report_error'] = str(ex)
    print(json.dumps(summary, indent=2))
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        pass
    return 0 if summary["success"] else 1
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
