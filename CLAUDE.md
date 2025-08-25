# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

RouteForge is a multi-agent system for migrating Apache Camel 2 Spring Boot applications to Apache Camel 4. It uses CrewAI agents orchestrated by LangGraph workflows with a web-based GUI dashboard.

## Development Commands

### Environment Setup
```bash
# Create virtual environment and install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create .env file with required environment variables
# MODEL_API_KEY=your_api_key_here
# MODEL_NAME=gpt-4  # or qwen-plus-latest
# MODEL_BASE_URL=https://api.openai.com/v1  # or compatible endpoint
# MODEL_TEMPERATURE=0.7

# The system will validate these variables and throw clear errors if missing
```

### Running the System
```bash
# One-command run (GUI + migration workflow)
python -m tasks.run_coordinator --source-path /path/to/repo --branch feature/fuse2camel --port 8000

# Manual GUI server (separate terminal)
uvicorn gui.server:app --reload --port 8000

# Run migration workflow only
python -m tasks.task_1 --source-path /path/to/repo --branch feature/fuse2camel --json
```

### Testing
```bash
# Quick system verification
python tests/verify_system.py

# Test individual components
python tests/test_crewai_agents.py
python tests/test_end_to_end.py
python tests/test_full_migration.py

# Test specific agents
python main.py --test-agent config
python main.py --test-agent git --repo-url https://github.com/user/app.git
python main.py --test-agent dependency --workspace examples/
```

### Migration Commands
```bash
# Full migration with checkpointing
python main.py --repo https://github.com/user/camel-app.git --checkpoint

# Environment validation only
python main.py --validate-only

# Migration with custom settings
python main.py --repo <repo-url> --branch <branch-name> --workspace <local-path>
```

## Architecture Overview

### Multi-Agent System
- **CrewAI Agents**: 7 specialized agents handle different migration aspects (config_agent.py, git_agent.py, dependency_agent.py, dsl_conversion_agent.py, service_refactor_agent.py, test_agent.py, containerization_agent.py)
- **LangGraph Orchestration**: Workflow management with state tracking, conditional routing, and checkpointing (orchestration/langgraph_workflow.py)
- **Coordinator**: Simple state management for GUI integration (agents/coordinator_agent.py)

### Workflow Phases
1. **coordinator**: Initial setup and validation
2. **git_agent**: Repository cloning and branch management
3. **jdk_agent**: JDK 21 installation if needed
4. **rewrite_agent**: Code transformation (dependencies, DSL conversion, service refactoring)
5. **tests_agent**: Migration validation
6. **qa_agent**: Quality assurance
7. **commit_agent**: Git operations
8. **reporter**: Final report generation

### Key Components
- **Environment Validation**: Automatic validation of required environment variables (config/env_validation.py)
- **GUI Dashboard**: Real-time workflow visualization (gui/server.py, gui/web/index.html)
- **Tools Layer**: Utility functions for Git, Maven, Docker operations (tools/)
- **Configuration**: Environment-specific settings (config/)
- **Prompts**: Agent instructions in separate text files (prompts/)

### State Management
- Uses TypedDict for workflow state in LangGraph
- Event logging to artifacts/events.jsonl
- GUI settings persistence in artifacts/gui_settings.json
- Flow configuration in config/flow.json

### Migration Process
The system converts:
- XML routes to Java DSL
- Camel 2 processors to Camel 4 syntax
- Maven POM dependencies
- Generates Docker/Kubernetes artifacts

### Testing Strategy
- System verification (tests/verify_system.py)
- Individual agent testing via main.py --test-agent
- End-to-end workflow testing
- Uses sample Camel 2 application for validation

## Important File Patterns

- Agent implementations: `agents/*_agent.py`
- Tool utilities: `tools/*.py`
- Configuration files: `config/*.py`
- Test scripts: `tests/test_*.py` and `tests/verify_system.py`
- Prompt templates: `prompts/*.txt`
- Example files: `examples/Sample*`
- Orchestration: `orchestration/langgraph_workflow.py`
- Main entry points: `main.py`, `tasks/run_coordinator.py`

## Development Notes

- **Environment Validation**: System validates all required .env variables on startup
- **Import Fix**: git_agent function added to resolve LangGraph import issues  
- All agents create tasks without executing crews directly
- LangGraph handles workflow orchestration and state management
- Checkpointing enables resumable long-running migrations
- GUI provides interactive branch decision making
- JDK 21 installation handled automatically via Red Hat downloads
- Migration reports saved as PDF in source repository
- System requires OpenAI-compatible API endpoint for LLM operations
- Clear error messages for missing or invalid configuration