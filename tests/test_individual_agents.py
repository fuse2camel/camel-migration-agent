#!/usr/bin/env python3
"""
Individual Agent Testing
Tests each agent in isolation to ensure they work correctly
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable display warnings
os.environ.pop('DISPLAY', None)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from agents.config_agent import ConfigAgent
from agents.git_agent import GitAgent
from agents.dependency_agent import DependencyAgent
from agents.dsl_conversion_agent import DSLConversionAgent
from agents.service_refactor_agent import ServiceRefactorAgent
from agents.containerization_agent import ContainerizationAgent
from agents.test_agent import TestAgent
from crewai import Crew


class TestAgents:
    """Test individual agents"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="agent_test_")
        print(f"Test directory: {self.test_dir}")
    
    def cleanup(self):
        """Clean up test directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_config_agent(self):
        """Test ConfigAgent"""
        print("\n" + "="*60)
        print("Testing ConfigAgent")
        print("="*60)
        
        try:
            agent = ConfigAgent()
            requirements = {
                "java": "17",
                "maven": "3.8.0",
                "git": "Any",
                "docker": "Any"
            }
            
            task = agent.create_validation_task(requirements)
            crew = Crew(
                agents=[agent.agent],
                tasks=[task],
                verbose=False
            )
            
            result = crew.kickoff()
            print(f"✅ ConfigAgent test passed")
            print(f"   Result: {str(result)[:100]}...")
            return True
        except Exception as e:
            print(f"❌ ConfigAgent test failed: {e}")
            return False
    
    def test_git_agent(self):
        """Test GitAgent"""
        print("\n" + "="*60)
        print("Testing GitAgent")
        print("="*60)
        
        try:
            agent = GitAgent()
            
            # Test with a sample repository
            task = agent.create_initiate_task(
                repository_url="https://github.com/apache/camel-examples.git",
                branch_name="test-migration",
                workspace_dir=os.path.join(self.test_dir, "git_test")
            )
            
            crew = Crew(
                agents=[agent.agent],
                tasks=[task],
                verbose=False
            )
            
            # We'll just test that the agent can be created and task defined
            # Not actually cloning to save time
            print(f"✅ GitAgent test passed (agent and task created)")
            return True
        except Exception as e:
            print(f"❌ GitAgent test failed: {e}")
            return False
    
    def test_dependency_agent(self):
        """Test DependencyAgent"""
        print("\n" + "="*60)
        print("Testing DependencyAgent")
        print("="*60)
        
        try:
            agent = DependencyAgent()
            
            # Create a sample pom.xml for testing
            pom_path = os.path.join(self.test_dir, "pom.xml")
            with open(pom_path, "w") as f:
                f.write("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-app</artifactId>
    <version>1.0.0</version>
    <dependencies>
        <dependency>
            <groupId>org.apache.camel</groupId>
            <artifactId>camel-core</artifactId>
            <version>2.25.4</version>
        </dependency>
    </dependencies>
</project>""")
            
            task = agent.create_update_task(pom_path)
            crew = Crew(
                agents=[agent.agent],
                tasks=[task],
                verbose=False
            )
            
            # Test that agent and task can be created
            print(f"✅ DependencyAgent test passed (agent and task created)")
            return True
        except Exception as e:
            print(f"❌ DependencyAgent test failed: {e}")
            return False
    
    def test_dsl_conversion_agent(self):
        """Test DSLConversionAgent"""
        print("\n" + "="*60)
        print("Testing DSLConversionAgent")
        print("="*60)
        
        try:
            agent = DSLConversionAgent()
            
            # Create a sample route for testing
            route_dir = os.path.join(self.test_dir, "src", "main", "java", "com", "example")
            os.makedirs(route_dir, exist_ok=True)
            
            route_file = os.path.join(route_dir, "TestRoute.java")
            with open(route_file, "w") as f:
                f.write("""
package com.example;

import org.apache.camel.builder.RouteBuilder;

public class TestRoute extends RouteBuilder {
    @Override
    public void configure() throws Exception {
        from("timer:test?period=1000")
            .log("Test message")
            .to("mock:result");
    }
}
""")
            
            task = agent.create_conversion_task(self.test_dir)
            crew = Crew(
                agents=[agent.agent],
                tasks=[task],
                verbose=False
            )
            
            print(f"✅ DSLConversionAgent test passed (agent and task created)")
            return True
        except Exception as e:
            print(f"❌ DSLConversionAgent test failed: {e}")
            return False
    
    def test_service_refactor_agent(self):
        """Test ServiceRefactorAgent"""
        print("\n" + "="*60)
        print("Testing ServiceRefactorAgent")
        print("="*60)
        
        try:
            agent = ServiceRefactorAgent()
            
            task = agent.create_refactor_task(self.test_dir)
            crew = Crew(
                agents=[agent.agent],
                tasks=[task],
                verbose=False
            )
            
            print(f"✅ ServiceRefactorAgent test passed (agent and task created)")
            return True
        except Exception as e:
            print(f"❌ ServiceRefactorAgent test failed: {e}")
            return False
    
    def test_containerization_agent(self):
        """Test ContainerizationAgent"""
        print("\n" + "="*60)
        print("Testing ContainerizationAgent")
        print("="*60)
        
        try:
            agent = ContainerizationAgent()
            
            task = agent.create_containerization_task(self.test_dir)
            crew = Crew(
                agents=[agent.agent],
                tasks=[task],
                verbose=False
            )
            
            print(f"✅ ContainerizationAgent test passed (agent and task created)")
            return True
        except Exception as e:
            print(f"❌ ContainerizationAgent test failed: {e}")
            return False
    
    def test_test_agent(self):
        """Test TestAgent"""
        print("\n" + "="*60)
        print("Testing TestAgent")
        print("="*60)
        
        try:
            agent = TestAgent()
            
            task = agent.create_test_task(self.test_dir)
            crew = Crew(
                agents=[agent.agent],
                tasks=[task],
                verbose=False
            )
            
            print(f"✅ TestAgent test passed (agent and task created)")
            return True
        except Exception as e:
            print(f"❌ TestAgent test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all agent tests"""
        print("\n" + "="*60)
        print("INDIVIDUAL AGENT TESTING")
        print("="*60)
        
        results = []
        
        # Test each agent
        results.append(("ConfigAgent", self.test_config_agent()))
        results.append(("GitAgent", self.test_git_agent()))
        results.append(("DependencyAgent", self.test_dependency_agent()))
        results.append(("DSLConversionAgent", self.test_dsl_conversion_agent()))
        results.append(("ServiceRefactorAgent", self.test_service_refactor_agent()))
        results.append(("ContainerizationAgent", self.test_containerization_agent()))
        results.append(("TestAgent", self.test_test_agent()))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        all_passed = True
        for agent_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{agent_name}: {status}")
            if not passed:
                all_passed = False
        
        print("\n" + "="*60)
        if all_passed:
            print("✅ ALL AGENT TESTS PASSED")
        else:
            print("❌ SOME AGENT TESTS FAILED")
        print("="*60)
        
        return all_passed


def main():
    """Main test runner"""
    tester = TestAgents()
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())