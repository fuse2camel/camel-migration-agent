"""
Orchestration Workflow using LangGraph
Manages the complete Camel migration process
"""

import os
import sys
from typing import Dict, Any, TypedDict, Annotated, Sequence, List
from enum import Enum
import operator
from langgraph.graph import StateGraph, END
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.config_agent import ConfigAgent
from agents.git_agent import GitAgent
from agents.dependency_agent import DependencyAgent
from agents.dsl_conversion_agent import DSLConversionAgent
from agents.service_refactor_agent import ServiceRefactorAgent
from agents.test_agent import TestAgent
from agents.containerization_agent import ContainerizationAgent


class WorkflowState(TypedDict):
    """State definition for the workflow"""
    # Input parameters
    repository_url: str
    branch_name: str
    workspace_dir: str
    java_version: int
    
    # Workflow state
    current_stage: str
    stages_completed: Annotated[Sequence[str], operator.add]
    error_messages: Annotated[Sequence[str], operator.add]
    
    # Agent outputs
    config_validation: Dict[str, Any]
    git_status: Dict[str, Any]
    dependency_update: Dict[str, Any]
    route_conversion: Dict[str, Any]
    service_refactoring: Dict[str, Any]
    test_results: Dict[str, Any]
    containerization: Dict[str, Any]
    
    # Final output
    migration_complete: bool
    final_report: str


class MigrationStage(Enum):
    """Enum for migration stages"""
    CONFIG_VALIDATION = "config_validation"
    GIT_CLONE = "git_clone"
    DEPENDENCY_UPDATE = "dependency_update"
    ROUTE_CONVERSION = "route_conversion"
    SERVICE_REFACTOR = "service_refactor"
    TESTING = "testing"
    CONTAINERIZATION = "containerization"
    GIT_PUSH = "git_push"
    COMPLETE = "complete"


