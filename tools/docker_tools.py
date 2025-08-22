"""
Docker Tools for containerization
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import docker
from jinja2 import Template


DOCKERFILE_TEMPLATE = """FROM eclipse-temurin:{{ java_version }}-jdk-alpine AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN apk add --no-cache maven && mvn clean package -DskipTests

FROM eclipse-temurin:{{ java_version }}-jre-alpine
WORKDIR /app

# Create non-root user
RUN addgroup -g 1000 camel && \
    adduser -D -u 1000 -G camel camel

# Copy JAR from builder stage
COPY --from=builder --chown=camel:camel /app/target/*.jar app.jar

# Switch to non-root user
USER camel

# Set JVM options for container environment
ENV JAVA_OPTS="-Xmx512m -Xms256m -XX:MaxRAMPercentage=75.0"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

# Expose default Spring Boot port
EXPOSE 8080

# Run the application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
"""


def generate_dockerfile(
    project_root_path: str,
    java_version: int = 17,
    base_image: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a Dockerfile for the Camel application.
    
    Args:
        project_root_path: Root directory of the project
        java_version: Java version to use
        base_image: Optional custom base image
        
    Returns:
        Dictionary with generation results
    """
    try:
        template = Template(DOCKERFILE_TEMPLATE)
        
        dockerfile_content = template.render(
            java_version=java_version
        )
        
        # If custom base image is provided, modify the template
        if base_image:
            dockerfile_content = dockerfile_content.replace(
                f"eclipse-temurin:{java_version}-jre-alpine",
                base_image
            )
        
        # Save Dockerfile
        dockerfile_path = os.path.join(project_root_path, "Dockerfile")
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        # Create .dockerignore
        dockerignore_content = """
target/
*.class
*.log
.git
.gitignore
.mvn/
.idea/
*.iml
.project
.settings/
.classpath
"""
        dockerignore_path = os.path.join(project_root_path, ".dockerignore")
        with open(dockerignore_path, 'w') as f:
            f.write(dockerignore_content)
        
        return {
            'status': 'Success',
            'dockerfile_path': dockerfile_path,
            'dockerignore_path': dockerignore_path,
            'java_version': java_version,
            'message': f'Successfully generated Dockerfile for Java {java_version}'
        }
        
    except Exception as e:
        return {
            'status': 'Failure',
            'error': str(e),
            'message': f'Failed to generate Dockerfile: {str(e)}'
        }





def build_docker_image(
    project_root_path: str,
    image_name: str,
    tag: str = "latest",
    push: bool = False,
    registry: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build a Docker image for the application.
    
    Args:
        project_root_path: Root directory of the project
        image_name: Name for the Docker image
        tag: Image tag
        push: Whether to push the image to a registry
        registry: Optional registry URL
        
    Returns:
        Dictionary with build results
    """
    try:
        client = docker.from_env()
        
        # Construct full image name
        if registry:
            full_image_name = f"{registry}/{image_name}:{tag}"
        else:
            full_image_name = f"{image_name}:{tag}"
        
        # Build the image
        image, build_logs = client.images.build(
            path=project_root_path,
            tag=full_image_name,
            rm=True,
            forcerm=True
        )
        
        # Parse build logs
        log_messages = []
        for log in build_logs:
            if 'stream' in log:
                log_messages.append(log['stream'].strip())
        
        result = {
            'status': 'Success',
            'image_name': full_image_name,
            'image_id': image.id,
            'image_tags': image.tags,
            'build_logs': log_messages[-10:],  # Last 10 log lines
            'message': f'Successfully built Docker image: {full_image_name}'
        }
        
        # Push image if requested
        if push:
            try:
                push_logs = client.images.push(
                    repository=image_name if not registry else f"{registry}/{image_name}",
                    tag=tag,
                    stream=True,
                    decode=True
                )
                
                push_messages = []
                for log in push_logs:
                    if 'status' in log:
                        push_messages.append(log['status'])
                
                result['pushed'] = True
                result['push_logs'] = push_messages[-5:]
                result['message'] += f' and pushed to registry'
            except Exception as push_error:
                result['pushed'] = False
                result['push_error'] = str(push_error)
        
        return result
        
    except docker.errors.BuildError as e:
        return {
            'status': 'Failure',
            'error': str(e),
            'build_logs': e.build_log if hasattr(e, 'build_log') else [],
            'message': f'Docker build failed: {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'Failure',
            'error': str(e),
            'message': f'Failed to build Docker image: {str(e)}'
        }



