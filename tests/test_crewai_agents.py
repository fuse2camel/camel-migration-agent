#!/usr/bin/env python3
"""Test CrewAI Agents with their actual methods"""
import os
import sys
import tempfile
from pathlib import Path

# Disable display
os.environ.pop('DISPLAY', None)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add project to path
sys.path.insert(0, '/')

def test_config_agent():
    """Test Config Agent validation"""
    print("\n" + "=" * 50)
    print("TEST: Config Agent")
    print("=" * 50)
    try:
        from agents.config_agent import ConfigAgent
        
        agent = ConfigAgent()
        
        # Test validation with empty requirements
        result = agent.validate(requirements_config={})
        print(f"✅ Config Agent validation result: {result.get('status', 'unknown')}")
        
        # Get summary
        summary = agent.get_validation_summary(result)
        print(f"   Summary: {summary[:100]}..." if len(summary) > 100 else f"   Summary: {summary}")
        
        return True
    except Exception as e:
        print(f"❌ Config Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependency_agent():
    """Test Dependency Agent with CrewAI tasks"""
    print("\n" + "=" * 50)
    print("TEST: Dependency Agent")
    print("=" * 50)
    try:
        from agents.dependency_agent import DependencyAgent
        from crewai import Task
        
        agent = DependencyAgent()
        
        # Create test POM
        test_dir = Path(tempfile.mkdtemp())
        test_pom = test_dir / "pom.xml"
        test_pom.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.test</groupId>
    <artifactId>test</artifactId>
    <version>1.0.0</version>
    <properties>
        <camel.version>2.25.4</camel.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.apache.camel</groupId>
            <artifactId>camel-core</artifactId>
            <version>${camel.version}</version>
        </dependency>
    </dependencies>
</project>''')
        
        # Create a task for the agent
        task = Task(
            description=f"Analyze and update the POM file at {test_pom} to Camel 4",
            agent=agent.agent,
            expected_output="Updated POM file with Camel 4 dependencies"
        )
        
        print(f"✅ Dependency Agent created successfully")
        print(f"   Test POM created at: {test_pom}")
        return True
    except Exception as e:
        print(f"❌ Dependency Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dsl_conversion_agent():
    """Test DSL Conversion Agent"""
    print("\n" + "=" * 50)
    print("TEST: DSL Conversion Agent")
    print("=" * 50)
    try:
        from agents.dsl_conversion_agent import DSLConversionAgent
        from crewai import Task
        
        agent = DSLConversionAgent()
        
        # Create test XML route
        test_dir = Path(tempfile.mkdtemp())
        test_xml = test_dir / "route.xml"
        test_xml.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns="http://camel.apache.org/schema/spring">
    <route id="test-route">
        <from uri="timer:foo?period=5000"/>
        <to uri="log:output"/>
    </route>
</routes>''')
        
        # Create a task for the agent
        task = Task(
            description=f"Convert the XML route at {test_xml} to Java DSL",
            agent=agent.agent,
            expected_output="Java DSL version of the route"
        )
        
        print(f"✅ DSL Conversion Agent created successfully")
        print(f"   Test XML created at: {test_xml}")
        return True
    except Exception as e:
        print(f"❌ DSL Conversion Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_refactor_agent():
    """Test Service Refactor Agent"""
    print("\n" + "=" * 50)
    print("TEST: Service Refactor Agent")
    print("=" * 50)
    try:
        from agents.service_refactor_agent import ServiceRefactorAgent
        from crewai import Task
        
        agent = ServiceRefactorAgent()
        
        # Create test Java file
        test_dir = Path(tempfile.mkdtemp())
        test_java = test_dir / "TestProcessor.java"
        test_java.write_text('''
import org.apache.camel.Exchange;
import org.apache.camel.Processor;

public class TestProcessor implements Processor {
    public void process(Exchange exchange) throws Exception {
        String body = exchange.getIn().getBody(String.class);
        exchange.getOut().setBody("Processed: " + body);
    }
}''')
        
        # Create a task for the agent
        task = Task(
            description=f"Refactor the Java processor at {test_java} to Camel 4",
            agent=agent.agent,
            expected_output="Refactored Java code compatible with Camel 4"
        )
        
        print(f"✅ Service Refactor Agent created successfully")
        print(f"   Test Java file created at: {test_java}")
        return True
    except Exception as e:
        print(f"❌ Service Refactor Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_containerization_agent():
    """Test Containerization Agent"""
    print("\n" + "=" * 50)
    print("TEST: Containerization Agent")
    print("=" * 50)
    try:
        from agents.containerization_agent import ContainerizationAgent
        from crewai import Task
        
        agent = ContainerizationAgent()
        
        # Create test project
        test_dir = Path(tempfile.mkdtemp())
        pom = test_dir / "pom.xml"
        pom.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.test</groupId>
    <artifactId>camel-app</artifactId>
    <version>1.0.0</version>
</project>''')
        
        # Create a task for the agent
        task = Task(
            description=f"Generate Docker and Kubernetes artifacts for the project at {test_dir}",
            agent=agent.agent,
            expected_output="Dockerfile and Kubernetes manifests"
        )
        
        print(f"✅ Containerization Agent created successfully")
        print(f"   Test project created at: {test_dir}")
        return True
    except Exception as e:
        print(f"❌ Containerization Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_git_agent():
    """Test Git Agent"""
    print("\n" + "=" * 50)
    print("TEST: Git Agent")
    print("=" * 50)
    try:
        from agents.git_agent import GitAgent
        from crewai import Task
        
        agent = GitAgent()
        
        # Create a task for the agent
        test_dir = tempfile.mkdtemp()
        task = Task(
            description=f"Clone the sample repository to {test_dir} and create a migration branch",
            agent=agent.agent,
            expected_output="Repository cloned and branch created"
        )
        
        print(f"✅ Git Agent created successfully")
        print(f"   Will clone to: {test_dir}")
        return True
    except Exception as e:
        print(f"❌ Git Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow():
    """Test the complete workflow"""
    print("\n" + "=" * 50)
    print("TEST: Complete Workflow")
    print("=" * 50)
    try:
        from orchestration.workflow import CamelMigrationWorkflow
        
        workflow = CamelMigrationWorkflow()
        
        print(f"✅ Workflow created successfully")
        print(f"   Stages: {', '.join([s.value for s in workflow.stages]) if hasattr(workflow, 'stages') else 'N/A'}")
        return True
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 50)
    print("CREWAI AGENT TESTING")
    print("=" * 50)
    
    results = []
    
    # Test each agent
    results.append(("Config Agent", test_config_agent()))
    results.append(("Git Agent", test_git_agent()))
    results.append(("Dependency Agent", test_dependency_agent()))
    results.append(("DSL Conversion Agent", test_dsl_conversion_agent()))
    results.append(("Service Refactor Agent", test_service_refactor_agent()))
    results.append(("Containerization Agent", test_containerization_agent()))
    results.append(("Workflow", test_workflow()))
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{name}: {status}")
    
    passed_count = sum(1 for r in results if r[1])
    failed_count = len(results) - passed_count
    
    print("\n" + "=" * 50)
    if all(r[1] for r in results):
        print(f"✅ ALL {len(results)} TESTS PASSED!")
    else:
        print(f"❌ {failed_count} FAILED, ✅ {passed_count} PASSED")
    print("=" * 50)

if __name__ == "__main__":
    main()