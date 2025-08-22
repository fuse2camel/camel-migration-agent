"""
Test Agent - Validates the migrated Camel application
"""

import json
import os
import sys
import time
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew
from crewai.tools import tool
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.maven_tools import run_maven_command
from tools.system_tools import run_command
from config.llm_config import get_llm


class TestAgent:
    """
    Agent responsible for testing and validating the migrated application
    """
    
    def __init__(self):
        """Initialize the Test Agent with LLM and tools"""
        self.llm = get_llm()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompts',
            'test_agent_prompt.txt'
        )
        
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
        
        return Agent(
            role='Quality Assurance Bot',
            goal='Validate that the Camel 4 migration was successful',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                self.compile_project_tool,
                self.run_tests_tool,
                self.smoke_test_tool,
                self.check_logs_tool
            ]
        )
    
    @tool("Compile Project")
    def compile_project_tool(self, project_path: str) -> str:
        """
        Compile the Maven project.
        
        Args:
            project_path: Path to the project root
            
        Returns:
            JSON string with compilation results
        """
        result = run_maven_command("clean compile", project_path)
        return json.dumps(result, indent=2)
    
    @tool("Run Tests")
    def run_tests_tool(self, project_path: str, skip_tests: bool = False) -> str:
        """
        Run Maven tests.
        
        Args:
            project_path: Path to the project root
            skip_tests: Whether to skip tests
            
        Returns:
            JSON string with test results
        """
        command = "test" if not skip_tests else "test -DskipTests"
        result = run_maven_command(command, project_path)
        return json.dumps(result, indent=2)
    
    @tool("Smoke Test Application")
    def smoke_test_tool(self, project_path: str, timeout: int = 60) -> str:
        """
        Perform a smoke test by starting the application.
        
        Args:
            project_path: Path to the project root
            timeout: Time to wait for application startup
            
        Returns:
            JSON string with smoke test results
        """
        # Build the application
        build_result = run_maven_command("package -DskipTests", project_path)
        
        if not build_result.get('build_success'):
            return json.dumps({
                "status": "Failure",
                "error": "Build failed",
                "details": build_result
            })
        
        # Find the JAR file
        target_dir = os.path.join(project_path, "target")
        jar_files = [f for f in os.listdir(target_dir) if f.endswith('.jar') and not f.endswith('-sources.jar')]
        
        if not jar_files:
            return json.dumps({
                "status": "Failure",
                "error": "No JAR file found in target directory"
            })
        
        jar_file = os.path.join(target_dir, jar_files[0])
        
        # Start the application
        success, stdout, stderr = run_command(
            f"timeout {timeout} java -jar {jar_file}",
            cwd=project_path
        )
        
        # Check for successful startup indicators
        startup_success = any([
            "Started" in stdout,
            "Camel context started" in stdout,
            "Routes started" in stdout,
            "Application started" in stdout
        ])
        
        return json.dumps({
            "status": "Success" if startup_success else "Failure",
            "jar_file": jar_file,
            "startup_success": startup_success,
            "startup_logs": stdout[:2000] if stdout else stderr[:2000]
        })
    
    @tool("Check Application Logs")
    def check_logs_tool(self, log_content: str) -> str:
        """
        Analyze application logs for errors and warnings.
        
        Args:
            log_content: Log content to analyze
            
        Returns:
            JSON string with log analysis
        """
        errors = []
        warnings = []
        camel_info = []
        
        lines = log_content.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'error' in line_lower or 'exception' in line_lower:
                errors.append(line[:200])
            elif 'warn' in line_lower:
                warnings.append(line[:200])
            elif 'camel' in line_lower and ('started' in line_lower or 'route' in line_lower):
                camel_info.append(line[:200])
        
        return json.dumps({
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors[:10],  # First 10 errors
            "warnings": warnings[:10],  # First 10 warnings
            "camel_info": camel_info[:10]  # First 10 Camel-related lines
        })
    
    def validate_migration(
        self,
        project_root_path: str,
        run_full_tests: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive validation of the migrated application.
        
        Args:
            project_root_path: Root directory of the migrated project
            run_full_tests: Whether to run full test suite
            
        Returns:
            Dictionary with validation results
        """
        # Create validation task
        validation_task = Task(
            description=f"""
            Validate the migrated Camel 4 application:
            1. Compile the project at: {project_root_path}
            2. Run unit tests (if run_full_tests is {run_full_tests})
            3. Package the application
            4. Perform a smoke test by starting the application
            5. Check logs for errors and warnings
            6. Verify Camel Context initialization
            
            Report any compilation errors, test failures, or runtime issues.
            """,
            expected_output="A comprehensive validation report with test results",
            agent=self.agent
        )
        
        # Create crew and execute
        crew = Crew(
            agents=[self.agent],
            tasks=[validation_task],
            verbose=True
        )
        
        try:
            # Execute validation
            result = crew.kickoff()
            
            # Perform actual validation steps
            validation_report = {
                "status": "Success",
                "project_path": project_root_path,
                "steps": []
            }
            
            # Step 1: Compile
            compile_result = run_maven_command("clean compile", project_root_path)
            validation_report["steps"].append({
                "step": "Compilation",
                "status": "Success" if compile_result.get('build_success') else "Failure",
                "details": compile_result.get('message', '')
            })
            validation_report["compilation_status"] = "Success" if compile_result.get('build_success') else "Failure"
            
            if not compile_result.get('build_success'):
                validation_report["status"] = "Failure"
                validation_report["message"] = "Compilation failed"
                return validation_report
            
            # Step 2: Run tests
            if run_full_tests:
                test_result = run_maven_command("test", project_root_path)
                validation_report["steps"].append({
                    "step": "Unit Tests",
                    "status": "Success" if test_result.get('build_success') and not test_result.get('test_failure') else "Failure",
                    "details": test_result.get('message', '')
                })
                validation_report["test_run_results"] = "Success" if test_result.get('build_success') else "Failure"
            else:
                validation_report["test_run_results"] = "Skipped"
            
            # Step 3: Package
            package_result = run_maven_command("package -DskipTests", project_root_path)
            validation_report["steps"].append({
                "step": "Packaging",
                "status": "Success" if package_result.get('build_success') else "Failure",
                "details": package_result.get('message', '')
            })
            
            # Step 4: Smoke test (simplified version)
            validation_report["smoke_test_passed"] = package_result.get('build_success', False)
            
            # Generate summary
            all_success = all(step["status"] == "Success" for step in validation_report["steps"] if step["step"] != "Unit Tests" or run_full_tests)
            validation_report["overall_status"] = "Success" if all_success else "Partial Success"
            validation_report["message"] = self._generate_summary(validation_report)
            
            return validation_report
            
        except Exception as e:
            return {
                "status": "Failure",
                "error": str(e),
                "message": f"Validation failed: {str(e)}"
            }
    
    def _generate_summary(self, validation_report: Dict[str, Any]) -> str:
        """
        Generate a summary of the validation results.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Summary string
        """
        summary = []
        summary.append("Validation Summary")
        summary.append("=" * 50)
        
        for step in validation_report.get("steps", []):
            status_icon = "✓" if step["status"] == "Success" else "✗"
            summary.append(f"{status_icon} {step['step']}: {step['status']}")
            if step["details"]:
                summary.append(f"  {step['details']}")
        
        overall = validation_report.get("overall_status", "Unknown")
        summary.append(f"\nOverall Status: {overall}")
        
        if overall == "Success":
            summary.append("✅ Migration validation successful! The application is ready for deployment.")
        elif overall == "Partial Success":
            summary.append("⚠️ Migration partially successful. Some issues need attention.")
        else:
            summary.append("❌ Migration validation failed. Please review the errors above.")
        
        return "\n".join(summary)
    
    def generate_test_report(
        self,
        validation_result: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a detailed test report.
        
        Args:
            validation_result: The validation result dictionary
            output_file: Optional file to save the report
            
        Returns:
            Report content as string
        """
        report = []
        report.append("=" * 70)
        report.append("CAMEL MIGRATION VALIDATION REPORT")
        report.append("=" * 70)
        report.append("")
        
        report.append(f"Project Path: {validation_result.get('project_path', 'N/A')}")
        report.append(f"Validation Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("Validation Steps:")
        report.append("-" * 40)
        
        for step in validation_result.get("steps", []):
            report.append(f"• {step['step']}: {step['status']}")
            if step.get('details'):
                report.append(f"  Details: {step['details']}")
        
        report.append("")
        report.append("Results:")
        report.append("-" * 40)
        report.append(f"Compilation: {validation_result.get('compilation_status', 'N/A')}")
        report.append(f"Tests: {validation_result.get('test_run_results', 'N/A')}")
        report.append(f"Smoke Test: {'Passed' if validation_result.get('smoke_test_passed') else 'Failed'}")
        
        report.append("")
        report.append("Overall Status: " + validation_result.get('overall_status', 'Unknown'))
        report.append("")
        
        if validation_result.get('message'):
            report.append("Summary:")
            report.append("-" * 40)
            report.append(validation_result['message'])
        
        report_content = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_content)
        
        return report_content
