# System Architecture: Red Hat Camel Migration Agent

## Overview

The Red Hat Camel Migration Agent is a sophisticated multi-agent system designed to automate the migration of Fuse 6/7 applications to Red Hat build of Apache Camel 4.10 with Spring Boot 3.x compatibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GUI Dashboard (FastAPI)                  │
│  ┌─────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │   Flow Diagram   │  │  Live Events   │  │  JDK Config  │ │
│  └─────────────────┘  └────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                               │ SSE/REST API
┌─────────────────────────────────────────────────────────────┐
│                LangGraph Workflow Orchestration             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  coordinator → jdk_agent → git_agent → dependency_agent │ │
│  │     ↓              ↓             ↓              ↓      │ │
│  │  dsl_conversion → service_refactor → reporter          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    CrewAI Agents Layer                      │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │  JDK Agent   │ │  Git Agent   │ │  Dependency Agent  │  │
│  │              │ │              │ │                    │  │
│  │ • Download   │ │ • Branch mgmt│ │ • POM updates      │  │
│  │ • Install    │ │ • Conflict   │ │ • Red Hat BOM      │  │
│  │ • Validate   │ │   resolution │ │ • Repository URLs  │  │
│  └──────────────┘ └──────────────┘ └────────────────────┘  │
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │ DSL Convert  │ │Service Refact│ │     Reporter       │  │
│  │              │ │              │ │                    │  │
│  │ • XML→Java   │ │ • Exchange   │ │ • Migration report │  │
│  │ • @Component │ │   API update │ │ • Compliance check │  │
│  │ • Route DSL  │ │ • Import fix │ │ • Validation       │  │
│  └──────────────┘ └──────────────┘ └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                      Tools & Utilities                      │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │  Git Tools   │ │ Maven Tools  │ │    JDK Tools       │  │
│  │              │ │              │ │                    │  │
│  │ • Clone      │ │ • POM parse  │ │ • Download mgmt    │  │
│  │ • Branch     │ │ • Dependency │ │ • Installation     │  │
│  │ • Commit     │ │   update     │ │ • Validation       │  │
│  └──────────────┘ └──────────────┘ └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. GUI Dashboard (FastAPI + HTML/JS)

**Location**: `gui/server.py`, `gui/web/index.html`

**Features**:
- Real-time workflow visualization using Mermaid diagrams
- Server-Sent Events (SSE) for live updates
- Interactive JDK path configuration
- Branch conflict resolution prompts
- Event log streaming with detailed phase information

**Technical Stack**:
- FastAPI for REST API and SSE endpoints
- HTML5/JavaScript for frontend
- Mermaid.js for flow diagram rendering
- CORS middleware for cross-origin requests

**Key Endpoints**:
- `/events` - Historical event data
- `/sse` - Live event stream
- `/flow` - Workflow phase configuration
- `/create_prompt` - User interaction prompts
- `/decision/{id}` - User decision responses

### 2. LangGraph Workflow Orchestration

**Location**: `tasks/run_coordinator.py`, workflow state management

**Responsibilities**:
- Sequential agent execution with state passing
- Error handling and recovery
- Event logging to GUI dashboard
- Workflow timing and performance tracking

**State Management**:
```python
WorkflowState = TypedDict('WorkflowState', {
    'source_path': str,
    'branch_name': str,
    'tasks_completed': List[str],
    'artifacts': Dict[str, Any]
})
```

**Phase Sequence**:
1. Coordinator - Setup and validation
2. JDK Agent - Java 21 environment preparation
3. Git Agent - Repository and branch management
4. Dependency Agent - Maven POM migration
5. DSL Conversion Agent - XML to Java DSL transformation
6. Service Refactor Agent - Java code API updates
7. Reporter - Migration summary generation

### 3. CrewAI Agents

#### JDK Agent (`agents/jdk_agent.py`)
**Purpose**: Automatic JDK 21 management for Red Hat Camel 4.10

**Capabilities**:
- Cross-platform JDK detection (macOS, Linux, Windows)
- Automatic download from Eclipse Temurin (Adoptium)
- Archive extraction and installation validation
- Environment script generation (`./artifacts/activate_java.sh`)
- GUI integration for installation progress and path configuration

**Key Functions**:
- `download_jdk()` - Handles HTTP redirects and progress tracking
- `install_jdk()` - Cross-platform extraction and setup
- `validate_java()` - Version verification and JAVA_HOME setup

#### Git Agent (`agents/git_agent.py`)
**Purpose**: Repository management with enterprise workflow support

**Capabilities**:
- Local repository validation for Fuse 6/7 projects
- Branch creation with interactive conflict resolution
- GUI-based user prompts for branch decisions
- Repository status tracking and reporting
- Integration with Red Hat migration artifacts

**Interactive Features**:
- Branch conflict resolution: override/create-new/ignore options
- Real-time GUI prompts with timeout handling
- Automatic cleanup of resolved prompts

#### Dependency Agent (`agents/dependency_agent.py`)
**Purpose**: Maven POM migration to Red Hat Camel 4.10

