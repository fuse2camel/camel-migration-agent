# Camel Migration Agent - Comprehensive Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Agents Description](#agents-description)
7. [Workflow Stages](#workflow-stages)
8. [Examples](#examples)
9. [Troubleshooting](#troubleshooting)
10. [Development Process](#development-process)

## Overview

The Camel Migration Agent is an AI-powered multi-agent system designed to automate the migration of Apache Camel 2 Spring Boot applications to Apache Camel 4. It uses CrewAI for agent implementation and LangGraph for orchestration, providing a complete end-to-end migration solution.

### Key Features
- **Automated Migration**: Fully automated conversion from Camel 2 to Camel 4
- **Multi-Agent Architecture**: Specialized agents for each migration aspect
- **Intelligent Workflow**: LangGraph-based orchestration with error handling
- **Docker-Ready**: Generates optimized Docker configurations
- **Few-Shot Learning**: Uses examples to improve conversion accuracy
- **Comprehensive Testing**: Validates migration at each stage

## Architecture

### System Components

```
┌─────────────────────────────────────────┐
│         Orchestration Layer              │
│         (LangGraph Workflow)             │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│           Agent Layer (CrewAI)           │
├──────────────┬──────────────────────────┤
│ Config Agent │ Git Agent                 │
│ Dependency   │ DSL Conversion            │
│ Service      │ Test Agent                │
│ Container    │                           │
└──────────────┴──────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│           Tool Layer                     │
│  (System, Git, Maven, Code, Docker)      │
└─────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Each agent handles a specific migration aspect
2. **Tool-Agent Separation**: Tools perform actions, agents make decisions
3. **State Management**: Orchestrator maintains workflow state
4. **Error Recovery**: Graceful handling of failures with retry logic
5. **Platform Agnostic**: Containerized for cross-platform compatibility

## Installation

### Prerequisites

1. **System Requirements**:
   - Python 3.9+
   - Java 17+ (for target application)
   - Maven 3.8.0+
   - Git
   - Docker or Podman (optional, for containerization)

2. **Clone the Repository**:
```bash
git clone https://github.com/your-org/camel-migration-agent.git
cd camel-migration-agent
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

## Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# LLM Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_API_BASE=https://api.openai.com/v1

# Agent Settings
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=4000

# Workflow Settings
DEFAULT_JAVA_VERSION=17
DEFAULT_BRANCH_NAME=feature/camel4-migration
WORKSPACE_DIR=/tmp/camel-migration
```

### LLM Configuration

The system uses the configuration in `config/llm_config.py`:

```python
def get_llm():
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
        api_key=os.getenv("OPENAI_API_KEY")
    )
```

## Usage

### Basic Migration

```bash
# Migrate a repository
python main.py --repo https://github.com/user/camel-app.git

# With custom settings
python main.py \
  --repo https://github.com/user/camel-app.git \
  --branch my-migration-branch \
  --workspace /path/to/workspace \
  --java 17
```

### Testing Individual Agents

```bash
# Test configuration validation
python main.py --test-agent config

# Test dependency analysis
python main.py --test-agent dependency --workspace /path/to/project

# Test route conversion
python main.py --test-agent dsl --workspace /path/to/project
```

### Example: Migrating Sample Fuse 6 Application

```bash
python main.py --repo https://github.com/fuse2camel/sample-fuse6-app.git
```

## Agents Description

### 1. Config Agent
**Purpose**: Validates the local system environment

**Responsibilities**:
- Check Java installation (version 17+)
- Verify Maven availability (3.8.0+)
- Confirm Git installation
- Validate container engine (Docker/Podman)

**Output**: Validation report with pass/fail status

### 2. Git Agent
**Purpose**: Manages source code repository operations

**Responsibilities**:
- Clone repository
- Create migration branch
- Commit changes
- Push to remote

**Output**: Repository status and branch URLs

### 3. Dependency Agent
**Purpose**: Updates Maven dependencies

**Key Conversions**:
- `camel-core` → `camel-core-model`, `camel-core-engine`
- `camel-http4` → `camel-http`
- `camel-swagger-java` → `camel-openapi-java`
- Spring Boot 2.x → 3.x

**Output**: Updated pom.xml with migration report

### 4. DSL Conversion Agent
**Purpose**: Converts routes to Camel 4 Java DSL

**Conversions**:
```xml
<!-- Camel 2 XML -->
<route>
  <from uri="timer:foo"/>
  <to uri="log:bar"/>
</route>
```

```java
// Camel 4 Java DSL
from("timer:foo")
  .to("log:bar");
```

**Output**: Java RouteBuilder classes

### 5. Service Refactor Agent
**Purpose**: Updates Java business logic

**Key Changes**:
- `exchange.getIn()` → `exchange.getMessage()`
- `exchange.getOut()` → `exchange.getMessage()`
- Update deprecated APIs
- Fix import statements

**Output**: Refactored Java files

### 6. Test Agent
**Purpose**: Validates the migration

**Tests**:
- Compilation check
- Unit test execution
- Smoke test
- Log analysis

**Output**: Validation report

### 7. Containerization Agent
**Purpose**: Prepares for Docker deployment

**Generates**:
- Optimized Dockerfile
- .dockerignore file
- Docker deployment guide
- Docker Compose example

**Output**: Docker configuration files

## Workflow Stages

The migration follows these sequential stages:

1. **Configuration Validation**
   - Verify environment prerequisites
   - Check tool versions

2. **Repository Cloning**
   - Clone source repository
   - Create migration branch

3. **Dependency Update**
   - Analyze current dependencies
   - Update to Camel 4 versions
   - Remove deprecated dependencies

4. **Route Conversion**
   - Find XML route files
   - Convert to Java DSL
   - Create RouteBuilder classes

5. **Service Refactoring**
   - Update Processor implementations
   - Fix Exchange API usage
   - Update imports

6. **Testing**
   - Compile project
   - Run tests
   - Perform smoke test

7. **Containerization** (Optional)
   - Generate Dockerfile
   - Create Docker configuration

8. **Push Changes**
   - Commit all changes
   - Push to remote branch

## Examples

### Example 1: XML to Java DSL Conversion

**Input (Camel 2 XML)**:
```xml
<route id="order-route">
  <from uri="jms:queue:orders"/>
  <choice>
    <when>
      <simple>${header.priority} == 'HIGH'</simple>
      <to uri="direct:express"/>
    </when>
    <otherwise>
      <to uri="direct:normal"/>
    </otherwise>
  </choice>
</route>
```

**Output (Camel 4 Java DSL)**:
```java
from("jms:queue:orders")
  .routeId("order-route")
  .choice()
    .when(simple("${header.priority} == 'HIGH'"))
      .to("direct:express")
    .otherwise()
      .to("direct:normal")
  .end();
```

### Example 2: Processor Migration

**Camel 2 Processor**:
```java
public void process(Exchange exchange) {
    String body = exchange.getIn().getBody(String.class);
    exchange.getOut().setBody(body.toUpperCase());
}
```

**Camel 4 Processor**:
```java
public void process(Exchange exchange) {
    String body = exchange.getMessage().getBody(String.class);
    exchange.getMessage().setBody(body.toUpperCase());
}
```

### Example 3: POM Dependency Update

**Before (Camel 2)**:
```xml
<dependency>
    <groupId>org.apache.camel</groupId>
    <artifactId>camel-core</artifactId>
    <version>2.25.4</version>
</dependency>
```

**After (Camel 4)**:
```xml
<dependency>
    <groupId>org.apache.camel</groupId>
    <artifactId>camel-core-model</artifactId>
    <version>4.0.0</version>
</dependency>
<dependency>
    <groupId>org.apache.camel</groupId>
    <artifactId>camel-core-engine</artifactId>
    <version>4.0.0</version>
</dependency>
```

## Troubleshooting

### Common Issues

1. **Environment Validation Fails**
   ```bash
   # Check specific tool
   java -version
   mvn --version
   docker --version
   ```

2. **Compilation Errors After Migration**
   - Check for custom processors needing manual updates
   - Verify all imports are correct
   - Look for deprecated API usage

3. **Test Failures**
   - Update test assertions for new behavior
   - Check for timing issues in integration tests

4. **LLM API Errors**
   - Verify API key is correct
   - Check rate limits
   - Ensure network connectivity

### Debug Mode

Run with verbose output:
```bash
export AGENT_VERBOSE=true
python main.py --repo <url>
```

### Manual Intervention Points

Some scenarios require manual review:
- Complex custom processors
- Non-standard component usage
- Database migration scripts
- Custom error handlers

## Development Process

### How This Project Was Built

1. **Requirements Analysis**
   - Studied Camel 2 to 4 migration patterns
   - Identified key conversion requirements
   - Designed multi-agent architecture

2. **Agent Implementation**
   - Created specialized agents using CrewAI
   - Implemented tool functions for each task
   - Added system prompts for guidance

3. **Workflow Orchestration**
   - Built LangGraph workflow
   - Added conditional routing
   - Implemented error handling

4. **Testing Strategy**
   - Unit tests for each agent
   - Integration tests for workflow
   - Example files for validation

5. **Documentation**
   - Comprehensive guides
   - Code examples
   - Troubleshooting section

### Key Design Decisions

1. **CrewAI for Agents**: Provides structured agent framework
2. **LangGraph for Orchestration**: Enables complex workflow management
3. **Tool Separation**: Keeps logic modular and testable
4. **Few-Shot Learning**: Improves conversion accuracy
5. **Containerization Focus**: Ensures cloud-readiness

### Future Enhancements

1. **Additional Conversions**
   - Support for more Camel components
   - Custom DSL patterns
   - Blueprint to Spring conversion

2. **Enhanced Testing**
   - Performance testing
   - Load testing automation
   - Security scanning

3. **Monitoring**
   - Migration metrics dashboard
   - Success rate tracking
   - Performance analytics

4. **Extended Platform Support**
   - OpenShift templates
   - AWS ECS/Fargate
   - Azure Container Instances

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-org/camel-migration-agent/issues)
- Documentation: This guide and code comments
- Examples: See the `examples/` directory

---

**Note**: This is an AI-powered tool. Always review and test the migrated code thoroughly before deploying to production.
