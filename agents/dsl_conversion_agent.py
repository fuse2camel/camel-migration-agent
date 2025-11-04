"""
DSL Conversion Agent - Converts Camel XML/Java DSL to modern Camel 4 Java DSL
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
    parse_xml_routes,
    convert_xml_to_java_dsl,
    create_route_builder_from_xml,
    analyze_java_files
)
from config.llm_config import get_llm

# Try to import knowledge tools, but don't fail if unavailable
try:
    from tools.knowledge_tools import (
        query_knowledge_tool,
        dsl_conversion_help_tool,
        component_migration_tool,
        ensure_knowledge_base_ready
    )
    KNOWLEDGE_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"Note: Knowledge tools not available ({e}). DSL agent will work without them.")
    KNOWLEDGE_TOOLS_AVAILABLE = False
    # Define dummy functions to avoid NameError
    def ensure_knowledge_base_ready():
        return False
    query_knowledge_tool = None
    dsl_conversion_help_tool = None
    component_migration_tool = None


class DSLConversionAgent:
    """
    Agent responsible for converting Camel routes from XML/old Java DSL to modern Camel 4 Java DSL
    Only creates agents and tasks, does not execute crews
    """
    
    def __init__(self):
        """Initialize the DSL Conversion Agent with LLM and tools"""
        self.llm = get_llm()
        # Try to initialize knowledge base, but don't fail if it's not available
        try:
            self.kb_available = ensure_knowledge_base_ready()
            if not self.kb_available:
                print("Note: Knowledge base not fully available. Using fallback patterns.")
        except Exception as e:
            print(f"Note: Knowledge base initialization failed ({e}). Using fallback patterns.")
            self.kb_available = False
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompts',
            'dsl_conversion_prompt.txt'
        )
        
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
        
        # Build tools list
        tools = [
            self.parse_xml_tool,
            self.convert_to_java_tool,
            self.create_route_builder_tool,
            self.analyze_files_tool
        ]

        # Add knowledge tools if available
        if self.kb_available and KNOWLEDGE_TOOLS_AVAILABLE:
            try:
                kb_tools = [
                    t for t in [query_knowledge_tool, dsl_conversion_help_tool, component_migration_tool]
                    if t is not None
                ]
                if kb_tools:
                    tools.extend(kb_tools)
                    print(f"Added {len(kb_tools)} knowledge tools to DSL agent")
            except Exception as e:
                print(f"Note: Could not add knowledge tools: {e}")

        return Agent(
            role='Core Camel Translator',
            goal='Convert legacy Camel routing definitions to modern Camel 4 Java DSL',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools
        )
    
    @tool("Parse XML Routes")
    def parse_xml_tool(self, xml_file_path: str) -> str:
        """
        Parse Camel XML DSL routes from a file.
        
        Args:
            xml_file_path: Path to the XML file
            
        Returns:
            JSON string with parsed routes
        """
        result = parse_xml_routes(xml_file_path)
        return json.dumps(result, indent=2)
    
    @tool("Convert XML to Java DSL")
    def convert_to_java_tool(self, xml_file_path: str, package_name: str = "com.example.routes") -> str:
        """
        Convert XML routes to Java DSL code.
        
        Args:
            xml_file_path: Path to the XML file
            package_name: Java package name
            
        Returns:
            Generated Java code
        """
        parsed_routes = parse_xml_routes(xml_file_path)
        if parsed_routes['status'] == 'Success':
            java_code = convert_xml_to_java_dsl(parsed_routes, package_name)
            return java_code
        else:
            return f"// Error: {parsed_routes.get('message', 'Failed to parse XML')}"
    
    @tool("Create RouteBuilder Class")
    def create_route_builder_tool(self, xml_file_path: str, output_dir: str, package_name: str = "com.example.routes") -> str:
        """
        Create a complete RouteBuilder Java class from XML routes.
        
        Args:
            xml_file_path: Path to XML file
            output_dir: Directory to save the Java file
            package_name: Package name for the class
            
        Returns:
            JSON string with conversion results
        """
        result = create_route_builder_from_xml(xml_file_path, output_dir, package_name)
        return json.dumps(result, indent=2)
    
    @tool("Analyze Java Files")
    def analyze_files_tool(self, directory_path: str) -> str:
        """
        Analyze Java files in a directory for Camel usage.
        
        Args:
            directory_path: Directory to analyze
            
        Returns:
            JSON string with analysis results
        """
        result = analyze_java_files(directory_path)
        return json.dumps(result, indent=2)
    
    def create_conversion_task(
        self,
        source_code_path: str,
        source_files: List[str] = None,
        output_dir: str = None,
        package_name: str = "com.example.routes.migrated"
    ) -> Task:
        """
        Create a task for converting Camel routes from XML/old Java DSL to modern Camel 4 Java DSL.
        
        Args:
            source_code_path: Path to the source code directory
            source_files: Optional list of specific files to convert
            output_dir: Output directory for converted files
            package_name: Package name for generated Java classes
            
        Returns:
            CrewAI Task for route conversion
        """
        if output_dir is None:
            output_dir = os.path.join(source_code_path, "src", "main", "java")
        
        # Find route files if not specified
        if source_files is None:
            source_files = self._find_route_files(source_code_path)
        
        return Task(
            description=f"""
            Convert Camel routes to modern Camel 4 Java DSL:
            1. Analyze the source directory: {source_code_path}
            2. Find all XML route files (camel-context.xml, routes.xml, etc.)
            3. Parse each XML file to understand the route structure
            4. Convert each route to modern Camel 4 Java DSL
            5. Create RouteBuilder classes in package: {package_name}
            6. Save converted files to: {output_dir}
            
            Files to convert: {source_files if source_files else 'Auto-detect'}
            
            Ensure all routes are properly converted with correct syntax.
            """,
            expected_output="A report of all converted routes with file paths",
            agent=self.agent
        )
    
    def _find_route_files(self, directory: str) -> List[str]:
        """
        Find potential Camel route files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of file paths
        """
        route_files = []
        
        # Common patterns for Camel route files
        patterns = [
            "**/camel-context.xml",
            "**/routes.xml",
            "**/route-*.xml",
            "**/*-routes.xml",
            "**/spring-camel.xml",
            "**/applicationContext.xml"
        ]
        
        for pattern in patterns:
            files = glob.glob(os.path.join(directory, pattern), recursive=True)
            route_files.extend(files)
        
        # Remove duplicates
        route_files = list(set(route_files))
        
        return route_files
    
    def generate_conversion_report(self, conversion_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable conversion report.
        
        Args:
            conversion_result: The conversion result dictionary
            
        Returns:
            Report string
        """
        report = []
        report.append("Route Conversion Report")
        report.append("=" * 50)
        
        report.append(f"\nSource Directory: {conversion_result.get('source_directory', 'N/A')}")
        report.append(f"Output Directory: {conversion_result.get('output_directory', 'N/A')}")
        report.append(f"Files Converted: {conversion_result.get('file_count', 0)}")
        
        conversion_map = conversion_result.get('conversion_map', {})
        if conversion_map:
            report.append("\nConversion Details:")
            for source, target in conversion_map.items():
                report.append(f"  {os.path.basename(source)} -> {os.path.basename(target)}")
        
        return "\n".join(report)


