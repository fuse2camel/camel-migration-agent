"""
LangGraph Orchestration Workflow for Camel Migration
Manages the complete Camel migration process using LangGraph with CrewAI agents
"""

import os
import sys
from typing import Dict, Any, TypedDict, Annotated, Sequence, List, Optional
from enum import Enum
import operator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph.message import add_messages
from crewai import Crew
import json
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.config_agent import ConfigAgent
from agents.git_agent import GitAgent
from agents.dependency_agent import DependencyAgent
from agents.dsl_conversion_agent import DSLConversionAgent
from agents.service_refactor_agent import ServiceRefactorAgent
from agents.test_agent import TestAgent
from agents.containerization_agent import ContainerizationAgent
from config.llm_config import get_llm

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationState(TypedDict):
    """State definition for the migration workflow"""
    # Input parameters
    repository_url: str
    branch_name: str
    workspace_dir: str
    java_version: int
    
    # Workflow tracking
    current_stage: str
    stages_completed: Annotated[List[str], operator.add]
    error_messages: Annotated[List[str], operator.add]
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
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


class MigrationStage(str, Enum):
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


class CamelMigrationLangGraphWorkflow:
    """
    Orchestrates the complete Camel 2 to Camel 4 migration workflow using LangGraph
    """
    
    def __init__(self, checkpoint: bool = False):
        """
        Initialize the workflow with all agents
        
        Args:
            checkpoint: Whether to enable checkpointing for resumable workflows
        """
        # Initialize agents (they only create agents and tasks, not crews)
        self.config_agent = ConfigAgent()
        self.git_agent = GitAgent()
        self.dependency_agent = DependencyAgent()
        self.dsl_agent = DSLConversionAgent()
        self.service_agent = ServiceRefactorAgent()
        self.test_agent = TestAgent()
        self.container_agent = ContainerizationAgent()
        
        # Setup checkpointing if enabled
        self.memory = MemorySaver() if checkpoint else None
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        # Create the state graph
        workflow = StateGraph(MigrationState)
        
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
            self._check_validation,
            {
                "continue": "clone_repository",
                "error": "generate_report"
            }
        )
        
        workflow.add_conditional_edges(
            "clone_repository",
            self._check_step_success,
            {
                "continue": "update_dependencies",
                "error": "generate_report"
            }
        )
        
        workflow.add_conditional_edges(
            "update_dependencies",
            self._check_step_success,
            {
                "continue": "convert_routes",
                "error": "generate_report"
            }
        )
        
        workflow.add_conditional_edges(
            "convert_routes",
            self._check_step_success,
            {
                "continue": "refactor_services",
                "error": "generate_report"
            }
        )
        
        workflow.add_conditional_edges(
            "refactor_services",
            self._check_step_success,
            {
                "continue": "run_tests",
                "error": "generate_report"
            }
        )
        
        workflow.add_conditional_edges(
            "run_tests",
            self._check_test_results,
            {
                "continue": "containerize",
                "skip_container": "push_changes",
                "error": "generate_report"
            }
        )
        
        workflow.add_conditional_edges(
            "containerize",
            self._check_step_success,
            {
                "continue": "push_changes",
                "error": "generate_report"
            }
        )
        
        workflow.add_conditional_edges(
            "push_changes",
            self._check_step_success,
            {
                "continue": "generate_report",
                "error": "generate_report"
            }
        )
        
        # Generate report is the final step
        workflow.add_edge("generate_report", END)
        
        # Compile the workflow
        if self.memory:
            return workflow.compile(checkpointer=self.memory)
        else:
            return workflow.compile()
    
    def _check_validation(self, state: MigrationState) -> str:
        """Check if configuration validation passed"""
        if state.get("error_messages"):
            return "error"
        if state.get("config_validation", {}).get("overall_status") == "Success":
            return "continue"
        return "error"
    
    def _check_step_success(self, state: MigrationState) -> str:
        """Check if the current step completed successfully"""
        if state.get("error_messages"):
            # Check if we have critical errors
            critical_errors = [e for e in state["error_messages"] if "critical" in e.lower()]
            if critical_errors:
                return "error"
        return "continue"
    
    def _check_test_results(self, state: MigrationState) -> str:
        """Check test results and decide next step"""
        if state.get("error_messages"):
            return "error"
        test_results = state.get("test_results", {})
        if test_results.get("all_passed", False):
            return "continue"
        elif test_results.get("skip_containerization", False):
            return "skip_container"
        return "error"
    
    def _execute_crew_task(self, agent, task) -> Dict[str, Any]:
        """
        Helper method to execute a crew with single agent and task
        
        Args:
            agent: The CrewAI agent
            task: The CrewAI task
            
        Returns:
            Dictionary with execution results
        """
        try:
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )
            result = crew.kickoff()
            
            # Try to parse result as JSON if possible
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {"result": result, "status": "Success"}
            return result if isinstance(result, dict) else {"result": result}
            
        except Exception as e:
            logger.error(f"Crew execution failed: {str(e)}")
            return {"status": "Error", "error": str(e)}
    
    def validate_config_node(self, state: MigrationState) -> MigrationState:
        """Validate configuration and environment"""
        try:
            logger.info("Validating configuration...")
            
            # Create validation task
            requirements = {
                "java": str(state.get("java_version", 17)),
                "maven": "3.8.0",
                "git": "Any",
                "docker": "Any"
            }
            
            task = self.config_agent.create_validation_task(requirements)
            result = self._execute_crew_task(self.config_agent.agent, task)
            
            state["config_validation"] = result
            state["current_stage"] = MigrationStage.CONFIG_VALIDATION
            state["stages_completed"].append(MigrationStage.CONFIG_VALIDATION)
            
            if result.get("overall_status") != "Success":
                state["error_messages"].append(f"Config validation failed: {result}")
            
            state["messages"].append(
                HumanMessage(content=f"Configuration validation completed: {result.get('overall_status', 'Unknown')}")
            )
            
        except Exception as e:
            state["error_messages"].append(f"Config validation error: {str(e)}")
            state["messages"].append(HumanMessage(content=f"Error in config validation: {str(e)}"))
        
        return state
    
    def clone_repository_node(self, state: MigrationState) -> MigrationState:
        """Clone the repository and create migration branch"""
        try:
            logger.info("Cloning repository...")
            
            task = self.git_agent.create_initiate_task(
                repository_url=state["repository_url"],
                branch_name=state["branch_name"],
                workspace_dir=state["workspace_dir"]
            )
            
            result = self._execute_crew_task(self.git_agent.agent, task)
            
            state["git_status"] = result
            state["current_stage"] = MigrationStage.GIT_CLONE
            state["stages_completed"].append(MigrationStage.GIT_CLONE)
            
            if result.get("status") != "Success":
                state["error_messages"].append(f"Git clone failed: {result}")
            
            state["messages"].append(
                HumanMessage(content=f"Repository cloned to: {state['workspace_dir']}")
            )
            
        except Exception as e:
            state["error_messages"].append(f"Git clone error: {str(e)}")
            state["messages"].append(HumanMessage(content=f"Error cloning repository: {str(e)}"))
        
        return state
    
    def update_dependencies_node(self, state: MigrationState) -> MigrationState:
        """Update Maven dependencies"""
        try:
            logger.info("Updating dependencies...")
            
            pom_path = os.path.join(state["workspace_dir"], "pom.xml")
            task = self.dependency_agent.create_update_task(pom_path)
            
            result = self._execute_crew_task(self.dependency_agent.agent, task)
            
            state["dependency_update"] = result
            state["current_stage"] = MigrationStage.DEPENDENCY_UPDATE
            state["stages_completed"].append(MigrationStage.DEPENDENCY_UPDATE)
            
            state["messages"].append(
                HumanMessage(content="Dependencies updated for Camel 4")
            )
            
        except Exception as e:
            state["error_messages"].append(f"Dependency update error: {str(e)}")
            state["messages"].append(HumanMessage(content=f"Error updating dependencies: {str(e)}"))
        
        return state
    
    def convert_routes_node(self, state: MigrationState) -> MigrationState:
        """Convert Camel routes to modern Java DSL"""
        try:
            logger.info("Converting routes...")
            
            task = self.dsl_agent.create_conversion_task(state["workspace_dir"])
            result = self._execute_crew_task(self.dsl_agent.agent, task)
            
            state["route_conversion"] = result
            state["current_stage"] = MigrationStage.ROUTE_CONVERSION
            state["stages_completed"].append(MigrationStage.ROUTE_CONVERSION)
            
            state["messages"].append(
                HumanMessage(content="Routes converted to Camel 4 Java DSL")
            )
            
        except Exception as e:
            state["error_messages"].append(f"Route conversion error: {str(e)}")
            state["messages"].append(HumanMessage(content=f"Error converting routes: {str(e)}"))
        
        return state
    
    def refactor_services_node(self, state: MigrationState) -> MigrationState:
        """Refactor Java services for Camel 4"""
        try:
            logger.info("Refactoring services...")
            
            task = self.service_agent.create_refactor_task(state["workspace_dir"])
            result = self._execute_crew_task(self.service_agent.agent, task)
            
            state["service_refactoring"] = result
            state["current_stage"] = MigrationStage.SERVICE_REFACTOR
            state["stages_completed"].append(MigrationStage.SERVICE_REFACTOR)
            
            state["messages"].append(
                HumanMessage(content="Services refactored for Camel 4")
            )
            
        except Exception as e:
            state["error_messages"].append(f"Service refactor error: {str(e)}")
            state["messages"].append(HumanMessage(content=f"Error refactoring services: {str(e)}"))
        
        return state
    
    def run_tests_node(self, state: MigrationState) -> MigrationState:
        """Run tests to validate migration"""
        try:
            logger.info("Running tests...")
            
            task = self.test_agent.create_test_task(state["workspace_dir"])
            result = self._execute_crew_task(self.test_agent.agent, task)
            
            state["test_results"] = result
            state["current_stage"] = MigrationStage.TESTING
            state["stages_completed"].append(MigrationStage.TESTING)
            
            # Determine if we should skip containerization based on test results
            if result.get("status") == "Warning":
                result["skip_containerization"] = True
            
            state["messages"].append(
                HumanMessage(content=f"Tests completed: {result.get('summary', 'No summary')}")
            )
            
        except Exception as e:
            state["error_messages"].append(f"Test execution error: {str(e)}")
            state["messages"].append(HumanMessage(content=f"Error running tests: {str(e)}"))
        
        return state
    
    def containerize_node(self, state: MigrationState) -> MigrationState:
        """Generate containerization artifacts"""
        try:
            logger.info("Generating container artifacts...")
            
            task = self.container_agent.create_containerization_task(state["workspace_dir"])
            result = self._execute_crew_task(self.container_agent.agent, task)
            
            state["containerization"] = result
            state["current_stage"] = MigrationStage.CONTAINERIZATION
            state["stages_completed"].append(MigrationStage.CONTAINERIZATION)
            
            state["messages"].append(
                HumanMessage(content="Container artifacts generated")
            )
            
        except Exception as e:
            state["error_messages"].append(f"Containerization error: {str(e)}")
            state["messages"].append(HumanMessage(content=f"Error in containerization: {str(e)}"))
        
        return state
    
    def push_changes_node(self, state: MigrationState) -> MigrationState:
        """Commit and push changes to remote repository"""
        try:
            logger.info("Pushing changes...")
            
            task = self.git_agent.create_finalize_task(
                source_code_path=state["workspace_dir"],
                commit_message="Migrate from Apache Camel 2 to Camel 4",
                branch_name=state["branch_name"]
            )
            
            result = self._execute_crew_task(self.git_agent.agent, task)
            
            state["git_status"] = result
            state["current_stage"] = MigrationStage.GIT_PUSH
            state["stages_completed"].append(MigrationStage.GIT_PUSH)
            
            state["messages"].append(
                HumanMessage(content=f"Changes pushed to branch: {state['branch_name']}")
            )
            
        except Exception as e:
            state["error_messages"].append(f"Git push error: {str(e)}")
            state["messages"].append(HumanMessage(content=f"Error pushing changes: {str(e)}"))
        
        return state
    
    def generate_report_node(self, state: MigrationState) -> MigrationState:
        """Generate final migration report"""
        try:
            logger.info("Generating migration report...")
            
            # Build the report
            report = []
            report.append("=" * 60)
            report.append("CAMEL MIGRATION REPORT")
            report.append("=" * 60)
            report.append(f"\nRepository: {state['repository_url']}")
            report.append(f"Branch: {state['branch_name']}")
            report.append(f"Workspace: {state['workspace_dir']}")
            report.append("\n" + "-" * 60)
            report.append("STAGES COMPLETED:")
            report.append("-" * 60)
            
            for stage in state.get("stages_completed", []):
                report.append(f"✓ {stage}")
            
            if state.get("error_messages"):
                report.append("\n" + "-" * 60)
                report.append("ERRORS ENCOUNTERED:")
                report.append("-" * 60)
                for error in state["error_messages"]:
                    report.append(f"✗ {error}")
            
            # Add test results summary
            if state.get("test_results"):
                report.append("\n" + "-" * 60)
                report.append("TEST RESULTS:")
                report.append("-" * 60)
                test_results = state["test_results"]
                report.append(f"Status: {test_results.get('status', 'Unknown')}")
                if test_results.get("summary"):
                    report.append(f"Summary: {test_results['summary']}")
            
            # Determine overall status
            if state.get("error_messages"):
                overall_status = "FAILED"
            elif len(state.get("stages_completed", [])) >= 7:
                overall_status = "SUCCESS"
            else:
                overall_status = "PARTIAL"
            
            report.append("\n" + "=" * 60)
            report.append(f"OVERALL STATUS: {overall_status}")
            report.append("=" * 60)
            
            final_report = "\n".join(report)
            state["final_report"] = final_report
            state["migration_complete"] = overall_status == "SUCCESS"
            state["current_stage"] = MigrationStage.COMPLETE
            
            # Save report to file
            report_path = os.path.join(state["workspace_dir"], "migration-report.txt")
            try:
                with open(report_path, "w") as f:
                    f.write(final_report)
                state["messages"].append(
                    HumanMessage(content=f"Migration report saved to: {report_path}")
                )
            except Exception:
                pass
            
            state["messages"].append(HumanMessage(content=f"Migration {overall_status}"))
            
        except Exception as e:
            state["error_messages"].append(f"Report generation error: {str(e)}")
            state["final_report"] = f"Error generating report: {str(e)}"
        
        return state
    
    def run_migration(
        self,
        repository_url: str,
        branch_name: str = "feature/camel4-migration",
        workspace_dir: str = "/tmp/camel-migration",
        java_version: int = 17,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the complete migration workflow
        
        Args:
            repository_url: URL of the repository to migrate
            branch_name: Name for the migration branch
            workspace_dir: Directory to clone the repository to
            java_version: Target Java version
            thread_id: Optional thread ID for resumable workflows
            
        Returns:
            Dictionary with migration results
        """
        # Initialize state
        initial_state = {
            "repository_url": repository_url,
            "branch_name": branch_name,
            "workspace_dir": workspace_dir,
            "java_version": java_version,
            "current_stage": "",
            "stages_completed": [],
            "error_messages": [],
            "messages": [],
            "config_validation": {},
            "git_status": {},
            "dependency_update": {},
            "route_conversion": {},
            "service_refactoring": {},
            "test_results": {},
            "containerization": {},
            "migration_complete": False,
            "final_report": ""
        }
        
        # Configure execution
        config = {}
        if thread_id and self.memory:
            config["configurable"] = {"thread_id": thread_id}
        
        # Execute workflow
        try:
            final_state = self.workflow.invoke(initial_state, config)
            
            return {
                "success": final_state.get("migration_complete", False),
                "report": final_state.get("final_report", ""),
                "stages_completed": final_state.get("stages_completed", []),
                "errors": final_state.get("error_messages", []),
                "workspace": final_state.get("workspace_dir", ""),
                "branch": final_state.get("branch_name", "")
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "report": f"Migration failed: {str(e)}"
            }
    
    def get_workflow_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a workflow (for resumable workflows)
        
        Args:
            thread_id: Thread ID to retrieve state for
            
        Returns:
            Current workflow state or None if not found
        """
        if not self.memory:
            return None
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = self.workflow.get_state(config)
            return state.values if state else None
        except Exception:
            return None
    
    def visualize_workflow(self) -> str:
        """
        Generate a visual representation of the workflow
        
        Returns:
            ASCII representation of the workflow
        """
        visualization = """
        Camel Migration Workflow (LangGraph)
        =====================================
        
        [Start]
           |
           v
        [Config Validation] --error--> [Generate Report]
           |
           v
        [Clone Repository] --error--> [Generate Report]
           |
           v
        [Update Dependencies] --error--> [Generate Report]
           |
           v
        [Convert Routes] --error--> [Generate Report]
           |
           v
        [Refactor Services] --error--> [Generate Report]
           |
           v
        [Run Tests] --error--> [Generate Report]
           |     |
           |     skip
           |     |
           v     v
        [Containerize] --> [Push Changes]
           |                    |
           error                |
           |                    |
           v                    v
        [Generate Report] <------
           |
           v
        [End]
        
        Each step:
        - Uses CrewAI agents for task execution
        - Updates the shared state
        - Can trigger error handling
        - Supports checkpointing for resume
        """
        return visualization