"""
Simplified Config Agent - Validates the local system environment for Camel migration
"""
from typing import Dict, Any
from crewai import Task
from agents.base_agent import BaseAgent
from tools.system_tools import validate_environment


class ConfigAgent(BaseAgent):
    """
    Agent responsible for validating the local system's environment
    """
    
    def __init__(self):
        """Initialize the Config Agent"""
        super().__init__(
            role='Configuration Validator',
            goal='Validate that all required tools for Camel migration are properly installed and configured',
            backstory="""You are an expert system administrator responsible for validating 
                        that the local environment has all necessary tools and configurations 
                        for performing a Camel 2 to Camel 4 migration.""",
            verbose=True
        )
        
        # Add tools
        self.agent.tools = [validate_environment]
    
    def create_validation_task(self, requirements: Dict[str, str] = None) -> Task:
        """
        Create a validation task
        
        Args:
            requirements: Dictionary of tool requirements (e.g., {"java": "17", "maven": "3.8.0"})
        
        Returns:
            CrewAI Task for validation
        """
        if requirements is None:
            requirements = {
                "java": "17",
                "maven": "3.8.0",
                "git": "Any",
                "docker": "Any"
            }
        
        return Task(
            description=f"""
            Validate the local system environment for Camel migration.
            Check that all required tools are installed and meet these requirements:
            {requirements}
            
            Provide a detailed report of each check.
            """,
            agent=self.agent,
            expected_output="JSON report with validation results for each tool"
        )
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of validation results
        
        Args:
            validation_result: Dictionary with validation results
            
        Returns:
            Formatted string summary
        """
        summary = []
        
        if isinstance(validation_result, dict):
            overall_status = validation_result.get("overall_status", "Unknown")
            summary.append(f"Overall Status: {overall_status}")
            
            if "checks" in validation_result:
                summary.append("\nIndividual Checks:")
                for check, status in validation_result["checks"].items():
                    summary.append(f"  - {check}: {status}")
            
            if "message" in validation_result:
                summary.append(f"\nMessage: {validation_result['message']}")
        else:
            summary.append(f"Result: {str(validation_result)}")
        
        return "\n".join(summary)