class CamelMigrationWorkflow:
    """
    Orchestrates the complete Camel 2 to Camel 4 migration workflow
    """
    
    def __init__(self):
        """Initialize the workflow with all agents"""
        self.config_agent = ConfigAgent()
        self.git_agent = GitAgent()
        self.dependency_agent = DependencyAgent()
        self.dsl_agent = DSLConversionAgent()
        self.service_agent = ServiceRefactorAgent()
        self.test_agent = TestAgent()
        self.container_agent = ContainerizationAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each stage
        workflow.add_node("validate_config", self.validate_config_node)
        workflow.add_node("clone_repository", self.clone_repository_node)
        workflow.add_node("update_dependencies", self.update_dependencies_node)
        workflow.add_node("convert_routes", self.convert_routes_node)
        workflow.add_node("refactor_services", self.refactor_services_node)
        workflow.add_node("run_tests", self.run_tests_node)
        workflow.add_node("containerize", self.containerize_node)
        workflow.add_node("push_changes", self.push_changes_node)
        workflow.add_node("generate_report", self.generate_report_node)
        
        # Define the workflow edges
        workflow.set_entry_point("validate_config")
        
        # Add conditional edges based on success/failure
        workflow.add_conditional_edges(
            "validate_config",
            self.check_validation,
            {
                "continue": "clone_repository",
                "fail": "generate_report"
            }
        )
        
        workflow.add_edge("clone_repository", "update_dependencies")
        workflow.add_edge("update_dependencies", "convert_routes")
        workflow.add_edge("convert_routes", "refactor_services")
        workflow.add_edge("refactor_services", "run_tests")
        
        workflow.add_conditional_edges(
            "run_tests",
            self.check_tests,
            {
                "continue": "containerize",
                "skip_container": "push_changes",
                "fail": "generate_report"
            }
        )
        
        workflow.add_edge("containerize", "push_changes")
        workflow.add_edge("push_changes", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    def validate_config_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Validate system configuration"""
        print("\n🔍 Stage 1: Validating System Configuration...")
        
        requirements = {
            "java": str(state.get("java_version", 17)),
            "maven": "3.8.0",
            "git": "Any",
            "docker": "Any"
        }
        
        validation_result = self.config_agent.validate(requirements)
        
        return {
            "config_validation": validation_result,
            "current_stage": MigrationStage.CONFIG_VALIDATION.value,
            "stages_completed": [MigrationStage.CONFIG_VALIDATION.value]
        }
    
    def clone_repository_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Clone the repository and create migration branch"""
        print("\n📥 Stage 2: Cloning Repository...")
        
        git_result = self.git_agent.initiate_workflow(
            repository_url=state["repository_url"],
            branch_name=state.get("branch_name", "feature/camel4-migration"),
            workspace_dir=state.get("workspace_dir", "/tmp/camel-migration")
        )
        
        return {
            "git_status": git_result,
            "workspace_dir": git_result.get("local_path", state.get("workspace_dir")),
            "current_stage": MigrationStage.GIT_CLONE.value,
            "stages_completed": [MigrationStage.GIT_CLONE.value]
        }
    
    def update_dependencies_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Update Maven dependencies"""
        print("\n📦 Stage 3: Updating Dependencies...")
        
        workspace = state.get("workspace_dir", "/tmp/camel-migration")
        pom_path = os.path.join(workspace, "pom.xml")
        
        dependency_result = self.dependency_agent.update_project_dependencies(pom_path)
        
        return {
            "dependency_update": dependency_result,
            "current_stage": MigrationStage.DEPENDENCY_UPDATE.value,
            "stages_completed": [MigrationStage.DEPENDENCY_UPDATE.value]
        }
    
    def convert_routes_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Convert Camel routes to Java DSL"""
        print("\n🔄 Stage 4: Converting Routes...")
        
        workspace = state.get("workspace_dir", "/tmp/camel-migration")
        
        conversion_result = self.dsl_agent.convert_routes(
            source_code_path=workspace,
            package_name="com.example.routes.migrated"
        )
        
        return {
            "route_conversion": conversion_result,
            "current_stage": MigrationStage.ROUTE_CONVERSION.value,
            "stages_completed": [MigrationStage.ROUTE_CONVERSION.value]
        }
    
    def refactor_services_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Refactor service classes"""
        print("\n♻️ Stage 5: Refactoring Services...")
        
        workspace = state.get("workspace_dir", "/tmp/camel-migration")
        
        refactor_result = self.service_agent.refactor_business_logic(workspace)
        
        return {
            "service_refactoring": refactor_result,
            "current_stage": MigrationStage.SERVICE_REFACTOR.value,
            "stages_completed": [MigrationStage.SERVICE_REFACTOR.value]
        }
    
    def run_tests_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Run tests to validate migration"""
        print("\n✅ Stage 6: Running Tests...")
        
        workspace = state.get("workspace_dir", "/tmp/camel-migration")
        
        test_result = self.test_agent.validate_migration(workspace, run_full_tests=False)
        
        return {
            "test_results": test_result,
            "current_stage": MigrationStage.TESTING.value,
            "stages_completed": [MigrationStage.TESTING.value]
        }
    
    def containerize_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Containerize the application"""
        print("\n🐳 Stage 7: Creating Docker Configuration...")
        
        workspace = state.get("workspace_dir", "/tmp/camel-migration")
        
        container_result = self.container_agent.containerize_application(
            project_root_path=workspace,
            app_name="camel-app",
            java_version=state.get("java_version", 17),
            build_image=False
        )
        
        return {
            "containerization": container_result,
            "current_stage": MigrationStage.CONTAINERIZATION.value,
            "stages_completed": [MigrationStage.CONTAINERIZATION.value]
        }
    
    def push_changes_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Push changes back to repository"""
        print("\n📤 Stage 8: Pushing Changes...")
        
        workspace = state.get("workspace_dir", "/tmp/camel-migration")
        
        push_result = self.git_agent.finalize_workflow(
            source_code_path=workspace,
            commit_message="Migrate from Apache Camel 2 to Camel 4",
            branch_name=state.get("branch_name")
        )
        
        return {
            "git_status": push_result,
            "current_stage": MigrationStage.GIT_PUSH.value,
            "stages_completed": [MigrationStage.GIT_PUSH.value],
            "migration_complete": True
        }
    
    def generate_report_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate final migration report"""
        print("\n📊 Generating Final Report...")
        
        report = self._generate_final_report(state)
        
        return {
            "final_report": report,
            "current_stage": MigrationStage.COMPLETE.value,
            "stages_completed": [MigrationStage.COMPLETE.value]
        }
    
    def check_validation(self, state: WorkflowState) -> str:
        """Check if configuration validation passed"""
        validation = state.get("config_validation", {})
        if validation.get("overall_status") == "Success":
            return "continue"
        else:
            state["error_messages"] = [f"Configuration validation failed: {validation.get('message', 'Unknown error')}"]
            return "fail"
    
    def check_tests(self, state: WorkflowState) -> str:
        """Check if tests passed"""
        test_results = state.get("test_results", {})
        if test_results.get("compilation_status") == "Success":
            # Check if containerization should be skipped
            if state.get("skip_containerization", False):
                return "skip_container"
            return "continue"
        else:
            state["error_messages"] = [f"Tests failed: {test_results.get('message', 'Unknown error')}"]
            return "fail"
    
    def _generate_final_report(self, state: WorkflowState) -> str:
        """Generate a comprehensive final report"""
        report = []
        report.append("=" * 70)
        report.append("CAMEL MIGRATION WORKFLOW REPORT")
        report.append("=" * 70)
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Repository: {state.get('repository_url', 'N/A')}")
        report.append(f"Branch: {state.get('branch_name', 'N/A')}")
        report.append(f"Workspace: {state.get('workspace_dir', 'N/A')}")
        report.append(f"Migration Status: {'✅ Complete' if state.get('migration_complete') else '❌ Failed'}")
        report.append("")
        
        # Stages completed
        report.append("STAGES COMPLETED")
        report.append("-" * 40)
        for stage in state.get("stages_completed", []):
            report.append(f"✓ {stage}")
        report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS")
        report.append("-" * 40)
        
        # Config validation
        if "config_validation" in state:
            config = state["config_validation"]
            report.append(f"1. Configuration: {config.get('overall_status', 'N/A')}")
        
        # Dependency update
        if "dependency_update" in state:
            deps = state["dependency_update"]
            report.append(f"2. Dependencies: {deps.get('status', 'N/A')}")
            if deps.get('status') == 'Success':
                update_result = deps.get('update_result', {})
                report.append(f"   - Removed: {len(update_result.get('removed_dependencies', []))} dependencies")
                report.append(f"   - Added: {len(update_result.get('added_dependencies', []))} dependencies")
        
        # Route conversion
        if "route_conversion" in state:
            routes = state["route_conversion"]
            report.append(f"3. Route Conversion: {routes.get('status', 'N/A')}")
            if routes.get('status') == 'Success':
                report.append(f"   - Converted: {routes.get('file_count', 0)} route files")
        
        # Service refactoring
        if "service_refactoring" in state:
            services = state["service_refactoring"]
            report.append(f"4. Service Refactoring: {services.get('status', 'N/A')}")
            if services.get('status') == 'Success':
                report.append(f"   - Refactored: {services.get('refactored_count', 0)} Java files")
        
        # Tests
        if "test_results" in state:
            tests = state["test_results"]
            report.append(f"5. Testing: {tests.get('overall_status', 'N/A')}")
            report.append(f"   - Compilation: {tests.get('compilation_status', 'N/A')}")
            report.append(f"   - Tests: {tests.get('test_run_results', 'N/A')}")
        
        # Containerization
        if "containerization" in state:
            container = state["containerization"]
            report.append(f"6. Containerization: {container.get('status', 'N/A')}")
            if container.get('status') == 'Success':
                report.append(f"   - Artifacts: {container.get('artifact_count', 0)} files generated")
        
        # Git push
        if state.get("migration_complete"):
            report.append(f"7. Git Push: Success")
            git_status = state.get("git_status", {})
            if git_status.get("pushed_branch_url"):
                report.append(f"   - Branch URL: {git_status['pushed_branch_url']}")
        
        # Errors
        errors = state.get("error_messages", [])
        if errors:
            report.append("")
            report.append("ERRORS")
            report.append("-" * 40)
            for error in errors:
                report.append(f"❌ {error}")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def run(
        self,
        repository_url: str,
        branch_name: str = "feature/camel4-migration",
        workspace_dir: str = "/tmp/camel-migration",
        java_version: int = 17,
        skip_containerization: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete migration workflow.
        
        Args:
            repository_url: URL of the repository to migrate
            branch_name: Name for the migration branch
            workspace_dir: Local directory for the migration
            java_version: Target Java version
            skip_containerization: Whether to skip containerization
            
        Returns:
            Final workflow state with all results
        """
        initial_state = {
            "repository_url": repository_url,
            "branch_name": branch_name,
            "workspace_dir": workspace_dir,
            "java_version": java_version,
            "skip_containerization": skip_containerization,
            "current_stage": "starting",
            "stages_completed": [],
            "error_messages": [],
            "migration_complete": False
        }
        
        print(f"\n🚀 Starting Camel Migration Workflow")
        print(f"   Repository: {repository_url}")
        print(f"   Branch: {branch_name}")
        print(f"   Workspace: {workspace_dir}")
        print(f"   Java Version: {java_version}")
        print("")
        
        try:
            # Run the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Print the final report
            print("\n" + final_state.get("final_report", "No report generated"))
            
            # Save report to file
            report_file = os.path.join(workspace_dir, "migration-report.txt")
            with open(report_file, 'w') as f:
                f.write(final_state.get("final_report", ""))
            print(f"\nReport saved to: {report_file}")
            
            return final_state
            
        except Exception as e:
            print(f"\n❌ Workflow failed with error: {str(e)}")
            return {
                **initial_state,
                "error": str(e),
                "migration_complete": False
            }