def dsl_conversion_agent(state):
    """
    DSL conversion agent function for LangGraph workflow compatibility.
    Converts XML routes to Java DSL for Camel 4.

    Args:
        state: Current workflow state

    Returns:
        Updated state with DSL conversion results
    """
    try:
        # Get git repository path from previous agents
        git_repo_path = state.get("artifacts", {}).get("git_repo_path")
        if not git_repo_path:
            return {"error": "Git repository path not found from previous agents"}

        # Initialize DSL conversion agent
        agent = DSLConversionAgent()

        tasks_completed = list(state.get("tasks_completed", []))
        artifacts = dict(state.get("artifacts", {}))

        # Solution 3: Find and filter XML route files
        from tools.code_tools import needs_xml_migration, batch_files, parse_xml_routes_chunked

        all_route_files = agent._find_route_files(git_repo_path)

        # Filter: only process files that actually contain routes
        route_files = [f for f in all_route_files if needs_xml_migration(f)]

        if len(all_route_files) > len(route_files):
            skipped = len(all_route_files) - len(route_files)
            tasks_completed.append(f"Skipped {skipped} XML files without Camel routes")

        if not route_files:
            tasks_completed.append("No XML route files found to convert")
            artifacts.update({
                "dsl_conversion": {
                    "route_files_found": 0,
                    "files_converted": 0,
                    "message": "No XML routes found"
                }
            })
            return {
                "tasks_completed": tasks_completed,
                "artifacts": artifacts
            }

        # Solution 1: Batch processing for large file sets
        BATCH_SIZE = 5  # Process 5 XML files per batch
        file_batches = batch_files(route_files, BATCH_SIZE)

        converted_files = []
        java_routes_created = []

        print(f"Processing {len(route_files)} XML route files in {len(file_batches)} batches...")

        for batch_idx, batch in enumerate(file_batches):
            print(f"Processing batch {batch_idx + 1}/{len(file_batches)} ({len(batch)} files)...")

            for route_file in batch:
                try:
                    # Solution 2: Use chunked parsing for large XML files
                    chunks = parse_xml_routes_chunked(route_file, max_routes_per_chunk=10)

                    # Process each chunk
                    for chunk_idx, parsed_routes in enumerate(chunks):
                        if parsed_routes['status'] == 'Success':
                            # Get complete Java class from convert_xml_to_java_dsl
                            java_class_content = convert_xml_to_java_dsl(parsed_routes, "com.example.routes")

                            # Create Java route class file
                            route_name = os.path.basename(route_file).replace('.xml', '').replace('-', '').replace('_', '')
                            route_class_name = f"{route_name.capitalize()}Route"

                            # For chunked files, add chunk suffix
                            if len(chunks) > 1:
                                route_class_name = f"{route_class_name}Part{chunk_idx + 1}"

                            # Update class name and add documentation comment
                            java_class_content = java_class_content.replace(
                                '@Component\npublic class MigratedRoutes extends RouteBuilder {',
                                f'/**\n * Route converted from {os.path.basename(route_file)}\n * Generated by Camel Migration Agent for Red Hat build of Apache Camel 4.10\n */\n@Component\npublic class {route_class_name} extends RouteBuilder {{'
                            )

                            # Find src/main/java directory or create one
                            java_dir = os.path.join(git_repo_path, "src", "main", "java", "com", "example", "routes")
                            os.makedirs(java_dir, exist_ok=True)

                            java_file_path = os.path.join(java_dir, f"{route_class_name}.java")

                            # Write Java DSL route
                            with open(java_file_path, 'w') as f:
                                f.write(java_class_content)

                            java_routes_created.append(java_file_path)

                    converted_files.append(route_file)
                    tasks_completed.append(f"Converted {os.path.relpath(route_file, git_repo_path)} → {len(chunks)} Java file(s)")

                except Exception as e:
                    tasks_completed.append(f"Error converting {os.path.relpath(route_file, git_repo_path)}: {str(e)}")
        
        if converted_files:
            tasks_completed.append(f"Successfully converted {len(converted_files)} XML routes to Java DSL for Camel 4")
        
        artifacts.update({
            "dsl_conversion": {
                "route_files_found": len(route_files),
                "files_converted": len(converted_files),
                "xml_files": route_files,
                "java_files_created": java_routes_created,
                "conversion_successful": len(converted_files) > 0
            }
        })
        
        return {
            "tasks_completed": tasks_completed,
            "artifacts": artifacts
        }
        
    except Exception as e:
        return {"error": f"DSL conversion agent failed: {str(e)}"}
