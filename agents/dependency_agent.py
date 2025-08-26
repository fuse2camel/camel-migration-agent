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


def dependency_agent(state):
    """
    Dependency agent function for LangGraph workflow compatibility.
    Updates Maven dependencies from Fuse6/7 to Red Hat build of Camel 4.10.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with dependency migration results
    """
    try:
        # Get git repository path from previous git_agent
        git_repo_path = state.get("artifacts", {}).get("git_repo_path")
        if not git_repo_path:
            return {"error": "Git repository path not found from git_agent"}
        
        # Initialize dependency agent
        agent = DependencyAgent()
        
        # Find POM files in the repository
        import os
        pom_files = []
        for root, dirs, files in os.walk(git_repo_path):
            for file in files:
                if file == "pom.xml":
                    pom_files.append(os.path.join(root, file))
        
        if not pom_files:
            return {"error": "No pom.xml files found in the repository"}
        
        tasks_completed = list(state.get("tasks_completed", []))
        artifacts = dict(state.get("artifacts", {}))
        
        # Update each POM file
        updated_poms = []
        for pom_file in pom_files:
            try:
                # Read current POM content
                with open(pom_file, 'r') as f:
                    pom_content = f.read()
                
                # Apply Red Hat Camel 4.10 dependency updates
                updated_content = update_camel_dependencies_to_redhat_4_10(pom_content)
                
                # Write updated content
                if updated_content != pom_content:
                    with open(pom_file, 'w') as f:
                        f.write(updated_content)
                    updated_poms.append(pom_file)
                    tasks_completed.append(f"Updated dependencies in: {os.path.relpath(pom_file, git_repo_path)}")
                
            except Exception as e:
                tasks_completed.append(f"Error updating {os.path.relpath(pom_file, git_repo_path)}: {str(e)}")
        
        if updated_poms:
            tasks_completed.append(f"Successfully updated {len(updated_poms)} POM files for Red Hat Camel 4.10")
        else:
            tasks_completed.append("No dependency updates needed")
        
        artifacts.update({
            "dependency_migration": {
                "pom_files_found": len(pom_files),
                "pom_files_updated": len(updated_poms),
                "updated_files": updated_poms
            }
        })
        
        return {
            "tasks_completed": tasks_completed,
            "artifacts": artifacts
        }
        
    except Exception as e:
        return {"error": f"Dependency agent failed: {str(e)}"}


def update_camel_dependencies_to_redhat_4_10(pom_content: str) -> str:
    """
    Update POM content from Fuse6/7 dependencies to Red Hat build of Camel 4.10
    Based on Red Hat documentation: https://docs.redhat.com/en/documentation/red_hat_build_of_apache_camel/4.10
    """
    import re
    
    updated_content = pom_content
    
    # Update parent POM to Red Hat Camel Spring Boot BOM
    parent_pattern = r'<parent>\s*<groupId>org\.apache\.camel\.springboot</groupId>\s*<artifactId>camel-spring-boot-bom</artifactId>\s*<version>[^<]+</version>\s*</parent>'
    redhat_parent = '''<parent>
        <groupId>com.redhat.camel.springboot</groupId>
        <artifactId>camel-spring-boot-bom</artifactId>
        <version>4.10.0.redhat-00001</version>
        <relativePath/>
    </parent>'''
    
    if re.search(parent_pattern, updated_content, re.MULTILINE):
        updated_content = re.sub(parent_pattern, redhat_parent, updated_content, flags=re.MULTILINE)
    
    # Update dependency management section
    bom_pattern = r'<dependencyManagement>.*?</dependencyManagement>'
    redhat_bom = '''<dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>com.redhat.camel.springboot</groupId>
                <artifactId>camel-spring-boot-bom</artifactId>
                <version>4.10.0.redhat-00001</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>'''
    
    if re.search(bom_pattern, updated_content, re.MULTILINE | re.DOTALL):
        updated_content = re.sub(bom_pattern, redhat_bom, updated_content, flags=re.MULTILINE | re.DOTALL)
    
    # Update specific Camel dependencies to Red Hat versions
    dependency_mappings = {
        r'<groupId>org\.apache\.camel</groupId>\s*<artifactId>camel-core</artifactId>': 
            '<groupId>org.apache.camel</groupId>\n            <artifactId>camel-core</artifactId>',
        r'<groupId>org\.apache\.camel</groupId>\s*<artifactId>camel-http4</artifactId>': 
            '<groupId>org.apache.camel</groupId>\n            <artifactId>camel-http</artifactId>',
        r'<groupId>org\.apache\.camel</groupId>\s*<artifactId>camel-jetty9</artifactId>': 
            '<groupId>org.apache.camel</groupId>\n            <artifactId>camel-jetty</artifactId>',
        r'<groupId>org\.apache\.camel</groupId>\s*<artifactId>camel-rabbitmq</artifactId>': 
            '<groupId>org.apache.camel</groupId>\n            <artifactId>camel-spring-rabbitmq</artifactId>'
    }
    
    for old_pattern, new_dependency in dependency_mappings.items():
        updated_content = re.sub(old_pattern, new_dependency, updated_content, flags=re.MULTILINE)
    
    # Update Camel version properties
    version_pattern = r'<camel\.version>[^<]+</camel\.version>'
    if re.search(version_pattern, updated_content):
        updated_content = re.sub(version_pattern, '<camel.version>4.10.0.redhat-00001</camel.version>', updated_content)
    
    # Add Red Hat repositories if not present
    if '<repositories>' not in updated_content:
        repo_section = '''
    <repositories>
        <repository>
            <id>redhat-ga</id>
            <name>Red Hat GA Repository</name>
            <url>https://maven.repository.redhat.com/ga/</url>
            <releases>
                <enabled>true</enabled>
            </releases>
            <snapshots>
                <enabled>false</enabled>
            </snapshots>
        </repository>
    </repositories>'''
        
        # Insert before </project>
        updated_content = updated_content.replace('</project>', repo_section + '\n</project>')
    
    return updated_content