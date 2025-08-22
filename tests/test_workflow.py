"""
Test cases for the Camel Migration Workflow
"""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.workflow import CamelMigrationWorkflow, WorkflowState, MigrationStage


class TestCamelMigrationWorkflow(unittest.TestCase):
    """Test cases for the orchestration workflow"""
    
    def setUp(self):
        self.workflow = CamelMigrationWorkflow()
        self.temp_dir = tempfile.mkdtemp()
        self.test_state = {
            "repository_url": "https://github.com/test/repo.git",
            "branch_name": "test-branch",
            "workspace_dir": self.temp_dir,
            "java_version": 17,
            "current_stage": "starting",
            "stages_completed": [],
            "error_messages": [],
            "migration_complete": False
        }
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch.object(CamelMigrationWorkflow, 'config_agent')
    def test_validate_config_node(self, mock_agent):
        """Test configuration validation node"""
        mock_validate = Mock()
        mock_validate.validate.return_value = {
            "overall_status": "Success",
            "checks": []
        }
        mock_agent.return_value = mock_validate
        self.workflow.config_agent = mock_validate
        
        result = self.workflow.validate_config_node(self.test_state)
        
        self.assertIn("config_validation", result)
        self.assertEqual(result["current_stage"], MigrationStage.CONFIG_VALIDATION.value)
        self.assertIn(MigrationStage.CONFIG_VALIDATION.value, result["stages_completed"])
    
    @patch.object(CamelMigrationWorkflow, 'git_agent')
    def test_clone_repository_node(self, mock_agent):
        """Test repository cloning node"""
        mock_git = Mock()
        mock_git.initiate_workflow.return_value = {
            "status": "Success",
            "local_path": self.temp_dir
        }
        mock_agent.return_value = mock_git
        self.workflow.git_agent = mock_git
        
        result = self.workflow.clone_repository_node(self.test_state)
        
        self.assertIn("git_status", result)
        self.assertEqual(result["current_stage"], MigrationStage.GIT_CLONE.value)
    
    @patch.object(CamelMigrationWorkflow, 'dependency_agent')
    def test_update_dependencies_node(self, mock_agent):
        """Test dependency update node"""
        mock_deps = Mock()
        mock_deps.update_project_dependencies.return_value = {
            "status": "Success",
            "removed_dependencies": ["old-dep"],
            "added_dependencies": ["new-dep"]
        }
        mock_agent.return_value = mock_deps
        self.workflow.dependency_agent = mock_deps
        
        # Create a dummy pom.xml
        pom_path = os.path.join(self.temp_dir, "pom.xml")
        with open(pom_path, 'w') as f:
            f.write("<project></project>")
        
        result = self.workflow.update_dependencies_node(self.test_state)
        
        self.assertIn("dependency_update", result)
        self.assertEqual(result["current_stage"], MigrationStage.DEPENDENCY_UPDATE.value)
    
    @patch.object(CamelMigrationWorkflow, 'dsl_agent')
    def test_convert_routes_node(self, mock_agent):
        """Test route conversion node"""
        mock_dsl = Mock()
        mock_dsl.convert_routes.return_value = {
            "status": "Success",
            "file_count": 2,
            "converted_files": ["Route1.java", "Route2.java"]
        }
        mock_agent.return_value = mock_dsl
        self.workflow.dsl_agent = mock_dsl
        
        result = self.workflow.convert_routes_node(self.test_state)
        
        self.assertIn("route_conversion", result)
        self.assertEqual(result["current_stage"], MigrationStage.ROUTE_CONVERSION.value)
    
    @patch.object(CamelMigrationWorkflow, 'service_agent')
    def test_refactor_services_node(self, mock_agent):
        """Test service refactoring node"""
        mock_service = Mock()
        mock_service.refactor_business_logic.return_value = {
            "status": "Success",
            "refactored_count": 3
        }
        mock_agent.return_value = mock_service
        self.workflow.service_agent = mock_service
        
        result = self.workflow.refactor_services_node(self.test_state)
        
        self.assertIn("service_refactoring", result)
        self.assertEqual(result["current_stage"], MigrationStage.SERVICE_REFACTOR.value)
    
    @patch.object(CamelMigrationWorkflow, 'test_agent')
    def test_run_tests_node(self, mock_agent):
        """Test validation node"""
        mock_test = Mock()
        mock_test.validate_migration.return_value = {
            "overall_status": "Success",
            "compilation_status": "Success",
            "test_run_results": "Success"
        }
        mock_agent.return_value = mock_test
        self.workflow.test_agent = mock_test
        
        result = self.workflow.run_tests_node(self.test_state)
        
        self.assertIn("test_results", result)
        self.assertEqual(result["current_stage"], MigrationStage.TESTING.value)
    
    @patch.object(CamelMigrationWorkflow, 'container_agent')
    def test_containerize_node(self, mock_agent):
        """Test containerization node"""
        mock_container = Mock()
        mock_container.containerize_application.return_value = {
            "status": "Success",
            "artifact_count": 2,
            "generated_artifacts": ["Dockerfile", ".dockerignore"]
        }
        mock_agent.return_value = mock_container
        self.workflow.container_agent = mock_container
        
        result = self.workflow.containerize_node(self.test_state)
        
        self.assertIn("containerization", result)
        self.assertEqual(result["current_stage"], MigrationStage.CONTAINERIZATION.value)
    
    @patch.object(CamelMigrationWorkflow, 'git_agent')
    def test_push_changes_node(self, mock_agent):
        """Test push changes node"""
        mock_git = Mock()
        mock_git.finalize_workflow.return_value = {
            "status": "Success",
            "pushed_branch_url": "https://github.com/test/repo/tree/test-branch"
        }
        mock_agent.return_value = mock_git
        self.workflow.git_agent = mock_git
        
        result = self.workflow.push_changes_node(self.test_state)
        
        self.assertIn("git_status", result)
        self.assertEqual(result["current_stage"], MigrationStage.GIT_PUSH.value)
        self.assertTrue(result["migration_complete"])
    
    def test_check_validation_success(self):
        """Test validation check for success"""
        state = {
            **self.test_state,
            "config_validation": {"overall_status": "Success"}
        }
        
        result = self.workflow.check_validation(state)
        
        self.assertEqual(result, "continue")
    
    def test_check_validation_failure(self):
        """Test validation check for failure"""
        state = {
            **self.test_state,
            "config_validation": {"overall_status": "Failure", "message": "Test error"},
            "error_messages": []
        }
        
        result = self.workflow.check_validation(state)
        
        self.assertEqual(result, "fail")
    
    def test_check_tests_success(self):
        """Test test check for success"""
        state = {
            **self.test_state,
            "test_results": {"compilation_status": "Success"}
        }
        
        result = self.workflow.check_tests(state)
        
        self.assertEqual(result, "continue")
    
    def test_check_tests_skip_container(self):
        """Test test check with skip containerization"""
        state = {
            **self.test_state,
            "test_results": {"compilation_status": "Success"},
            "skip_containerization": True
        }
        
        result = self.workflow.check_tests(state)
        
        self.assertEqual(result, "skip_container")
    
    def test_check_tests_failure(self):
        """Test test check for failure"""
        state = {
            **self.test_state,
            "test_results": {"compilation_status": "Failure", "message": "Compilation failed"},
            "error_messages": []
        }
        
        result = self.workflow.check_tests(state)
        
        self.assertEqual(result, "fail")
    
    def test_generate_final_report(self):
        """Test final report generation"""
        state = {
            **self.test_state,
            "migration_complete": True,
            "stages_completed": [
                MigrationStage.CONFIG_VALIDATION.value,
                MigrationStage.GIT_CLONE.value,
                MigrationStage.DEPENDENCY_UPDATE.value
            ],
            "config_validation": {"overall_status": "Success"},
            "dependency_update": {
                "status": "Success",
                "update_result": {
                    "removed_dependencies": ["old"],
                    "added_dependencies": ["new"]
                }
            }
        }
        
        report = self.workflow._generate_final_report(state)
        
        self.assertIn("CAMEL MIGRATION WORKFLOW REPORT", report)
        self.assertIn("✅ Complete", report)
        self.assertIn("Configuration:", report)
        self.assertIn("Dependencies:", report)
    
    @patch.object(CamelMigrationWorkflow, '_build_workflow')
    def test_run_workflow_mock(self, mock_build):
        """Test running the workflow with mocked components"""
        # Create a mock compiled workflow
        mock_workflow = Mock()
        mock_workflow.invoke.return_value = {
            **self.test_state,
            "migration_complete": True,
            "final_report": "Test Report"
        }
        mock_build.return_value = mock_workflow
        
        # Create workflow instance
        workflow = CamelMigrationWorkflow()
        workflow.workflow = mock_workflow
        
        # Run workflow
        result = workflow.run(
            repository_url="https://github.com/test/repo.git",
            branch_name="test-branch",
            workspace_dir=self.temp_dir
        )
        
        self.assertTrue(result.get("migration_complete"))
        self.assertEqual(result.get("final_report"), "Test Report")


class TestMigrationStage(unittest.TestCase):
    """Test cases for MigrationStage enum"""
    
    def test_stage_values(self):
        """Test that all stages have correct values"""
        self.assertEqual(MigrationStage.CONFIG_VALIDATION.value, "config_validation")
        self.assertEqual(MigrationStage.GIT_CLONE.value, "git_clone")
        self.assertEqual(MigrationStage.DEPENDENCY_UPDATE.value, "dependency_update")
        self.assertEqual(MigrationStage.ROUTE_CONVERSION.value, "route_conversion")
        self.assertEqual(MigrationStage.SERVICE_REFACTOR.value, "service_refactor")
        self.assertEqual(MigrationStage.TESTING.value, "testing")
        self.assertEqual(MigrationStage.CONTAINERIZATION.value, "containerization")
        self.assertEqual(MigrationStage.GIT_PUSH.value, "git_push")
        self.assertEqual(MigrationStage.COMPLETE.value, "complete")


if __name__ == "__main__":
    unittest.main()
