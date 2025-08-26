"""
Service Refactor Agent - Refactors Java business logic for Camel 4 compatibility
"""

import json
import os
import sys
from typing import Dict, Any, List
from crewai import Agent, Task
from crewai.tools import tool
from pathlib import Path
import glob

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.code_tools import (
    refactor_java_code,
    analyze_java_files
)
from config.llm_config import get_llm


class ServiceRefactorAgent:
    """
    Agent responsible for refactoring Java business logic for Camel 4 compatibility
    """
    
    def __init__(self):
        """Initialize the Service Refactor Agent with LLM and tools"""
        self.llm = get_llm()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompts',
            'service_refactor_prompt.txt'
        )
        
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
        
        return Agent(
            role='Business Logic Updater',
            goal='Refactor Java classes for Camel 4 API compatibility',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                self.refactor_java_tool,
                self.analyze_java_tool,
                self.generate_processor_tool
            ]
        )
    
    @tool("Refactor Java Code")
    def refactor_java_tool(self, java_file_path: str, output_path: str = None) -> str:
        """
        Refactor Java code from Camel 2 to Camel 4.
        
        Args:
            java_file_path: Path to the Java file
            output_path: Optional output path
            
        Returns:
            JSON string with refactoring results
        """
        result = refactor_java_code(java_file_path, output_path)
        return json.dumps(result, indent=2)
    
    @tool("Analyze Java Files")
    def analyze_java_tool(self, directory_path: str) -> str:
        """
        Analyze Java files for Camel usage patterns.
        
        Args:
            directory_path: Directory to analyze
            
        Returns:
            JSON string with analysis results
        """
        result = analyze_java_files(directory_path)
        return json.dumps(result, indent=2)
    
    @tool("Generate Modern Processor")
    def generate_processor_tool(self, class_name: str, package_name: str, logic: str) -> str:
        """
        Generate a modern Camel 4 processor template.
        
        Args:
            class_name: Name of the processor class
            package_name: Package name
            logic: Business logic description
            
        Returns:
            Generated Java code
        """
        template = f"""package {package_name};

import org.apache.camel.Exchange;
import org.apache.camel.Processor;
import org.springframework.stereotype.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component("{class_name.lower()}")
public class {class_name} implements Processor {{
    
    private static final Logger LOG = LoggerFactory.getLogger({class_name}.class);
    
    @Override
    public void process(Exchange exchange) throws Exception {{
        // Get message (Camel 4 style)
        var message = exchange.getMessage();
        
        // Get body
        String body = message.getBody(String.class);
        
        // Business logic: {logic}
        // TODO: Implement actual business logic
        
        // Set response
        message.setBody(body);
        
        LOG.debug("Processed message in {class_name}");
    }}
}}"""
        return template
    
    def create_refactor_task(
        self,
        source_code_path: str,
        backup: bool = True
    ) -> Task:
        """
        Create a task for refactoring Java business logic for Camel 4 compatibility.
        
        Args:
            source_code_path: Path to the source code directory
            backup: Whether to create backups of original files
            
        Returns:
            CrewAI Task for service refactoring
        """
        # Optionally analyze the codebase first
        try:
            analysis = analyze_java_files(source_code_path)
            file_count = analysis.get('camel_file_count', 'unknown')
        except Exception:
            file_count = 'unknown'
        
        return Task(
            description=f"""
            Refactor Java business logic for Camel 4 compatibility:
            1. Analyze Java files in: {source_code_path}
            2. Identify Processor implementations
            3. Identify Bean components and Transformers
            4. Update Exchange API usage (getIn() -> getMessage())
            5. Update deprecated method calls
            6. Fix imports for relocated classes
            7. Ensure Spring annotations are correct
            
            Found {file_count} Camel-related files to refactor.
            
            Make sure all business logic remains intact while updating to Camel 4 APIs.
            """,
            expected_output="A report of all refactored files with changes made",
            agent=self.agent
        )
        
        try:
            # Execute the refactoring
            result = crew.kickoff()
            
            # Perform actual refactoring
            refactored_files = []
            refactoring_details = []
            
            # Refactor each Camel-related file
            for file_path in analysis.get('camel_files', []):
                if backup:
                    import shutil
                    backup_path = f"{file_path}.backup"
                    shutil.copy2(file_path, backup_path)
                
                refactor_result = refactor_java_code(file_path)
                
                if refactor_result['status'] == 'Success':
                    refactored_files.append(file_path)
                    refactoring_details.append({
                        'file': file_path,
                        'changes': refactor_result.get('changes_made', [])
                    })
            
            return {
                "status": "Success",
                "source_directory": source_code_path,
                "total_java_files": analysis['total_java_files'],
                "camel_files": analysis['camel_file_count'],
                "refactored_files": refactored_files,
                "refactored_count": len(refactored_files),
                "refactoring_details": refactoring_details,
                "backups_created": backup,
                "summary": self._generate_summary(refactoring_details),
                "message": f"Successfully refactored {len(refactored_files)} Java files for Camel 4"
            }
            
        except Exception as e:
            return {
                "status": "Failure",
                "error": str(e),
                "message": f"Failed to refactor business logic: {str(e)}"
            }
    
    def _generate_summary(self, refactoring_details: List[Dict]) -> str:
        """
        Generate a summary of refactoring changes.
        
        Args:
            refactoring_details: List of refactoring details
            
        Returns:
            Summary string
        """
        summary = []
        summary.append("Refactoring Summary")
        summary.append("=" * 50)
        
        total_changes = 0
        change_types = {}
        
        for detail in refactoring_details:
            changes = detail.get('changes', [])
            total_changes += len(changes)
            
            for change in changes:
                # Categorize changes
                if 'import' in change.lower():
                    change_type = 'Import updates'
                elif 'getin()' in change.lower() or 'getout()' in change.lower():
                    change_type = 'Exchange API updates'
                elif 'deprecated' in change.lower():
                    change_type = 'Deprecated method updates'
                elif 'uri' in change.lower():
                    change_type = 'Component URI updates'
                else:
                    change_type = 'Other updates'
                
                change_types[change_type] = change_types.get(change_type, 0) + 1
        
        summary.append(f"\nTotal files refactored: {len(refactoring_details)}")
        summary.append(f"Total changes made: {total_changes}")
        
        if change_types:
            summary.append("\nChanges by type:")
            for change_type, count in sorted(change_types.items(), key=lambda x: x[1], reverse=True):
                summary.append(f"  - {change_type}: {count}")
        
        # Show sample changes
        if refactoring_details and refactoring_details[0].get('changes'):
            summary.append("\nSample changes from first file:")
            for change in refactoring_details[0]['changes'][:5]:
                summary.append(f"  • {change}")
        
        return "\n".join(summary)
    
    def create_processor_template(
        self,
        output_dir: str,
        processor_name: str,
        package_name: str = "com.example.processors"
    ) -> Dict[str, Any]:
        """
        Create a modern Camel 4 processor template.
        
        Args:
            output_dir: Directory to save the processor
            processor_name: Name of the processor
            package_name: Java package name
            
        Returns:
            Dictionary with creation results
        """
        try:
            # Generate processor code
            java_code = self.generate_processor_tool(
                processor_name,
                package_name,
                "Custom processing logic"
            )
            
            # Create package directory
            package_path = package_name.replace('.', os.sep)
            full_output_dir = os.path.join(output_dir, package_path)
            os.makedirs(full_output_dir, exist_ok=True)
            
            # Save processor file
            output_file = os.path.join(full_output_dir, f"{processor_name}.java")
            with open(output_file, 'w') as f:
                f.write(java_code)
            
            return {
                "status": "Success",
                "processor_name": processor_name,
                "package_name": package_name,
                "output_file": output_file,
                "message": f"Successfully created processor template: {processor_name}"
            }
            
        except Exception as e:
            return {
                "status": "Failure",
                "error": str(e),
                "message": f"Failed to create processor template: {str(e)}"
            }


