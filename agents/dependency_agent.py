"""
Dependency Agent - Updates Maven POM dependencies for Camel 4 migration
"""

import json
import os
import sys
from typing import Dict, Any, List
from crewai import Agent, Task, Crew
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
    
    def update_project_dependencies(
        self,
        pom_file_path: str,
        backup: bool = True
    ) -> Dict[str, Any]:
        """
        Update project dependencies for Camel 4 migration.
        
        Args:
            pom_file_path: Path to the project's pom.xml file
            backup: Whether to create a backup of the original file
            
        Returns:
            Dictionary with update results
        """
        # Create backup if requested
        if backup:
            import shutil
            backup_path = f"{pom_file_path}.backup"
            shutil.copy2(pom_file_path, backup_path)
        
        # Create task for dependency update
        update_task = Task(
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
        
        # Create crew and execute
        crew = Crew(
            agents=[self.agent],
            tasks=[update_task],
            verbose=True
        )
        
        try:
            # Execute the update
            result = crew.kickoff()
            
            # Perform actual update
            update_result = update_pom_dependencies(pom_file_path)
            
            # Validate the updated POM
            validation_result = validate_pom_file(pom_file_path)
            
            return {
                "status": "Success",
                "pom_file_path": pom_file_path,
                "backup_created": backup,
                "update_result": update_result,
                "validation_result": validation_result,
                "summary": self._generate_summary(update_result),
                "message": f"Successfully updated POM file with {len(update_result.get('removed_dependencies', []))} removals and {len(update_result.get('added_dependencies', []))} additions"
            }
            
        except Exception as e:
            return {
                "status": "Failure",
                "error": str(e),
                "message": f"Failed to update dependencies: {str(e)}"
            }
    
    def _generate_summary(self, update_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the update.
        
        Args:
            update_result: The update result dictionary
            
        Returns:
            Summary string
        """
        summary = []
        summary.append("Dependency Update Summary")
        summary.append("=" * 50)
        
        removed = update_result.get('removed_dependencies', [])
        if removed:
            summary.append(f"\nRemoved {len(removed)} deprecated dependencies:")
            for dep in removed[:10]:  # Show first 10
                summary.append(f"  - {dep}")
            if len(removed) > 10:
                summary.append(f"  ... and {len(removed) - 10} more")
        
        added = update_result.get('added_dependencies', [])
        if added:
            summary.append(f"\nAdded {len(added)} new dependencies:")
            for dep in added[:10]:  # Show first 10
                summary.append(f"  + {dep}")
            if len(added) > 10:
                summary.append(f"  ... and {len(added) - 10} more")
        
        updated = update_result.get('updated_dependencies', [])
        if updated:
            summary.append(f"\nUpdated {len(updated)} dependencies:")
            for update in updated[:10]:  # Show first 10
                summary.append(f"  * {update}")
            if len(updated) > 10:
                summary.append(f"  ... and {len(updated) - 10} more")
        
        return "\n".join(summary)
    
    def analyze_dependencies(self, pom_file_path: str) -> Dict[str, Any]:
        """
        Analyze current dependencies in a POM file.
        
        Args:
            pom_file_path: Path to the pom.xml file
            
        Returns:
            Dictionary with analysis results
        """
        try:
            pom_info = parse_pom_file(pom_file_path)
            
            if pom_info['status'] == 'Failure':
                return pom_info
            
            dependencies = pom_info.get('dependencies', [])
            
            # Categorize dependencies
            camel_deps = []
            spring_deps = []
            other_deps = []
            deprecated_deps = []
            
            for dep in dependencies:
                group_id = dep.get('groupId', '')
                artifact_id = dep.get('artifactId', '')
                
                if 'camel' in group_id.lower():
                    camel_deps.append(dep)
                    # Check for deprecated
                    if artifact_id in ['camel-core-osgi', 'camel-blueprint', 'camel-cdi']:
                        deprecated_deps.append(dep)
                elif 'spring' in group_id.lower():
                    spring_deps.append(dep)
                else:
                    other_deps.append(dep)
            
            # Detect Camel version
            camel_version = None
            for prop_name, prop_value in pom_info.get('properties', {}).items():
                if 'camel' in prop_name.lower() and 'version' in prop_name.lower():
                    camel_version = prop_value
                    break
            
            return {
                "status": "Success",
                "total_dependencies": len(dependencies),
                "camel_dependencies": len(camel_deps),
                "spring_dependencies": len(spring_deps),
                "other_dependencies": len(other_deps),
                "deprecated_dependencies": len(deprecated_deps),
                "current_camel_version": camel_version,
                "needs_migration": camel_version and camel_version.startswith('2.'),
                "deprecated_list": [f"{d['groupId']}:{d['artifactId']}" for d in deprecated_deps],
                "message": f"Analyzed {len(dependencies)} dependencies, found {len(camel_deps)} Camel dependencies"
            }
            
        except Exception as e:
            return {
                "status": "Failure",
                "error": str(e),
                "message": f"Failed to analyze dependencies: {str(e)}"
            }
