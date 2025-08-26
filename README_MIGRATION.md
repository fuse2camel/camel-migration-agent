# Red Hat Camel Migration Agent

A comprehensive enterprise migration system for transforming Fuse 6/7 applications to Red Hat build of Apache Camel 4.10 with Spring Boot 3.x compatibility.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git repository with Fuse 6/7 application
- OpenAI-compatible API key

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd camel-migration-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API key and model settings
```

### Run Migration
```bash
# Single command migration with GUI dashboard
python -m tasks.run_coordinator \
  --source-path /path/to/your/fuse-app \
  --branch feature/fuse2camel \
  --port 8000

# Access GUI dashboard at http://127.0.0.1:8000
```

## 🏗️ Architecture

### Multi-Agent System
The migration system uses specialized CrewAI agents orchestrated by LangGraph:

1. **JDK Agent** - Automatic JDK 21 installation from Adoptium
2. **Git Agent** - Repository management with branch conflict resolution  
3. **Dependency Agent** - Maven POM migration to Red Hat Camel 4.10 BOM
4. **DSL Conversion Agent** - XML routes to Java DSL transformation
5. **Service Refactor Agent** - Java code updates for Camel 4.10 APIs
6. **Reporter** - Migration summary and compliance reporting

### GUI Dashboard
Real-time workflow monitoring with:
- Interactive flow diagram showing migration progress
- Live event streaming with detailed phase information
- JDK installation status and path configuration
- Branch conflict resolution prompts
- Migration artifact tracking

## 🔄 Migration Process

### What Gets Migrated

#### Maven Dependencies
```xml
<!-- FROM: Legacy Fuse/Camel 2.x -->
<parent>
  <groupId>org.apache.camel.springboot</groupId>
  <artifactId>camel-spring-boot-bom</artifactId>
  <version>2.x</version>
</parent>

<!-- TO: Red Hat Camel 4.10 -->
<parent>
  <groupId>com.redhat.camel.springboot</groupId>
  <artifactId>camel-spring-boot-bom</artifactId>
  <version>4.10.0.redhat-00001</version>
</parent>
```

#### Dependency Mappings
- `camel-http4` → `camel-http`
- `camel-jetty9` → `camel-jetty`
- `camel-rabbitmq` → `camel-spring-rabbitmq`
- Adds Red Hat Maven repositories

#### XML to Java DSL
```xml
<!-- FROM: Spring XML configuration -->
<route>
  <from uri="timer:foo"/>
  <to uri="log:bar"/>
</route>
```

```java
// TO: Red Hat Camel 4.10 Java DSL
@Component
public class MigrationRoutes extends RouteBuilder {
    @Override
    public void configure() throws Exception {
        from("timer:foo").to("log:bar");
    }
}
```

#### Exchange API Updates
```java
// FROM: Legacy Camel 2.x
public void process(Exchange exchange) {
    exchange.getIn().setBody("data");
    String header = exchange.getOut().getHeader("id", String.class);
}

// TO: Red Hat Camel 4.10
@Component
public void process(Exchange exchange) {
    exchange.getMessage().setBody("data");
    String header = exchange.getMessage().getHeader("id", String.class);
}
```

## 🛠️ Technical Features

### Enterprise-Grade Capabilities
- **Automatic JDK Management**: Downloads and configures JDK 21 from Eclipse Temurin
- **Interactive Branch Resolution**: GUI-based conflict resolution for existing branches
- **Red Hat Repository Integration**: Automatic configuration of Red Hat Maven repositories
- **Real-time Monitoring**: Live GUI dashboard with phase tracking and event streaming
- **Error Recovery**: Comprehensive error handling with detailed reporting
- **Cross-platform Support**: Works on macOS, Linux, and Windows

### GUI Integration
- **Flow Visualization**: Mermaid-based diagrams showing migration workflow
- **JDK Path Configuration**: Interactive JDK installation path selection
- **Branch Conflict Resolution**: User prompts for branch override/create-new/ignore options
- **Live Updates**: Real-time SSE (Server-Sent Events) for workflow progress
- **Status Tracking**: Phase-by-phase completion status with timing information

### Code Quality
- **Enterprise Patterns**: Applies Red Hat security and monitoring patterns
- **Spring Boot 3.x Integration**: Full compatibility with modern Spring Boot
- **Import Optimization**: Updates package imports for Camel 4.x structure
- **Component Annotations**: Adds @Component annotations for Spring discovery

## 📊 Migration Report

The system generates comprehensive migration reports including:
- Files analyzed and transformed
- Dependency changes made
- Code patterns updated  
- Red Hat compliance status
- Validation results
- Recommendations for manual review

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required
MODEL_API_KEY=your_api_key_here
MODEL_NAME=gpt-4  # or compatible model
MODEL_BASE_URL=https://api.openai.com/v1

# Optional
MODEL_TEMPERATURE=0.7
DEFAULT_BRANCH_NAME=feature/fuse2camel
```

### GUI Settings
- **Port Configuration**: Default 8000, configurable via --port
- **JDK Path Selection**: Interactive path configuration through GUI
- **Branch Resolution**: User-driven decision making for conflicts
- **Real-time Updates**: Automatic refresh with SSE connections

## 🧪 Testing

```bash
# System verification
python tests/verify_system.py

# End-to-end testing
python tests/test_end_to_end.py

# Individual agent testing
python main.py --test-agent jdk
python main.py --test-agent git --repo-url https://github.com/user/fuse-app.git
```

## 📁 Project Structure

```
camel-migration-agent/
├── agents/                 # CrewAI agents for each migration phase
├── config/                 # Configuration and environment validation
├── gui/                    # Web dashboard (FastAPI + HTML/JS)
├── prompts/                # Agent instruction templates
├── tasks/                  # Workflow entry points
├── tools/                  # Utility functions (Git, Maven, etc.)
├── artifacts/              # Generated files (JDK, reports, etc.)
├── tests/                  # Test suites and verification
└── examples/               # Sample Fuse applications
```

## 🚨 Troubleshooting

### Common Issues

**JDK Installation Failed**
- Check internet connectivity for Adoptium downloads
- Verify disk space in ./artifacts/jdk21/ directory
- Review GUI logs for specific error messages

**Branch Conflicts**
- Use GUI prompts to resolve branch conflicts
- Choose override, create-new, or ignore options
- Check Git repository permissions

**GUI Not Loading**
- Ensure port 8000 is available
- Check browser console for JavaScript errors
- Verify FastAPI server is running with uvicorn

**Migration Errors**
- Review artifacts/events.jsonl for detailed logs
- Check Maven POM syntax after dependency updates
- Validate Java compilation after code transformations

## 🎯 Best Practices

1. **Backup Your Code**: Always work on a separate Git branch
2. **Review Changes**: Inspect generated code before committing
3. **Test Thoroughly**: Run comprehensive tests after migration
4. **Monitor GUI**: Use the dashboard to track progress and errors
5. **Check Logs**: Review event logs for detailed migration information

## 📖 Documentation

- **Agent Prompts**: See `prompts/` directory for detailed agent instructions
- **API Documentation**: FastAPI automatically generates docs at `/docs`
- **Migration Patterns**: Review `examples/` for transformation patterns
- **Configuration**: Check `config/` for environment and workflow settings

## 🤝 Contributing

This is an enterprise migration tool designed for Red Hat Camel 4.10 migration. Contributions should maintain compatibility with Red Hat certified components and enterprise development patterns.

## 📄 License

Enterprise migration tool for Red Hat build of Apache Camel 4.10 compatibility.