# Test Suite Documentation

## Valid Test Files

The Camel Migration Agent includes the following test scripts:

### 1. `verify_system.py` ✅
**Purpose:** Quick system verification  
**What it tests:**
- All imports work correctly
- LLM configuration is valid
- All 7 agents can be created
- Workflow orchestration works

**Usage:**
```bash
python verify_system.py
```

### 2. `test_crewai_agents.py` ✅
**Purpose:** Test agent creation with CrewAI framework  
**What it tests:**
- Each agent can be instantiated
- CrewAI Task creation works
- Agent-task integration

**Usage:**
```bash
python test_crewai_agents.py
```

### 3. `test_end_to_end.py` ✅
**Purpose:** End-to-end integration testing  
**What it tests:**
- Environment setup
- Sample repository analysis
- Individual migration steps
- Workflow orchestration

**Usage:**
```bash
python test_end_to_end.py
```

### 4. `test_full_migration.py` ✅
**Purpose:** Full migration execution test  
**What it tests:**
- Complete migration using main.py
- Repository cloning
- POM updates
- Containerization artifacts

**Usage:**
```bash
python test_full_migration.py
```

## Running Tests

### Quick Verification
```bash
# Verify system is working
python verify_system.py
```

### Comprehensive Testing
```bash
# Test all agents
python test_crewai_agents.py

# Test complete workflow
python test_end_to_end.py

# Run actual migration test
python test_full_migration.py
```

## Test Results Location

Test outputs are saved to:
- `/tmp/camel_migration_test_*` - Test workspaces
- `/tmp/camel_migration_test_report.txt` - Test reports

## Removed/Obsolete Files

The following test files were removed as they are obsolete or broken:
- `run_tests.py` - Obsolete wrapper script
- `test_agents.py` - Old comprehensive test with import issues
- `test_individual_agents.py` - Uses wrong import patterns
- `direct_test.py` - Has incorrect path configuration

## Notes

- All tests disable display warnings using environment variables
- Tests use the sample Fuse 6 application from GitHub for validation
- The LLM configuration must be properly set in `.env` file
- Tests may take a few minutes to complete due to LLM operations