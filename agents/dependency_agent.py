"""
Dependency Agent - Updates Maven POM dependencies for Camel 4 migration
Refactored to separate agent and task creation from crew execution
"""

import json
import os
import sys
from typing import Dict, Any, List
from crewai import Agent, Task
from crewai.tools import tool
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.maven_tools import (
    parse_pom_file,
    update_pom_dependencies,
    validate_pom_file
)
from config.llm_config import get_llm


class DependencyAgent:
    """
    Agent responsible for updating Maven dependencies from Camel 2 to Camel 4
    Only creates agents and tasks, does not execute crews
    """
    
    def __init__(self):
        """Initialize the Dependency Agent with LLM and tools"""
        self.llm = get_llm()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompts',
            'dependency_checker_prompt.txt'
        )
        
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
        
        return Agent(
            role='Project Build Expert',
            goal='Modernize Maven POM files for Camel 4 migration',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                self.parse_pom_tool,
                self.update_dependencies_tool,
                self.validate_pom_tool
            ]
        )
    
    @tool("Parse POM File")
    def parse_pom_tool(self, pom_path: str) -> str:
        """
        Parse a Maven POM file.
        
        Args:
            pom_path: Path to the pom.xml file
            
        Returns:
            JSON string with POM information
        """
        result = parse_pom_file(pom_path)
        # Remove non-serializable elements
        if 'tree' in result:
            del result['tree']
        if 'root' in result:
            del result['root']
        if 'namespace' in result:
            del result['namespace']
        return json.dumps(result, indent=2)
    
    @tool("Update POM Dependencies")
    def update_dependencies_tool(self, pom_path: str, output_path: str = None) -> str:
        """
        Update POM dependencies from Camel 2 to Camel 4.
        
        Args:
            pom_path: Path to the input pom.xml file
            output_path: Optional output path
            
        Returns:
            JSON string with update results
        """
        result = update_pom_dependencies(pom_path, output_path)
        return json.dumps(result, indent=2)
    
    @tool("Validate POM File")
    def validate_pom_tool(self, pom_path: str) -> str:
        """
        Validate a POM file for common issues.
        
        Args:
            pom_path: Path to the pom.xml file
            
        Returns:
            JSON string with validation results
        """
        result = validate_pom_file(pom_path)
        return json.dumps(result, indent=2)
    
    def create_update_task(
        self,
        pom_file_path: str,
        backup: bool = True
    ) -> Task:
        """
        Create a task for updating project dependencies.
        
        Args:
            pom_file_path: Path to the project's pom.xml file
            backup: Whether to create a backup of the original file
            
        Returns:
            CrewAI Task for dependency update
        """
        # Create backup if requested
        if backup:
            import shutil
            backup_path = f"{pom_file_path}.backup"
            try:
                shutil.copy2(pom_file_path, backup_path)
            except Exception:
                pass  # Backup creation is optional
        
        return Task(
            description=f"""
            Update the Maven POM file for Camel 4 migration:
            1. Parse the POM file at: {pom_file_path}
            2. Identify all Camel 2.x dependencies
            3. Remove deprecated dependencies
            4. Update to Camel 4.x compatible dependencies
            5. Update Spring Boot version to 3.x
            6. Validate the updated POM file
            
            Provide a detailed report of all changes made.
            """,
            expected_output="A comprehensive report of dependency updates with removed and added dependencies",
            agent=self.agent
        )
    
    def create_scan_task(self, project_path: str) -> Task:
        """
        Create a task for scanning all POM files in a project.
        
        Args:
            project_path: Root path of the project to scan
            
        Returns:
            CrewAI Task for dependency scanning
        """
        return Task(
            description=f"""
            Scan the project for all POM files:
            1. Find all pom.xml files in: {project_path}
            2. Parse each POM file
            3. Identify Camel dependencies in each file
            4. Generate a report of all Camel dependencies found
            5. Identify which POMs need updates for Camel 4
            
            Include submodules and multi-module projects.
            """,
            expected_output="A detailed report of all POM files and their Camel dependencies",
            agent=self.agent
        )
    
    def get_dependency_mapping(self) -> Dict[str, str]:
        """
        Get the mapping of Camel 2 to Camel 4 dependencies.
        
        Returns:
            Dictionary mapping old to new dependency coordinates
        """
        return {
            "camel-core": "camel-core-model",
            "camel-http4": "camel-http",
            "camel-jetty9": "camel-jetty",
            "camel-rabbitmq": "camel-spring-rabbitmq",
            "camel-kafka": "camel-kafka",
            "camel-activemq": "camel-jms"
        }