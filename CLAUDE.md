# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**Red Hat Camel Migration Agent** is a comprehensive multi-agent system for migrating Fuse 6/7 applications to Red Hat build of Apache Camel 4.10 with Spring Boot 3.x compatibility. It uses CrewAI agents orchestrated by LangGraph workflows with a real-time web-based GUI dashboard for enterprise-grade migration operations.

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
- **CrewAI Agents**: 8 specialized agents handle different migration aspects (config_agent.py, jdk_agent.py, git_agent.py, dependency_agent.py, dsl_conversion_agent.py, service_refactor_agent.py, test_agent.py, containerization_agent.py)
- **LangGraph Orchestration**: Workflow management with state tracking, conditional routing, and checkpointing (orchestration/langgraph_workflow.py)
- **Coordinator**: Simple state management for GUI integration (agents/coordinator_agent.py)

### Migration Workflow Phases (Red Hat Camel 4.10)
1. **coordinator**: Initial setup and validation for Red Hat enterprise migration
2. **jdk_agent**: JDK 21 detection and automatic installation from Adoptium with GUI integration
3. **git_agent**: Repository validation and branch management with conflict resolution
4. **dependency_agent**: Maven POM migration to Red Hat Camel 4.10 BOM and dependencies
5. **dsl_conversion_agent**: XML Spring routes to Red Hat Camel 4.10 Java DSL conversion
6. **service_refactor_agent**: Java code refactoring for Red Hat Camel 4.10 APIs (Exchange, Processor)
7. **reporter**: Migration report generation with Red Hat enterprise compliance

### Key Components
- **Environment Validation**: Automatic validation of required environment variables (config/env_validation.py)
- **JDK Management**: Automatic JDK 21 detection and installation from Adoptium (agents/jdk_agent.py)
- **GUI Dashboard**: Real-time workflow visualization with JDK path selection (gui/server.py, gui/web/index.html)
- **Tools Layer**: Utility functions for Git, Maven, Docker operations (tools/)
- **Configuration**: Environment-specific settings (config/)
- **Prompts**: Agent instructions in separate text files (prompts/)

### State Management
- Uses TypedDict for workflow state in LangGraph
- Event logging to artifacts/events.jsonl
- GUI settings persistence in artifacts/gui_settings.json
- Flow configuration in config/flow.json

### Red Hat Camel 4.10 Migration Process
The system provides enterprise-grade migration from Fuse 6/7 to Red Hat build of Apache Camel 4.10:

**Maven Dependencies:**
- Updates parent POM to Red Hat Camel Spring Boot BOM (com.redhat.camel.springboot:camel-spring-boot-bom:4.10.0.redhat-00001)
- Adds Red Hat Maven repositories (https://maven.repository.redhat.com/ga/)
- Maps legacy dependencies: camel-http4→camel-http, camel-jetty9→camel-jetty, camel-rabbitmq→camel-spring-rabbitmq

**Code Transformation:**
- XML Spring routes to Red Hat Camel 4.10 Java DSL with @Component annotations
- Exchange API migration: getIn()/getOut() → getMessage() for Red Hat enterprise patterns
- Processor implementations updated for Red Hat Camel 4.10 compatibility
- Import updates: org.apache.camel.impl.* → org.apache.camel.support.*

**Enterprise Features:**
- Spring Boot 3.x integration with Red Hat certified components
- Enterprise security and monitoring pattern application
- Red Hat support compliance and documentation
- GUI-based workflow monitoring with real-time updates

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
- **JDK Management**: Automatic JDK 21 detection/installation from Adoptium with GUI path selection
- **Import Fix**: git_agent function added to resolve LangGraph import issues  
- **Enhanced GUI**: Flow diagram with phase descriptions and real-time status updates
- All agents create tasks without executing crews directly
- LangGraph handles workflow orchestration and state management
- Checkpointing enables resumable long-running migrations
- GUI provides interactive branch decision making and JDK installation path setting
- JDK 21 installation handled automatically from Eclipse Temurin (Adoptium)
- Migration reports saved as PDF in source repository
- System requires OpenAI-compatible API endpoint for LLM operations
- Clear error messages for missing or invalid configuration
- Dashboard remains accessible after workflow completion