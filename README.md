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
3. **Knowledge Base**: Vector search with FAISS and HuggingFace embeddings for Red Hat Camel 4.10 migration guidance
4. GUI stays running until you stop it (Ctrl+C) - dashboard remains accessible after completion
5. Interactive branch decision via GUI if branch already exists: **create-new**, **override**, or **ignore**
6. Automatic PDF report saved in your source repo (`migration-report-<timestamp>.pdf`)
7. Flow diagram colors: **green** (done), **blinking yellow** (in progress), **light gray** (not started)

## Knowledge Base

The system includes a vector-based knowledge base for Red Hat Camel 4.10 migration guidance, providing contextual help to agents during migration.

### Key Features
- **HuggingFace Embeddings**: Uses `all-MiniLM-L6-v2` model for text embeddings
- **FAISS Vector Search**: Efficient similarity search for relevant documentation
- **Automatic Fallback**: Works even without PDF ingestion using built-in migration patterns
- **Non-blocking**: DSL conversion agent continues working even if knowledge base fails

### Ingesting Documentation (Manual Process)

Document ingestion is a **manual one-time setup**. The system works with fallback patterns if no documents are ingested.

```bash
# Place PDF files in knowledge/docs/ directory
mkdir -p knowledge/docs
# Copy your Red Hat Camel documentation PDFs here

# Run the ingestion script
python knowledge/ingest_docs.py

# Optional: specify different path or force re-ingestion
python knowledge/ingest_docs.py --docs-path /path/to/pdfs --force
```

The ingestion script will:
- Extract text from all PDFs in the specified directory
- Create embeddings using HuggingFace SentenceTransformer
- Build a FAISS index for fast similarity search
- Save the index to `knowledge/vector_db/`

**Note**: The DSL agent will automatically use the knowledge base if available, but will continue working with fallback patterns if no index exists.

### Querying the Knowledge Base
```python
from knowledge.camel_knowledge_base import get_knowledge_base

# Get knowledge base instance
kb = get_knowledge_base()

# Query for migration guidance
result = kb.query("How to convert XML DSL to Java DSL in Camel 4?")
print(result['response'])

# Get DSL conversion help
help_result = kb.get_dsl_conversion_help(
    xml_snippet='<route><from uri="file:input"/></route>',
    pattern_type="route"
)

# Get component migration info
component_info = kb.get_component_migration_info("http")
print(f"Migrate {component_info.get('known_mapping', {}).get('old')} to {component_info.get('known_mapping', {}).get('new')}")
```

### Built-in Fallback Patterns
Even without PDF ingestion, the knowledge base provides:
- XML to Java DSL conversion patterns
- Spring Boot 3 migration guidelines
- Component dependency mappings (http4→http, jetty9→jetty, etc.)
- Common error solutions
- Red Hat Camel 4.10 best practices

### Integration with DSL Agent
The DSL conversion agent automatically uses the knowledge base through three tools:
- `Query Camel Knowledge Base` - General migration queries
- `Get DSL Conversion Help` - DSL-specific guidance
- `Get Component Migration Info` - Component mapping information

If the knowledge base is unavailable, the agent continues with fallback patterns.

## Testing the Complete Flow

### Quick Test (Knowledge Base + DSL Agent)
```bash
# Test the full flow with knowledge base integration
python test_full_flow_with_kb.py
```

This test will:
1. ✅ Test knowledge base with fallback patterns (no PDFs needed)
2. ✅ Verify DSL agent integration with knowledge tools
3. ✅ Test workflow integration
4. ✅ Run sample migration with knowledge assistance

### Test with PDF Ingestion (Optional)
```bash
# Step 1: Ingest Red Hat Camel documentation
python knowledge/ingest_docs.py

# Step 2: Run the test to verify vector search works
python test_full_flow_with_kb.py

# You should see "Knowledge base ready with X vectors" in the output
```

### Full Migration Test
```bash
# Test with a real Camel 2 project
python -m tasks.run_coordinator \
    --source-path examples/SampleCamelApp \
    --branch feature/test-kb \
    --port 8000

# Or use your own project
python -m tasks.run_coordinator \
    --source-path /path/to/your/camel-project \
    --branch feature/fuse2camel \
    --port 8000
```

The migration will:
1. **Coordinator**: Validate environment and setup
2. **JDK Agent**: Ensure Java 21 is available
3. **Git Agent**: Create/manage migration branch
4. **Dependency Agent**: Update Maven dependencies to Red Hat Camel 4.10
5. **DSL Conversion Agent**: Convert XML to Java DSL **with knowledge base assistance**
   - Uses vector search if PDFs are ingested
   - Falls back to built-in patterns if not
6. **Service Refactor Agent**: Update Java code for Camel 4 APIs
7. **Reporter**: Generate migration report PDF

### Verify Knowledge Tools in Action
Watch for these messages during migration:
- `"Added 3 knowledge tools to DSL agent"` - Knowledge tools integrated
- `"Knowledge base ready with X vectors"` - Vector search active
- `"Using fallback patterns"` - Working without vector index

The DSL agent will query the knowledge base for:
- XML to Java DSL conversion patterns
- Component migration mappings (http4→http, etc.)
- Spring Boot 3 compatibility guidance

## Troubleshooting
- **Environment validation failed** → Create `.env` file with required variables: MODEL_API_KEY, MODEL_NAME, MODEL_BASE_URL, MODEL_TEMPERATURE
- **ModuleNotFoundError: 'agents'** → run with `python -m ...` from `project_root`, or `export PYTHONPATH=.`
- **ImportError: cannot import name 'git_agent'** → Fixed - ensure you have the latest version with the git_agent function
- **No events in GUI** → ensure the runner started the GUI and `EVENT_HTTP_ENDPOINT` is correct.
- **Knowledge base not available** → System works with fallback patterns. To enable vector search, place PDF docs in `knowledge/docs/` and run ingestion
- **Embeddings initialization failed** → Install sentence-transformers: `pip install sentence-transformers`
- **PDF extraction failed** → Install PyPDF2: `pip install PyPDF2`
- **Port in use** → use `--port 8080`.


## JDK 21 Automatic Installation
- **JDK Agent** automatically checks if Java 21+ is available on your system
- If not found, it downloads Eclipse Temurin JDK 21 from Adoptium.net (open source)
- **GUI Integration**: Set custom installation path via the dashboard (defaults to `./artifacts/jdk21/`)
- Supports **Linux**, **macOS**, and **Windows** with automatic OS/architecture detection
- Creates `./artifacts/activate_java.sh` script to set `JAVA_HOME` and update `PATH`
- **Usage**: `source artifacts/activate_java.sh` to activate the JDK in your current shell
