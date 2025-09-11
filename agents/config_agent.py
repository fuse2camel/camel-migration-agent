"""
Config Agent - Validates the local system environment for Camel migration
Refactored to separate agent and task creation from crew execution
"""

import json
from typing import Dict, Any
from crewai import Agent, Task
from crewai.tools import tool
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.system_tools import validate_environment
from config.llm_config import get_llm


# Create tool function outside the class to avoid self parameter issues
@tool("Validate Environment")
def validate_environment_tool(requirements_json: str) -> str:
    """
    Validate the system environment against requirements.
    
    Args:
        requirements_json: JSON string with tool requirements
        
    Returns:
        JSON string with validation results
    """
    try:
        requirements = json.loads(requirements_json)
    except (json.JSONDecodeError, TypeError):
        requirements = {
            "java": "17",
            "maven": "3.8.0",
            "git": "Any",
            "docker": "Any"
        }
    
    result = validate_environment(requirements)
    return json.dumps(result, indent=2)


class ConfigAgent:
    """
    Agent responsible for validating the local system's environment
    Only creates agents and tasks, does not execute crews
    """
    
    def __init__(self):
        """Initialize the Config Agent with LLM and tools"""
        self.llm = get_llm()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompts',
            'config_agent_prompt.txt'
        )
        
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
        
        return Agent(
            role='Configuration Validator',
            goal='Validate that all required tools for Camel migration are properly installed and configured',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[validate_environment_tool]  # Use the standalone tool function
        )
    
    def create_validation_task(self, requirements_config: Dict[str, str] = None) -> Task:
        """
        Create a validation task for the system environment.
        
        Args:
            requirements_config: Dictionary with minimum version requirements
            
        Returns:
            CrewAI Task for validation
        """
        if requirements_config is None:
            requirements_config = {
                "java": "17",
                "maven": "3.8.0",
                "git": "Any",
                "docker": "Any"
            }
        
        return Task(
            description=f"""
            Validate the local system environment for Camel migration.
            Check that all required tools are installed and meet these requirements:
            {json.dumps(requirements_config, indent=2)}
            
            Provide a detailed report of each check.
            """,
            expected_output="A comprehensive validation report in JSON format",
            agent=self.agent
        )
    
    def get_validation_summary(self, validation_report: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the validation report.
        
        Args:
            validation_report: The validation report dictionary
            
        Returns:
            Human-readable summary string
        """
        summary = []
        summary.append(f"Environment Validation: {validation_report.get('overall_status', 'Unknown')}")
        summary.append("-" * 50)
        
        checks = validation_report.get('checks', [])
        for check in checks:
            tool_name = check.get('tool', 'Unknown')
            status = "✓" if check.get('meets_requirement', False) else "✗"
            version = check.get('current_version', 'Not installed')
            required = check.get('required_version', 'Any')
            
            summary.append(f"{status} {tool_name}:")
            summary.append(f"  Required: {required}")
            summary.append(f"  Found: {version}")
            
            if not check.get('meets_requirement', False):
                details = check.get('details', '')
                if details:
                    summary.append(f"  Details: {details}")
            summary.append("")
        
        return "\n".join(summary)