**Migration Tasks**:
- Parent POM update to Red Hat Camel Spring Boot BOM
- Red Hat Maven repository configuration
- Legacy dependency mapping (http4→http, jetty9→jetty)
- Version property updates to Red Hat certified versions

**Key Transformations**:
```xml
<!-- Red Hat BOM Integration -->
<parent>
  <groupId>com.redhat.camel.springboot</groupId>
  <artifactId>camel-spring-boot-bom</artifactId>
  <version>4.10.0.redhat-00001</version>
</parent>

<!-- Red Hat Repository -->
<repository>
  <id>redhat-ga</id>
  <url>https://maven.repository.redhat.com/ga/</url>
</repository>
```

#### DSL Conversion Agent (`agents/dsl_conversion_agent.py`)
**Purpose**: XML Spring routes to Red Hat Camel 4.10 Java DSL

**Conversion Process**:
- XML route parsing and analysis
- Java DSL RouteBuilder class generation
- Spring Boot @Component annotation addition
- Enterprise pattern integration

**Transformation Examples**:
```java
@Component
public class MigrationRoutes extends RouteBuilder {
    @Override
    public void configure() throws Exception {
        from("timer:foo").to("log:bar");
    }
}
```

#### Service Refactor Agent (`agents/service_refactor_agent.py`)
**Purpose**: Java code updates for Red Hat Camel 4.10 APIs

**Refactoring Tasks**:
- Exchange API migration: `getIn()/getOut()` → `getMessage()`
- Import statement updates: `org.apache.camel.impl.*` → `org.apache.camel.support.*`
- Processor implementation updates for enterprise patterns
- @Component annotation addition for Spring Boot integration

### 4. Tools & Utilities Layer

#### Git Tools (`tools/git_tools.py`)
- Repository operations: clone, branch, commit, push
- Status checking and validation
- Branch management with conflict detection

#### Maven Tools (`tools/maven_tools.py`)
- POM file parsing and validation
- Dependency analysis and updates
- Red Hat BOM integration utilities

#### JDK Tools (integrated in `agents/jdk_agent.py`)
- Cross-platform download management
- Archive extraction utilities
- Installation validation and environment setup

## Data Flow

### 1. Initialization
```
User Input (source-path, branch) 
→ Environment Validation 
→ GUI Server Startup 
→ Workflow Initialization
```

### 2. Migration Execution
```
Coordinator Setup 
→ JDK Installation (if needed)
→ Git Branch Creation 
→ Maven POM Updates
→ XML to Java DSL Conversion 
→ Java Code Refactoring 
→ Report Generation
```

### 3. Real-time Updates
```
Agent Events 
→ LangGraph State Updates 
→ GUI Event Logging 
→ SSE Broadcast 
→ Dashboard Refresh
```

## Configuration Management

### Environment Variables (`.env`)
```bash
MODEL_API_KEY=your_openai_api_key
MODEL_NAME=gpt-4
MODEL_BASE_URL=https://api.openai.com/v1
MODEL_TEMPERATURE=0.7
DEFAULT_BRANCH_NAME=feature/fuse2camel
```

### Workflow Configuration (`config/flow.json`)
```json
{
  "phases": [
    "coordinator",
    "jdk_agent", 
    "git_agent",
    "dependency_agent",
    "dsl_conversion_agent",
    "service_refactor_agent",
    "reporter"
  ]
}
```

### Agent Prompts (`prompts/*.txt`)
Each agent has a dedicated prompt file containing:
- Role definition and responsibilities
- Red Hat Camel 4.10 specific instructions
- Enterprise pattern requirements
- Example transformations and best practices

## Error Handling & Recovery

### GUI Integration
- Real-time error display in dashboard
- User interaction prompts for conflict resolution
- Detailed error logging with context

### Agent-Level Recovery
- Individual agent error handling
- State preservation for workflow continuation
- Comprehensive error reporting to GUI

### System-Level Resilience
- Environment validation before execution
- Graceful degradation on component failures
- Clear error messages and resolution guidance

## Security Considerations

### Enterprise Compliance
- Red Hat certified component usage
- Security pattern integration
- Enterprise monitoring capabilities

### API Security
- Environment variable protection
- Secure API key handling
- CORS configuration for web dashboard

## Performance Optimization

### Parallel Operations
- Concurrent agent execution where possible
- Efficient file system operations
- Optimized GUI updates with SSE

### Resource Management
- Controlled JDK downloads with progress tracking
- Efficient memory usage in code transformations
- Minimal GUI resource consumption

## Extensibility

### Adding New Agents
1. Create agent class in `agents/`
2. Add prompt file in `prompts/`
3. Update workflow configuration
4. Register agent in LangGraph workflow

### GUI Enhancements
1. Add new endpoints to FastAPI server
2. Implement frontend features in HTML/JS
3. Integrate with existing SSE event system
4. Update flow diagram configuration

This architecture provides a robust, scalable foundation for enterprise-grade Fuse 6/7 to Red Hat Camel 4.10 migration operations.