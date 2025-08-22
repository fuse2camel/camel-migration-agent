"""
DSL Conversion Agent - Converts Camel XML/Java DSL to modern Camel 4 Java DSL
"""

import json
import os
import sys
from typing import Dict, Any, List
from crewai import Agent, Task, Crew
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


class DSLConversionAgent:
    """
    Agent responsible for converting Camel routes from XML/old Java DSL to modern Camel 4 Java DSL
    """
    
    def __init__(self):
        """Initialize the DSL Conversion Agent with LLM and tools"""
        self.llm = get_llm()
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
        
        return Agent(
            role='Core Camel Translator',
            goal='Convert legacy Camel routing definitions to modern Camel 4 Java DSL',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                self.parse_xml_tool,
                self.convert_to_java_tool,
                self.create_route_builder_tool,
                self.analyze_files_tool
            ]
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
    
    def convert_routes(
        self,
        source_code_path: str,
        source_files: List[str] = None,
        output_dir: str = None,
        package_name: str = "com.example.routes.migrated"
    ) -> Dict[str, Any]:
        """
        Convert Camel routes from XML/old Java DSL to modern Camel 4 Java DSL.
        
        Args:
            source_code_path: Path to the source code directory
            source_files: Optional list of specific files to convert
            output_dir: Output directory for converted files
            package_name: Package name for generated Java classes
            
        Returns:
            Dictionary with conversion results
        """
        if output_dir is None:
            output_dir = os.path.join(source_code_path, "src", "main", "java")
        
        # Find route files if not specified
        if source_files is None:
            source_files = self._find_route_files(source_code_path)
        
        # Create conversion task
        conversion_task = Task(
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
        
        # Create crew and execute
        crew = Crew(
            agents=[self.agent],
            tasks=[conversion_task],
            verbose=True
        )
        
        try:
            # Execute the conversion
            result = crew.kickoff()
            
            # Perform actual conversions
            converted_files = []
            conversion_map = {}
            
            for source_file in source_files:
                if source_file.endswith('.xml'):
                    conversion_result = create_route_builder_from_xml(
                        source_file,
                        output_dir,
                        package_name
                    )
                    
                    if conversion_result['status'] == 'Success':
                        converted_files.append(conversion_result['output_file'])
                        conversion_map[source_file] = conversion_result['output_file']
            
            return {
                "status": "Success",
                "source_directory": source_code_path,
                "output_directory": output_dir,
                "source_files": source_files,
                "converted_files": converted_files,
                "conversion_map": conversion_map,
                "file_count": len(converted_files),
                "message": f"Successfully converted {len(converted_files)} route files to Camel 4 Java DSL"
            }
            
        except Exception as e:
            return {
                "status": "Failure",
                "error": str(e),
                "message": f"Failed to convert routes: {str(e)}"
            }
    
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