def service_refactor_agent(state):
    """
    Service refactor agent function for LangGraph workflow compatibility.
    Refactors Java business logic from Camel 2 to Camel 4 APIs.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with service refactoring results
    """
    try:
        # Get git repository path from previous agents
        git_repo_path = state.get("artifacts", {}).get("git_repo_path")
        if not git_repo_path:
            return {"error": "Git repository path not found from previous agents"}
        
        # Initialize service refactor agent
        agent = ServiceRefactorAgent()
        
        tasks_completed = list(state.get("tasks_completed", []))
        artifacts = dict(state.get("artifacts", {}))
        
        # Find Java files that need refactoring
        java_files = []
        for root, dirs, files in os.walk(git_repo_path):
            for file in files:
                if file.endswith('.java'):
                    full_path = os.path.join(root, file)
                    # Check if file contains Camel-related code
                    try:
                        with open(full_path, 'r') as f:
                            content = f.read()
                            if any(keyword in content for keyword in ['import org.apache.camel', 'Exchange', 'Processor', 'RouteBuilder']):
                                java_files.append(full_path)
                    except Exception:
                        continue
        
        if not java_files:
            tasks_completed.append("No Java files with Camel code found to refactor")
            artifacts.update({
                "service_refactoring": {
                    "java_files_found": 0,
                    "files_refactored": 0,
                    "message": "No Camel Java files found"
                }
            })
            return {
                "tasks_completed": tasks_completed,
                "artifacts": artifacts
            }
        
        refactored_files = []
        refactoring_changes = []
        
        for java_file in java_files:
            try:
                # Read Java file
                with open(java_file, 'r') as f:
                    original_content = f.read()
                
                # Apply Camel 4 refactoring
                refactored_content = refactor_java_for_camel4(original_content)
                
                if refactored_content != original_content:
                    # Create backup
                    backup_path = f"{java_file}.backup"
                    with open(backup_path, 'w') as f:
                        f.write(original_content)
                    
                    # Write refactored content
                    with open(java_file, 'w') as f:
                        f.write(refactored_content)
                    
                    refactored_files.append(java_file)
                    
                    # Analyze changes
                    changes = analyze_refactoring_changes(original_content, refactored_content)
                    refactoring_changes.append({
                        'file': java_file,
                        'changes': changes
                    })
                    
                    tasks_completed.append(f"Refactored {os.path.relpath(java_file, git_repo_path)} for Camel 4 compatibility")
                
            except Exception as e:
                tasks_completed.append(f"Error refactoring {os.path.relpath(java_file, git_repo_path)}: {str(e)}")
        
        if refactored_files:
            tasks_completed.append(f"Successfully refactored {len(refactored_files)} Java files for Red Hat Camel 4.10")
        
        artifacts.update({
            "service_refactoring": {
                "java_files_found": len(java_files),
                "files_refactored": len(refactored_files),
                "refactored_files": refactored_files,
                "refactoring_changes": refactoring_changes,
                "backup_created": True
            }
        })
        
        return {
            "tasks_completed": tasks_completed,
            "artifacts": artifacts
        }
        
    except Exception as e:
        return {"error": f"Service refactor agent failed: {str(e)}"}


