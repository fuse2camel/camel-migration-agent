"""
Test cases for all Camel Migration Agents
"""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.config_agent import ConfigAgent
from agents.git_agent import GitAgent
from agents.dependency_agent import DependencyAgent
from agents.dsl_conversion_agent import DSLConversionAgent
from agents.service_refactor_agent import ServiceRefactorAgent
from agents.test_agent import TestAgent
from agents.containerization_agent import ContainerizationAgent


class TestConfigAgent(unittest.TestCase):
    """Test cases for Config Agent"""
    
    def setUp(self):
        self.agent = ConfigAgent()
    
    @patch('agents.config_agent.validate_environment')
    def test_validate_success(self, mock_validate):
        """Test successful environment validation"""
        mock_validate.return_value = {
            "overall_status": "Success",
            "checks": [
                {"tool": "Java JDK", "status": "Success", "meets_requirement": True},
                {"tool": "Maven", "status": "Success", "meets_requirement": True},
                {"tool": "Git", "status": "Success", "meets_requirement": True},
                {"tool": "Container Engine", "status": "Success", "meets_requirement": True}
            ]
        }
        
        result = self.agent.validate()
        
        self.assertEqual(result["overall_status"], "Success")
        self.assertEqual(len(result["checks"]), 4)
    
    def test_get_validation_summary(self):
        """Test validation summary generation"""
        validation_report = {
            "overall_status": "Success",
            "checks": [
                {
                    "tool": "Java JDK",
                    "meets_requirement": True,
                    "current_version": "17",
                    "required_version": "17"
                }
            ]
        }
        
        summary = self.agent.get_validation_summary(validation_report)
        
        self.assertIn("Java JDK", summary)
        self.assertIn("✓", summary)


class TestGitAgent(unittest.TestCase):
    """Test cases for Git Agent"""
    
    def setUp(self):
        self.agent = GitAgent()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('agents.git_agent.clone_repository')
    def test_initiate_workflow(self, mock_clone):
        """Test workflow initiation"""
        mock_clone.return_value = {
            "status": "Success",
            "local_path": self.temp_dir
        }
        
        result = self.agent.initiate_workflow(
            repository_url="https://github.com/test/repo.git",
            branch_name="test-branch",
            workspace_dir=self.temp_dir
        )
        
        self.assertEqual(result["status"], "Success")
        self.assertEqual(result["workflow_stage"], "initiate")
    
    @patch('agents.git_agent.commit_changes')
    @patch('agents.git_agent.push_changes')
    def test_finalize_workflow(self, mock_push, mock_commit):
        """Test workflow finalization"""
        mock_commit.return_value = {
            "status": "Success",
            "commit_hash": "abc123"
        }
        mock_push.return_value = {
            "status": "Success",
            "pushed_branch_url": "https://github.com/test/repo/tree/test-branch"
        }
        
        result = self.agent.finalize_workflow(
            source_code_path=self.temp_dir,
            commit_message="Test commit"
        )
        
        self.assertEqual(result["status"], "Success")
        self.assertEqual(result["workflow_stage"], "finalize")


class TestDependencyAgent(unittest.TestCase):
    """Test cases for Dependency Agent"""
    
    def setUp(self):
        self.agent = DependencyAgent()
        self.temp_dir = tempfile.mkdtemp()
        self.pom_file = os.path.join(self.temp_dir, "pom.xml")
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_sample_pom(self):
        """Create a sample pom.xml file"""
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>camel-app</artifactId>
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
</project>"""
        with open(self.pom_file, 'w') as f:
            f.write(pom_content)
    
    @patch('agents.dependency_agent.parse_pom_file')
    def test_analyze_dependencies(self, mock_parse):
        """Test dependency analysis"""
        mock_parse.return_value = {
            "status": "Success",
            "dependencies": [
                {"groupId": "org.apache.camel", "artifactId": "camel-core", "version": "2.25.4"}
            ],
            "properties": {"camel.version": "2.25.4"}
        }
        
        self.create_sample_pom()
        result = self.agent.analyze_dependencies(self.pom_file)
        
        self.assertEqual(result["status"], "Success")
        self.assertTrue(result["needs_migration"])
        self.assertEqual(result["camel_dependencies"], 1)


class TestDSLConversionAgent(unittest.TestCase):
    """Test cases for DSL Conversion Agent"""
    
    def setUp(self):
        self.agent = DSLConversionAgent()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_sample_xml_route(self):
        """Create a sample XML route file"""
        xml_file = os.path.join(self.temp_dir, "routes.xml")
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns="http://camel.apache.org/schema/spring">
    <route id="test-route">
        <from uri="timer:foo"/>
        <to uri="log:bar"/>
    </route>
</routes>"""
        with open(xml_file, 'w') as f:
            f.write(xml_content)
        return xml_file
    
    @patch('agents.dsl_conversion_agent.create_route_builder_from_xml')
    def test_convert_routes(self, mock_convert):
        """Test route conversion"""
        xml_file = self.create_sample_xml_route()
        mock_convert.return_value = {
            "status": "Success",
            "output_file": os.path.join(self.temp_dir, "TestRoute.java"),
            "route_count": 1
        }
        
        result = self.agent.convert_routes(
            source_code_path=self.temp_dir,
            source_files=[xml_file]
        )
        
        self.assertEqual(result["status"], "Success")
        self.assertEqual(result["file_count"], 1)


