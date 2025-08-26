# User Guide: Red Hat Camel Migration Agent

## Table of Contents
- [Getting Started](#getting-started)
- [Migration Workflow](#migration-workflow)
- [GUI Dashboard](#gui-dashboard)
- [Understanding Migration Results](#understanding-migration-results)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Getting Started

### Prerequisites
Before starting the migration, ensure you have:
- A Fuse 6/7 application in a Git repository
- Python 3.11 or higher installed
- An OpenAI-compatible API key
- Internet connection for JDK downloads

### Installation Steps

1. **Clone the Migration Agent**
   ```bash
   git clone <repository-url>
   cd camel-migration-agent
   ```

2. **Set up Python Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file with your settings:
   ```bash
   MODEL_API_KEY=your_openai_api_key_here
   MODEL_NAME=gpt-4
   MODEL_BASE_URL=https://api.openai.com/v1
   MODEL_TEMPERATURE=0.7
   ```

4. **Verify Installation**
   ```bash
   python tests/verify_system.py
   ```

## Migration Workflow

### Starting a Migration

Run the migration with a single command:
```bash
python -m tasks.run_coordinator \
  --source-path /path/to/your/fuse-app \
  --branch feature/fuse2camel \
  --port 8000
```

**Parameters:**
- `--source-path`: Path to your local Fuse 6/7 Git repository
- `--branch`: Name for the migration branch (default: feature/fuse2camel)
- `--port`: GUI dashboard port (default: 8000)
- `--no-browser`: Skip automatic browser opening

### Migration Phases

The migration process follows these phases:

#### Phase 1: Coordinator (Setup & Validation)
- Validates environment configuration
- Initializes workflow state
- Prepares migration artifacts directory

#### Phase 2: JDK Agent (Java 21 Setup)
**What happens:**
- Checks for existing Java 21+ installation
- Downloads JDK 21 from Eclipse Temurin if needed
- Extracts and configures JDK in `./artifacts/jdk21/`
- Creates activation script at `./artifacts/activate_java.sh`

**GUI Integration:**
- Real-time download progress
- JDK path configuration interface
- Installation status updates

#### Phase 3: Git Agent (Repository Management)
**What happens:**
- Validates local Git repository
- Creates migration branch
- Handles branch conflicts through user interaction

**User Interaction:**
If the branch already exists, you'll see a GUI prompt with options:
- **Override**: Switch to existing branch (overwrites current branch)
- **Create New**: Creates a new branch with suffix (e.g., feature/fuse2camel-new)
- **Ignore**: Continue with existing branch as-is

#### Phase 4: Dependency Agent (Maven POM Updates)
**Transformations:**
- Updates parent POM to Red Hat Camel Spring Boot BOM
- Adds Red Hat Maven repositories
- Maps legacy dependencies to Red Hat equivalents
- Updates version properties

**Example Changes:**
```xml
<!-- Before -->
<parent>
  <groupId>org.apache.camel.springboot</groupId>
  <artifactId>camel-spring-boot-bom</artifactId>
  <version>2.x.x</version>
</parent>

<!-- After -->
<parent>
  <groupId>com.redhat.camel.springboot</groupId>
  <artifactId>camel-spring-boot-bom</artifactId>
  <version>4.10.0.redhat-00001</version>
</parent>
```

#### Phase 5: DSL Conversion Agent (XML to Java DSL)
**Transformations:**
- Converts XML Spring route definitions to Java DSL
- Creates RouteBuilder classes with @Component annotations
- Maintains original route logic while updating syntax

**Example Conversion:**
```xml
<!-- camel-context.xml -->
<route>
  <from uri="timer:foo?period=5000"/>
  <setBody><constant>Hello World</constant></setBody>
  <to uri="log:bar"/>
</route>
```

```java
// Generated Java DSL
@Component
public class MigrationRoutes extends RouteBuilder {
    @Override
    public void configure() throws Exception {
        from("timer:foo?period=5000")
            .setBody(constant("Hello World"))
            .to("log:bar");
    }
}
```

#### Phase 6: Service Refactor Agent (Java Code Updates)
**Transformations:**
- Updates Exchange API calls: `getIn()/getOut()` → `getMessage()`
- Fixes imports: `org.apache.camel.impl.*` → `org.apache.camel.support.*`
- Adds @Component annotations for Spring Boot integration
- Updates Processor implementations

**Example Refactoring:**
```java
// Before
public void process(Exchange exchange) {
    String data = exchange.getIn().getBody(String.class);
    exchange.getOut().setBody(data.toUpperCase());
}

// After
@Component
public void process(Exchange exchange) {
    String data = exchange.getMessage().getBody(String.class);
    exchange.getMessage().setBody(data.toUpperCase());
}
```

#### Phase 7: Reporter (Migration Summary)
**Generates:**
- Comprehensive migration report
- Files modified and created
- Dependency changes summary
- Code transformation details
- Validation status and recommendations

## GUI Dashboard

Access the dashboard at `http://127.0.0.1:8000` to monitor migration progress.

### Dashboard Features

#### Flow Diagram
- Visual workflow representation using Mermaid
- Real-time phase status updates
- Color-coded progress indicators:
  - **Gray**: Pending
  - **Yellow**: In Progress
  - **Green**: Completed
  - **Red**: Failed

#### JDK Installation Panel
- Current JDK status display
- Installation path configuration
- Download progress tracking

#### Events Log
- Real-time event streaming
- Detailed phase information
- Timing and duration data
- Error messages and status updates

#### Run Summary
- Overall progress statistics
- Completion status
- Error count and success metrics

### Interactive Features

#### Branch Conflict Resolution
When a branch conflict occurs:
1. GUI displays a prompt with options
2. Select your preferred action:
   - **Override**: Replaces existing branch
   - **Create New**: Creates a new branch variant
   - **Ignore**: Uses existing branch unchanged
3. Migration continues automatically

#### JDK Path Configuration
1. Click "Set Path" button in JDK panel
2. Enter desired installation path
3. System validates and configures path
4. Installation proceeds with user-specified location

## Understanding Migration Results

### Files Created/Modified

**New Files:**
- `./artifacts/jdk21/` - JDK 21 installation
- `./artifacts/activate_java.sh` - Java environment activation
- `src/main/java/.../RouteConfiguration.java` - Generated route classes
- Migration report PDF in project root

**Modified Files:**
- `pom.xml` - Updated with Red Hat dependencies
- Java processor/bean classes - Updated for Camel 4 APIs
- Existing route classes - Refactored for modern syntax

### Validation Steps

After migration completion:

1. **Compile Check**
   ```bash
   cd /path/to/your/migrated-app
   source ../camel-migration-agent/artifacts/activate_java.sh
   mvn clean compile
   ```

2. **Dependency Verification**
   ```bash
   mvn dependency:tree | grep camel
   ```
   Should show Red Hat Camel 4.10 dependencies

3. **Route Testing**
   ```bash
   mvn spring-boot:run
   ```
   Verify routes start without errors

## Troubleshooting

### Common Issues

#### JDK Download Fails
**Symptoms:**
- GUI shows "JDK Installation Failed"
- Error in events log about download issues

**Solutions:**
1. Check internet connectivity
2. Verify sufficient disk space in `./artifacts/jdk21/`
3. Clear artifacts directory and retry:
   ```bash
   rm -rf ./artifacts/jdk21/
   ```

#### Branch Creation Errors
**Symptoms:**
- Git agent reports branch conflicts
- GUI prompts not responding

**Solutions:**
1. Ensure Git repository is clean:
   ```bash
   git status
   git stash  # if needed
   ```
2. Check Git permissions and remote access
3. Use GUI prompts to resolve conflicts

#### GUI Not Loading
**Symptoms:**
- Browser shows connection refused
- Dashboard appears blank

**Solutions:**
1. Check if port 8000 is available:
   ```bash
   lsof -i :8000
   ```
2. Try different port:
   ```bash
   python -m tasks.run_coordinator --port 8001 ...
   ```
3. Clear browser cache and reload

#### Migration Compilation Errors
**Symptoms:**
- Java compilation fails after migration
- Import or API errors in generated code

**Solutions:**
1. Review migration report for incomplete transformations
2. Manually fix any remaining Camel 2.x syntax
3. Verify all dependencies are updated correctly
4. Check generated RouteBuilder classes for syntax errors

### Log Analysis

**Event Logs:**
Check `artifacts/events.jsonl` for detailed migration steps and any error messages.

**GUI Console:**
Open browser developer tools (F12) to see JavaScript errors or network issues.

**System Logs:**
Check terminal output where coordinator was started for system-level errors.

## Best Practices

### Pre-Migration
1. **Create a backup branch:**
   ```bash
   cd /path/to/your/fuse-app
   git checkout -b backup-before-migration
   git checkout main  # or your working branch
   ```

2. **Clean working directory:**
   ```bash
   git status
   git add . && git commit -m "Clean state before migration"
   ```

3. **Document current functionality:**
   - Note existing route behaviors
   - Document any custom processors
   - Record current test results

### During Migration
1. **Monitor GUI dashboard** for real-time progress
2. **Respond to prompts promptly** to avoid timeouts
3. **Review each phase completion** before proceeding
4. **Note any warnings or error messages**

### Post-Migration
1. **Thoroughly test migrated application:**
   ```bash
   mvn clean test
   mvn spring-boot:run
   ```

2. **Review generated code:**
   - Check RouteBuilder classes for accuracy
   - Verify processor logic preservation
   - Validate dependency configurations

3. **Update documentation:**
   - Update README with new Camel 4 information
   - Document any manual changes needed
   - Update deployment procedures if changed

4. **Commit changes systematically:**
   ```bash
   git add pom.xml
   git commit -m "Update Maven dependencies to Red Hat Camel 4.10"
   
   git add src/main/java/
   git commit -m "Migrate Java code to Camel 4 APIs"
   ```

### Performance Tips
1. **Use fast internet connection** for JDK downloads
2. **Ensure sufficient disk space** (>500MB for JDK)
3. **Close unnecessary applications** during migration
4. **Use SSD storage** for faster file operations

### Security Considerations
1. **Protect API keys** - never commit .env files
2. **Review generated code** before production use
3. **Test security configurations** after migration
4. **Validate dependency sources** are from Red Hat repositories

This migration tool is designed to handle the majority of Fuse 6/7 to Red Hat Camel 4.10 transformations automatically, but complex applications may require additional manual adjustments after the automated migration completes.