def refactor_java_for_camel4(java_content: str) -> str:
    """
    Refactor Java code from Camel 2/3 to Camel 4 APIs
    Based on Red Hat Camel 4.10 migration guidelines
    """
    import re
    
    refactored_content = java_content
    
    # Update Exchange API calls (most important change)
    # getIn() -> getMessage()
    refactored_content = re.sub(r'\.getIn\(\)', '.getMessage()', refactored_content)
    
    # getOut() -> getMessage() (in most cases)
    refactored_content = re.sub(r'\.getOut\(\)', '.getMessage()', refactored_content)
    
    # Update imports for relocated classes
    import_mappings = {
        'org.apache.camel.impl.DefaultCamelContext': 'org.apache.camel.CamelContext',
        'org.apache.camel.impl.SimpleRegistry': 'org.apache.camel.support.SimpleRegistry',
        'org.apache.camel.util.CamelContextHelper': 'org.apache.camel.support.CamelContextHelper',
        'org.apache.camel.impl.DefaultMessage': 'org.apache.camel.support.DefaultMessage',
        'org.apache.camel.impl.DefaultExchange': 'org.apache.camel.support.DefaultExchange'
    }
    
    for old_import, new_import in import_mappings.items():
        refactored_content = refactored_content.replace(f'import {old_import}', f'import {new_import}')
    
    # Update component URIs that changed in Camel 4
    uri_mappings = {
        'http4:': 'http:',
        'jetty9:': 'jetty:',
        'netty4:': 'netty:'
    }
    
    for old_uri, new_uri in uri_mappings.items():
        refactored_content = refactored_content.replace(f'"{old_uri}', f'"{new_uri}')
        refactored_content = refactored_content.replace(f"'{old_uri}", f"'{new_uri}")
    
    # Update deprecated method calls
    deprecated_mappings = {
        '.setHeader(': '.setHeader(',  # Most header methods remain the same
        '.getContext().getRegistry()': '.getCamelContext().getRegistry()',
    }
    
    for old_method, new_method in deprecated_mappings.items():
        refactored_content = refactored_content.replace(old_method, new_method)
    
    # Add Spring Boot annotations for modern Camel 4
    if 'extends RouteBuilder' in refactored_content and '@Component' not in refactored_content:
        # Add @Component annotation to RouteBuilder classes
        refactored_content = re.sub(
            r'(public class \w+RouteBuilder? extends RouteBuilder)',
            r'@Component\n\1',
            refactored_content
        )
        
        # Add import for @Component if not present
        if 'import org.springframework.stereotype.Component' not in refactored_content:
            if 'import org.apache.camel' in refactored_content:
                refactored_content = refactored_content.replace(
                    'import org.apache.camel',
                    'import org.springframework.stereotype.Component;\nimport org.apache.camel'
                )
    
    return refactored_content


def analyze_refactoring_changes(original: str, refactored: str) -> list:
    """
    Analyze what changes were made during refactoring
    """
    changes = []
    
    if '.getIn()' in original and '.getMessage()' in refactored:
        changes.append("Updated Exchange.getIn() to getMessage() for Camel 4 compatibility")
    
    if '.getOut()' in original and '.getMessage()' in refactored:
        changes.append("Updated Exchange.getOut() to getMessage() for Camel 4 compatibility")
    
    if 'http4:' in original and 'http:' in refactored:
        changes.append("Updated HTTP component URI from http4: to http:")
    
    if 'jetty9:' in original and 'jetty:' in refactored:
        changes.append("Updated Jetty component URI from jetty9: to jetty:")
    
    if '@Component' in refactored and '@Component' not in original:
        changes.append("Added @Component annotation for Spring Boot integration")
    
    if 'org.apache.camel.impl.' in original and 'org.apache.camel.support.' in refactored:
        changes.append("Updated imports for relocated Camel support classes")
    
    return changes
