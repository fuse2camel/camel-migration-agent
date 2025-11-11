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
    analyze_java_files,
    needs_java_migration,
    batch_files
)
from tools.java_parser import JavaParser, find_javax_imports
from tools.java_transformer import JavaTransformer
from tools.config_parser import migrate_application_properties, migrate_application_yaml
from tools.java_refactor_utils import (
    refactor_java_for_camel4,
    is_file_already_camel4,
    analyze_refactoring_changes
)
from knowledge.migration_patterns import get_migration_patterns
from config.llm_config import get_llm


class ServiceRefactorAgent:
    """
    Agent responsible for refactoring Java business logic for Camel 4 compatibility
    """
    
    def __init__(self):
        """Initialize the Service Refactor Agent with LLM and tools"""
        self.llm = get_llm()
        self.patterns = get_migration_patterns()
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
            role='Java Code Modernization Specialist',
            goal='Refactor Java code for Camel 4, Jakarta EE, Spring Boot 3, and Java 21',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                # Existing Camel 4 tools
                self.refactor_java_tool,
                self.analyze_java_tool,
                self.generate_processor_tool,
                # New Jakarta EE tools
                self.migrate_jakarta_imports_tool,
                self.scan_javax_usage_tool,
                # New Spring Boot tools
                self.migrate_spring_properties_tool,
                self.migrate_spring_yaml_tool,
                # New Java modernization tools
                self.analyze_java_modernization_tool,
                self.analyze_modernization_opportunities_tool
            ]
        )

    @staticmethod
    def _create_success_response(file_path: str, **data) -> str:
        """Create standardized success response"""
        return json.dumps({"status": "success", "file": file_path, **data}, indent=2)

    @staticmethod
    def _create_error_response(file_path: str, error: Exception) -> str:
        """Create standardized error response"""
        return json.dumps({"status": "error", "file": file_path, "error": str(error)}, indent=2)
    
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

    # ===== Jakarta EE Migration Tools =====

    @tool("Scan javax Usage")
    def scan_javax_usage_tool(self, file_path: str) -> str:
        """
        Scan a Java file for javax.* imports that need Jakarta EE migration.

        Args:
            file_path: Path to Java source file

        Returns:
            JSON string with found javax imports categorized by API type
        """
        try:
            javax_imports = find_javax_imports(file_path)

            categorized = {
                "persistence": [i for i in javax_imports if "persistence" in i],
                "validation": [i for i in javax_imports if "validation" in i],
                "servlet": [i for i in javax_imports if "servlet" in i],
                "ws_rs": [i for i in javax_imports if "ws.rs" in i],
                "inject": [i for i in javax_imports if "inject" in i],
            }
            categorized["other"] = [
                i for i in javax_imports
                if not any(i in cat_list for cat_list in categorized.values())
            ]

            return self._create_success_response(
                file_path,
                total_javax_imports=len(javax_imports),
                categorized=categorized,
                needs_migration=len(javax_imports) > 0
            )
        except Exception as e:
            return self._create_error_response(file_path, e)

    @tool("Migrate Jakarta Imports")
    def migrate_jakarta_imports_tool(self, file_path: str) -> str:
        """
        Migrate javax.* imports to jakarta.* in a Java file.

        Args:
            file_path: Path to Java source file

        Returns:
            JSON string with migration results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            transformer = JavaTransformer(source_code)
            mappings = self.patterns.get_all_jakarta_packages()

            count = 0
            for old_pkg, new_pkg in mappings.items():
                if transformer.replace_import(old_pkg, new_pkg):
                    count += 1
                count += transformer.replace_package_reference(old_pkg, new_pkg)

            if count > 0:
                transformed = transformer.apply_transformations()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(transformed)
                return self._create_success_response(
                    file_path,
                    transformations=count,
                    message=f"Migrated {count} javax references to jakarta"
                )
            else:
                return json.dumps({"status": "no_changes", "file": file_path}, indent=2)

        except Exception as e:
            return self._create_error_response(file_path, e)

    # ===== Spring Boot Migration Tools =====

    @tool("Migrate Spring Boot Properties")
    def migrate_spring_properties_tool(self, properties_file: str) -> str:
        """
        Migrate application.properties from Spring Boot 2.x to 3.x.

        Args:
            properties_file: Path to application.properties file

        Returns:
            JSON string with migration results
        """
        try:
            result = migrate_application_properties(properties_file, backup=True)
            return json.dumps(result, indent=2)
        except Exception as e:
            return self._create_error_response(properties_file, e)

    @tool("Migrate Spring Boot YAML")
    def migrate_spring_yaml_tool(self, yaml_file: str) -> str:
        """
        Migrate application.yml from Spring Boot 2.x to 3.x.

        Args:
            yaml_file: Path to application.yml file

        Returns:
            JSON string with migration results
        """
        try:
            result = migrate_application_yaml(yaml_file, backup=True)
            return json.dumps(result, indent=2)
        except Exception as e:
            return self._create_error_response(yaml_file, e)

    # ===== Java Modernization Tools =====

    @tool("Analyze Java Modernization Candidates")
    def analyze_java_modernization_tool(self, file_path: str, strategy: str = "balanced") -> str:
        """
        Analyze Java code for modernization opportunities (Java 21 features).
        This is an analysis-only tool - it identifies opportunities but doesn't modify code.

        Args:
            file_path: Path to Java source file
            strategy: Analysis strategy ('aggressive', 'balanced', 'conservative')

        Returns:
            JSON string with analysis results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            parser = JavaParser()
            parser.parse_source(source_code)

            # Find lambda conversion opportunities
            lambda_candidates = parser.find_lambda_candidates()

            return self._create_success_response(
                file_path,
                lambda_candidates=len(lambda_candidates),
                strategy=strategy,
                message=f"Found {len(lambda_candidates)} lambda conversion opportunities"
            )
        except Exception as e:
            return self._create_error_response(file_path, e)

    @tool("Analyze Modernization Opportunities")
    def analyze_modernization_opportunities_tool(self, file_path: str) -> str:
        """
        Analyze Java file for modernization opportunities (Java 21 features).

        Args:
            file_path: Path to Java source file

        Returns:
            JSON string with analysis results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            parser = JavaParser()
            parser.parse_source(source_code)

            # Find lambda candidates (only call once)
            lambda_candidates = parser.find_lambda_candidates()

            opportunities = {
                "lambda_candidates": len(lambda_candidates),
                "has_exchange_api": parser.has_exchange_api_usage(),
                "current_java_version": parser.detect_version(source_code) if hasattr(parser, 'detect_version') else "unknown"
            }

            recommendations = []
            if opportunities["lambda_candidates"] > 0:
                recommendations.append(
                    f"Convert {opportunities['lambda_candidates']} anonymous classes to lambdas"
                )

            return self._create_success_response(
                file_path,
                opportunities=opportunities,
                recommendations=recommendations
            )
        except Exception as e:
            return self._create_error_response(file_path, e)

    def create_refactor_task(
        self,
        source_code_path: str,
        backup: bool = True
    ) -> Task:
        """
        Create a task for refactoring Java business logic for complete Red Hat Camel 4.10 migration.

        Args:
            source_code_path: Path to the source code directory
            backup: Whether to create backups of original files

        Returns:
            CrewAI Task for comprehensive service refactoring
        """
        # Optionally analyze the codebase first
        try:
            analysis = analyze_java_files(source_code_path)
            file_count = analysis.get('camel_file_count', 'unknown')
        except Exception:
            file_count = 'unknown'

        return Task(
            description=f"""
            Refactor Java business logic for complete Red Hat Camel 4.10 enterprise migration.

            **CRITICAL: You MUST use ALL available migration tools, not just Camel 4 refactoring!**

            **PHASE 1: Analysis & Discovery**
            1. Analyze all Java files in: {source_code_path}
            2. Use scan_javax_usage_tool on EVERY .java file to find javax.* imports
            3. Identify Processor implementations and RouteBuilder classes
            4. Identify Bean components and Transformers
            5. Check for Spring Boot application.properties and application.yml files

            **PHASE 2: Camel 4 API Migration**
            6. Update Exchange API usage: getIn() -> getMessage(), getOut() -> getMessage()
            7. Fix imports for relocated classes: org.apache.camel.impl.* -> org.apache.camel.support.*
            8. Update deprecated method calls and patterns
            9. Add @Component annotations to RouteBuilder classes
            10. Use refactor_java_tool to apply Camel 4 transformations

            **PHASE 3: Jakarta EE Migration (REQUIRED)**
            11. For EACH Java file with javax.* imports found in Phase 1:
                - Use migrate_jakarta_imports_tool to convert javax.* -> jakarta.*
                - Verify javax.validation.* -> jakarta.validation.*
                - Verify javax.inject.* -> jakarta.inject.*
                - Verify javax.annotation.* -> jakarta.annotation.*
                - Verify javax.persistence.* -> jakarta.persistence.*
                - Verify javax.servlet.* -> jakarta.servlet.*
            12. Report all Jakarta EE migrations performed

            **PHASE 4: Spring Boot 2 -> 3 Migration (if applicable)**
            13. If application.properties exists: use migrate_spring_properties_tool
            14. If application.yml exists: use migrate_spring_yaml_tool
            15. Migrate deprecated Spring Boot 2.x configurations

            **PHASE 5: Verification & Reporting**
            16. Ensure ALL business logic remains intact
            17. Generate comprehensive report with:
                - Number of Camel 4 transformations
                - Number of javax -> jakarta migrations
                - Number of Spring Boot migrations
                - List of all modified files

            Found {file_count} Camel-related files to process.

            **REMEMBER:**
            - Use scan_javax_usage_tool FIRST to find javax imports
            - Use migrate_jakarta_imports_tool on ALL files with javax imports
            - Use migrate_spring_properties_tool on properties files
            - This is a COMPLETE migration, not just Camel 4!
            """,
            expected_output="""Comprehensive migration report including:
            1. Camel 4 API updates (getIn/getOut -> getMessage)
            2. Jakarta EE migrations (javax -> jakarta) with file-by-file details
            3. Spring Boot 2->3 property migrations
            4. Import relocations (org.apache.camel.impl -> support)
            5. Complete list of all modified files with change summaries""",
            agent=self.agent
        )
    
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

        # Solution 3: Find Java files with smart filtering
        from tools.code_tools import needs_java_migration, batch_files

        all_java_files = []
        for root, dirs, files in os.walk(git_repo_path):
            for file in files:
                if file.endswith('.java'):
                    all_java_files.append(os.path.join(root, file))

        # Filter: only process files that need migration
        java_files = [f for f in all_java_files if needs_java_migration(f)]

        if len(all_java_files) > len(java_files):
            skipped = len(all_java_files) - len(java_files)
            tasks_completed.append(f"Skipped {skipped} Java files that don't need migration")
        
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

        # Solution 1: Batch processing for large file sets
        BATCH_SIZE = 10  # Process 10 files per batch
        file_batches = batch_files(java_files, BATCH_SIZE)

        refactored_files = []
        refactoring_changes = []
        already_converted_files = []
        jakarta_migrated_files = []
        jakarta_migration_details = []

        print(f"Processing {len(java_files)} files in {len(file_batches)} batches...")

        for batch_idx, batch in enumerate(file_batches):
            print(f"Processing batch {batch_idx + 1}/{len(file_batches)} ({len(batch)} files)...")

            for java_file in batch:
                try:
                    # Read Java file
                    with open(java_file, 'r') as f:
                        original_content = f.read()

                    # Check if file has Camel 4 patterns
                    is_already_camel4 = is_file_already_camel4(original_content)

                    # Apply Camel 4 refactoring
                    refactored_content = refactor_java_for_camel4(original_content)

                    # ============ JAKARTA EE MIGRATION (NEW) ============
                    # Apply Jakarta EE migration (javax.* -> jakarta.*)
                    from tools.java_parser import find_javax_imports
                    from tools.java_transformer import JavaTransformer

                    javax_imports = find_javax_imports(java_file)

                    if javax_imports:
                        print(f"  Found {len(javax_imports)} javax.* imports in {os.path.basename(java_file)}, migrating to jakarta.*...")

                        transformer = JavaTransformer(refactored_content)
                        mappings = agent.patterns.get_all_jakarta_packages()

                        jakarta_count = 0
                        for old_pkg, new_pkg in mappings.items():
                            if transformer.replace_import(old_pkg, new_pkg):
                                jakarta_count += 1
                            jakarta_count += transformer.replace_package_reference(old_pkg, new_pkg)

                        if jakarta_count > 0:
                            refactored_content = transformer.apply_transformations()
                            jakarta_migrated_files.append(java_file)
                            jakarta_migration_details.append({
                                'file': java_file,
                                'javax_imports': javax_imports,
                                'transformations': jakarta_count
                            })
                            print(f"  ✓ Migrated {jakarta_count} javax references to jakarta in {os.path.basename(java_file)}")
                    # ====================================================

                    if refactored_content != original_content:
                        # File HAS changes - refactor it
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
                    else:
                        # File doesn't need changes
                        backup_path = f"{java_file}.backup"
                        has_old_backup = os.path.exists(backup_path)

                        if has_old_backup and is_already_camel4:
                            already_converted_files.append(java_file)
                            tasks_completed.append(f"Skipped {os.path.relpath(java_file, git_repo_path)} (already converted in previous run)")
                        elif is_already_camel4:
                            already_converted_files.append(java_file)
                            tasks_completed.append(f"Skipped {os.path.relpath(java_file, git_repo_path)} (already Camel 4 compatible)")
                        else:
                            tasks_completed.append(f"Skipped {os.path.relpath(java_file, git_repo_path)} (no Exchange API usage detected)")

                except Exception as e:
                    tasks_completed.append(f"Error refactoring {os.path.relpath(java_file, git_repo_path)}: {str(e)}")
        
        if refactored_files:
            tasks_completed.append(f"Successfully refactored {len(refactored_files)} Java files for Red Hat Camel 4.10")

        # Add Jakarta EE migration summary
        if jakarta_migrated_files:
            tasks_completed.append(f"Successfully migrated {len(jakarta_migrated_files)} Java files from javax.* to jakarta.*")
            for detail in jakarta_migration_details:
                file_name = os.path.basename(detail['file'])
                tasks_completed.append(f"  - {file_name}: {detail['transformations']} javax → jakarta transformations")

        # Add summary message about already converted files
        if already_converted_files and not refactored_files:
            tasks_completed.append(f"All {len(already_converted_files)} Java files already converted to Camel 4 (from previous migration run)")
        elif already_converted_files:
            tasks_completed.append(f"Found {len(already_converted_files)} files already converted from previous run")

        artifacts.update({
            "service_refactoring": {
                "java_files_found": len(java_files),
                "files_refactored": len(refactored_files),
                "files_already_converted": len(already_converted_files),
                "refactored_files": refactored_files,
                "already_converted_files": already_converted_files,
                "refactoring_changes": refactoring_changes,
                "jakarta_migrated_files": len(jakarta_migrated_files),
                "jakarta_migration_details": jakarta_migration_details,
                "backup_created": True,
                "status": "already_converted" if already_converted_files and not refactored_files else "success"
            }
        })
        
        return {
            "tasks_completed": tasks_completed,
            "artifacts": artifacts
        }
        
    except Exception as e:
        return {"error": f"Service refactor agent failed: {str(e)}"}
