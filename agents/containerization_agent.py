"""
Containerization Agent - Prepares the application for cloud deployment
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from crewai import Agent, Task
from crewai.tools import tool
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.docker_tools import (
    generate_dockerfile,
    build_docker_image
)
from config.llm_config import get_llm


class ContainerizationAgent:
    """
    Agent responsible for containerizing the application for cloud deployment
    """
    
    def __init__(self):
        """Initialize the Containerization Agent with LLM and tools"""
        self.llm = get_llm()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompts',
            'containerization_prompt.txt'
        )
        
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
        
        return Agent(
            role='Docker Container Packager',
            goal='Prepare the Camel application for Docker containerization',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                self.create_dockerfile_tool,
                self.build_image_tool
            ]
        )
    
    @tool("Create Dockerfile")
    def create_dockerfile_tool(self, project_path: str, java_version: int = 17) -> str:
        """
        Generate a Dockerfile for the application.
        
        Args:
            project_path: Path to the project root
            java_version: Java version to use
            
        Returns:
            JSON string with generation results
        """
        result = generate_dockerfile(project_path, java_version)
        return json.dumps(result, indent=2)
    
    @tool("Build Docker Image")
    def build_image_tool(
        self,
        project_path: str,
        image_name: str,
        tag: str = "latest"
    ) -> str:
        """
        Build a Docker image for the application.
        
        Args:
            project_path: Path to the project root
            image_name: Name for the image
            tag: Image tag
            
        Returns:
            JSON string with build results
        """
        result = build_docker_image(project_path, image_name, tag)
        return json.dumps(result, indent=2)
    

    def create_containerization_task(
        self,
        project_root_path: str,
        app_name: str = "camel-app",
        java_version: int = 17,
        build_image: bool = False
    ) -> Task:
        """
        Create a task for containerizing the Camel application using Docker.
        
        Args:
            project_root_path: Root directory of the project
            app_name: Name of the application
            java_version: Java version to use
            build_image: Whether to build the Docker image
            
        Returns:
            CrewAI Task for containerization
        """
        return Task(
            description=f"""
            Containerize the Camel application using Docker:
            1. Generate an optimized Dockerfile for Java {java_version}
            2. Create .dockerignore file
            {"3. Build the Docker image" if build_image else ""}
            
            Project path: {project_root_path}
            Application name: {app_name}
            
            Ensure the Dockerfile follows best practices for production deployment.
            """,
            expected_output="A report of generated Docker artifacts",
            agent=self.agent
        )
        
        try:
            # Execute containerization
            result = crew.kickoff()
            
            generated_artifacts = []
            containerization_report = {
                "status": "Success",
                "project_path": project_root_path,
                "app_name": app_name,
                "artifacts": {}
            }
            
            # Generate Dockerfile
            dockerfile_result = generate_dockerfile(project_root_path, java_version)
            if dockerfile_result['status'] == 'Success':
                generated_artifacts.append(dockerfile_result['dockerfile_path'])
                generated_artifacts.append(dockerfile_result['dockerignore_path'])
                containerization_report["artifacts"]["dockerfile"] = dockerfile_result
            
            # Build Docker image
            if build_image:
                image_result = build_docker_image(
                    project_root_path,
                    app_name,
                    tag="latest"
                )
                containerization_report["artifacts"]["docker_image"] = image_result
            
            containerization_report["generated_artifacts"] = generated_artifacts
            containerization_report["artifact_count"] = len(generated_artifacts)
            containerization_report["summary"] = self._generate_summary(containerization_report)
            containerization_report["message"] = f"Successfully generated {len(generated_artifacts)} containerization artifacts"
            
            return containerization_report
            
        except Exception as e:
            return {
                "status": "Failure",
                "error": str(e),
                "message": f"Containerization failed: {str(e)}"
            }
    
    def _generate_summary(self, containerization_report: Dict[str, Any]) -> str:
        """
        Generate a summary of containerization artifacts.
        
        Args:
            containerization_report: The containerization report
            
        Returns:
            Summary string
        """
        summary = []
        summary.append("Containerization Summary")
        summary.append("=" * 50)
        
        summary.append(f"\nApplication: {containerization_report.get('app_name', 'N/A')}")
        summary.append(f"Project Path: {containerization_report.get('project_path', 'N/A')}")
        summary.append(f"Total Artifacts: {containerization_report.get('artifact_count', 0)}")
        
        artifacts = containerization_report.get('artifacts', {})
        
        if 'dockerfile' in artifacts:
            summary.append("\n✓ Dockerfile:")
            summary.append(f"  - Path: {artifacts['dockerfile'].get('dockerfile_path', 'N/A')}")
            summary.append(f"  - Java Version: {artifacts['dockerfile'].get('java_version', 'N/A')}")
        
        if 'docker_image' in artifacts:
            image = artifacts['docker_image']
            if image.get('status') == 'Success':
                summary.append("\n✓ Docker Image:")
                summary.append(f"  - Name: {image.get('image_name', 'N/A')}")
                summary.append(f"  - ID: {image.get('image_id', 'N/A')[:12]}")
            else:
                summary.append("\n✗ Docker Image: Build failed")
        
        return "\n".join(summary)
    
    def generate_deployment_guide(
        self,
        containerization_result: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a Docker deployment guide for the containerized application.
        
        Args:
            containerization_result: The containerization result
            output_file: Optional file to save the guide
            
        Returns:
            Deployment guide content
        """
        app_name = containerization_result.get('app_name', 'camel-app')
        
        guide = []
        guide.append("# Docker Deployment Guide for " + app_name)
        guide.append("")
        guide.append("## Prerequisites")
        guide.append("- Docker or Podman installed")
        guide.append("")
        
        guide.append("## Building the Docker Image")
        guide.append("```bash")
        guide.append(f"cd {containerization_result.get('project_path', '.')}")
        guide.append(f"docker build -t {app_name}:latest .")
        guide.append("```")
        guide.append("")
        
        guide.append("## Running the Container")
        guide.append("```bash")
        guide.append("# Run in foreground")
        guide.append(f"docker run -p 8080:8080 {app_name}:latest")
        guide.append("")
        guide.append("# Run in background")
        guide.append(f"docker run -d -p 8080:8080 --name {app_name} {app_name}:latest")
        guide.append("```")
        guide.append("")
        
        guide.append("## Docker Compose (Optional)")
        guide.append("Create a `docker-compose.yml` file:")
        guide.append("```yaml")
        guide.append("version: '3.8'")
        guide.append("services:")
        guide.append(f"  {app_name}:")
        guide.append(f"    image: {app_name}:latest")
        guide.append("    ports:")
        guide.append("      - '8080:8080'")
        guide.append("    environment:")
        guide.append("      - SPRING_PROFILES_ACTIVE=docker")
        guide.append("```")
        guide.append("")
        guide.append("Run with: `docker-compose up`")
        guide.append("")
        
        guide.append("## Monitoring")
        guide.append("```bash")
        guide.append("# View logs")
        guide.append(f"docker logs {app_name}")
        guide.append("")
        guide.append("# Check health")
        guide.append(f"docker exec {app_name} wget -O- localhost:8080/actuator/health")
        guide.append("")
        guide.append("# View running containers")
        guide.append("docker ps")
        guide.append("```")
        guide.append("")
        
        guide.append("## Cleanup")
        guide.append("```bash")
        guide.append("# Stop and remove container")
        guide.append(f"docker stop {app_name}")
        guide.append(f"docker rm {app_name}")
        guide.append("")
        guide.append("# Remove image")
        guide.append(f"docker rmi {app_name}:latest")
        guide.append("```")
        
        guide_content = "\n".join(guide)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(guide_content)
        
        return guide_content