class TestServiceRefactorAgent(unittest.TestCase):
    """Test cases for Service Refactor Agent"""
    
    def setUp(self):
        self.agent = ServiceRefactorAgent()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_sample_processor(self):
        """Create a sample processor file"""
        java_file = os.path.join(self.temp_dir, "MyProcessor.java")
        java_content = """
package com.example;

import org.apache.camel.Exchange;
import org.apache.camel.Processor;

public class MyProcessor implements Processor {
    public void process(Exchange exchange) {
        String body = exchange.getIn().getBody(String.class);
        exchange.getOut().setBody(body.toUpperCase());
    }
}"""
        with open(java_file, 'w') as f:
            f.write(java_content)
        return java_file
    
    @patch('agents.service_refactor_agent.analyze_java_files')
    @patch('agents.service_refactor_agent.refactor_java_code')
    def test_refactor_business_logic(self, mock_refactor, mock_analyze):
        """Test business logic refactoring"""
        java_file = self.create_sample_processor()
        
        mock_analyze.return_value = {
            "status": "Success",
            "total_java_files": 1,
            "camel_files": [java_file],
            "camel_file_count": 1
        }
        
        mock_refactor.return_value = {
            "status": "Success",
            "changes_made": ["Replaced getIn() with getMessage()"]
        }
        
        result = self.agent.refactor_business_logic(self.temp_dir)
        
        self.assertEqual(result["status"], "Success")
        self.assertEqual(result["refactored_count"], 1)


class TestTestAgent(unittest.TestCase):
    """Test cases for Test Agent"""
    
    def setUp(self):
        self.agent = TestAgent()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('agents.test_agent.run_maven_command')
    def test_validate_migration(self, mock_maven):
        """Test migration validation"""
        mock_maven.return_value = {
            "status": "Success",
            "build_success": True,
            "message": "BUILD SUCCESS"
        }
        
        result = self.agent.validate_migration(
            project_root_path=self.temp_dir,
            run_full_tests=False
        )
        
        self.assertIn("compilation_status", result)
        self.assertIn("steps", result)
    
    def test_generate_test_report(self):
        """Test report generation"""
        validation_result = {
            "project_path": "/test/path",
            "compilation_status": "Success",
            "test_run_results": "Success",
            "smoke_test_passed": True,
            "overall_status": "Success",
            "steps": [
                {"step": "Compilation", "status": "Success"}
            ]
        }
        
        report = self.agent.generate_test_report(validation_result)
        
        self.assertIn("VALIDATION REPORT", report)
        self.assertIn("Success", report)


class TestContainerizationAgent(unittest.TestCase):
    """Test cases for Containerization Agent"""
    
    def setUp(self):
        self.agent = ContainerizationAgent()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('agents.containerization_agent.generate_dockerfile')
    def test_containerize_application(self, mock_docker):
        """Test application containerization"""
        mock_docker.return_value = {
            "status": "Success",
            "dockerfile_path": os.path.join(self.temp_dir, "Dockerfile"),
            "dockerignore_path": os.path.join(self.temp_dir, ".dockerignore")
        }
        
        result = self.agent.containerize_application(
            project_root_path=self.temp_dir,
            app_name="test-app",
            build_image=False
        )
        
        self.assertEqual(result["status"], "Success")
        self.assertIn("artifacts", result)
    
    def test_generate_deployment_guide(self):
        """Test deployment guide generation"""
        containerization_result = {
            "app_name": "test-app",
            "project_path": "/test/path",
            "artifacts": {
                "dockerfile": {"dockerfile_path": "/test/Dockerfile"}
            }
        }
        
        guide = self.agent.generate_deployment_guide(containerization_result)
        
        self.assertIn("Docker Deployment Guide", guide)
        self.assertIn("docker run", guide)
        self.assertIn("docker-compose", guide)


if __name__ == "__main__":
    unittest.main()
