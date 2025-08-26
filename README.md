# RouteForge (Multi-Agent Scaffold) — Phase 1–3 + GUI

Local, multi-agent scaffold using **LangGraph** with a dashboard to visualize phases, statuses, and durations.

## One-command run (starts GUI, runs Coordinator → Git Agent, keeps GUI alive)
```bash
cd project_root
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create .env file with required environment variables:
cat > .env << EOF
MODEL_API_KEY=your_api_key_here
MODEL_NAME=gpt-4
MODEL_BASE_URL=https://api.openai.com/v1
MODEL_TEMPERATURE=0.7
EOF

python -m tasks.run_coordinator --source-path /path/to/your/repo --branch feature/fuse2camel --port 8000
# Dashboard opens and stays up at http://127.0.0.1:8000/ (Ctrl+C to stop)
```

## Manual (separate terminals)
```bash
# Terminal 1
uvicorn gui.server:app --reload --port 8000

# Terminal 2
python -m tasks.task_1 --source-path /path/to/your/repo --branch feature/fuse2camel --json
```

## Diagram & demo settings
- Customize visible phases in **config/flow.json** (the GUI reads it via `/flow`).
- Adjust how long a phase stays **blinking yellow** using the dashboard control. This persists to `artifacts/gui_settings.json` and the runner honors it for each phase.

## Features
1. **Enhanced Flow Visualization**: Interactive flow diagram with phase descriptions and real-time status updates
2. **JDK Management**: Automatic JDK 21 detection and installation from Adoptium with GUI path selection
3. GUI stays running until you stop it (Ctrl+C) - dashboard remains accessible after completion
4. Interactive branch decision via GUI if branch already exists: **create-new**, **override**, or **ignore**
5. Automatic PDF report saved in your source repo (`migration-report-<timestamp>.pdf`)
6. Flow diagram colors: **green** (done), **blinking yellow** (in progress), **light gray** (not started)

## Troubleshooting
- **Environment validation failed** → Create `.env` file with required variables: MODEL_API_KEY, MODEL_NAME, MODEL_BASE_URL, MODEL_TEMPERATURE
- **ModuleNotFoundError: 'agents'** → run with `python -m ...` from `project_root`, or `export PYTHONPATH=.`
- **ImportError: cannot import name 'git_agent'** → Fixed - ensure you have the latest version with the git_agent function
- **No events in GUI** → ensure the runner started the GUI and `EVENT_HTTP_ENDPOINT` is correct.
- **Port in use** → use `--port 8080`.


## JDK 21 Automatic Installation
- **JDK Agent** automatically checks if Java 21+ is available on your system
- If not found, it downloads Eclipse Temurin JDK 21 from Adoptium.net (open source)
- **GUI Integration**: Set custom installation path via the dashboard (defaults to `./artifacts/jdk21/`)
- Supports **Linux**, **macOS**, and **Windows** with automatic OS/architecture detection
- Creates `./artifacts/activate_java.sh` script to set `JAVA_HOME` and update `PATH`
- **Usage**: `source artifacts/activate_java.sh` to activate the JDK in your current shell
