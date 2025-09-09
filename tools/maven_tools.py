"""
Maven Tools for dependency management and build operations
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import re
from .system_tools import run_command


# Camel 2 to Camel 4 dependency mappings
CAMEL_DEPENDENCY_MAPPINGS = {
    # Core dependencies
    "camel-core": ["camel-core-model", "camel-core-engine"],
    "camel-spring-boot-starter": "camel-spring-boot-starter",
    "camel-spring": "camel-spring",
    
    # Component starters
    "camel-http-starter": "camel-http-starter",
    "camel-servlet-starter": "camel-servlet-starter",
    "camel-jackson-starter": "camel-jackson-starter",
    "camel-jms-starter": "camel-jms-starter",
    "camel-kafka-starter": "camel-kafka-starter",
    "camel-sql-starter": "camel-sql-starter",
    "camel-mongodb-starter": "camel-mongodb-starter",
    "camel-aws-s3-starter": "camel-aws2-s3-starter",
    "camel-aws-sqs-starter": "camel-aws2-sqs-starter",
    "camel-aws-sns-starter": "camel-aws2-sns-starter",
    
    # Regular components
    "camel-http4": "camel-http",
    "camel-http": "camel-http",
    "camel-servlet": "camel-servlet",
    "camel-jackson": "camel-jackson",
    "camel-jms": "camel-jms",
    "camel-kafka": "camel-kafka",
    "camel-sql": "camel-sql",
    "camel-mongodb": "camel-mongodb",
    "camel-aws-s3": "camel-aws2-s3",
    "camel-aws-sqs": "camel-aws2-sqs",
    "camel-aws-sns": "camel-aws2-sns",
    "camel-ftp": "camel-ftp",
    "camel-mail": "camel-mail",
    "camel-quartz2": "camel-quartz",
    "camel-cxf": "camel-cxf",
    "camel-rest": "camel-rest",
    "camel-swagger-java": "camel-openapi-java",
    "camel-metrics": "camel-micrometer"
}

# Dependencies to remove in Camel 4
DEPRECATED_DEPENDENCIES = [
    "camel-core-osgi",
    "camel-blueprint",
    "camel-cdi",
    "camel-ejb",
    "camel-ibatis",
    "camel-jboss",
    "camel-mina",
    "camel-mina2",
    "camel-quartz",
    "camel-rmi",
    "camel-shiro",
    "camel-xmlbeans",
    "camel-xmljson",
    "camel-xstream"
]


def parse_pom_file(pom_path: str) -> Dict[str, Any]:
    """
    Parse a Maven POM file and extract relevant information.
    
    Args:
        pom_path: Path to the pom.xml file
        
    Returns:
        Dictionary with POM information
    """
    try:
        # Parse the XML file
        tree = ET.parse(pom_path)
        root = tree.getroot()
        
        # Handle namespace
        namespace = {'m': 'http://maven.apache.org/POM/4.0.0'}
        if root.tag.startswith('{'):
            namespace['m'] = root.tag.split('}')[0][1:]
        
        # Extract basic info
        group_id = root.find('.//m:groupId', namespace)
        artifact_id = root.find('.//m:artifactId', namespace)
        version = root.find('.//m:version', namespace)
        packaging = root.find('.//m:packaging', namespace)
        
        # Extract parent info
        parent = root.find('.//m:parent', namespace)
        parent_info = None
        if parent is not None:
            parent_group = parent.find('m:groupId', namespace)
            parent_artifact = parent.find('m:artifactId', namespace)
            parent_version = parent.find('m:version', namespace)
            parent_info = {
                "groupId": parent_group.text if parent_group is not None else None,
                "artifactId": parent_artifact.text if parent_artifact is not None else None,
                "version": parent_version.text if parent_version is not None else None
            }
        
        # Extract properties
        properties = {}
        props_elem = root.find('.//m:properties', namespace)
        if props_elem is not None:
            for prop in props_elem:
                prop_name = prop.tag.split('}')[-1] if '}' in prop.tag else prop.tag
                properties[prop_name] = prop.text
        
        # Extract dependencies
        dependencies = []
        deps_elem = root.find('.//m:dependencies', namespace)
        if deps_elem is not None:
            for dep in deps_elem.findall('m:dependency', namespace):
                dep_group = dep.find('m:groupId', namespace)
                dep_artifact = dep.find('m:artifactId', namespace)
                dep_version = dep.find('m:version', namespace)
                dep_scope = dep.find('m:scope', namespace)
                
                dependency = {
                    "groupId": dep_group.text if dep_group is not None else None,
                    "artifactId": dep_artifact.text if dep_artifact is not None else None,
                    "version": dep_version.text if dep_version is not None else None,
                    "scope": dep_scope.text if dep_scope is not None else None
                }
                dependencies.append(dependency)
        
        return {
            "status": "Success",
            "groupId": group_id.text if group_id is not None else None,
            "artifactId": artifact_id.text if artifact_id is not None else None,
            "version": version.text if version is not None else None,
            "packaging": packaging.text if packaging is not None else "jar",
            "parent": parent_info,
            "properties": properties,
            "dependencies": dependencies,
            "tree": tree,
            "root": root,
            "namespace": namespace
        }
    except Exception as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Failed to parse POM file: {str(e)}"
        }


def update_pom_dependencies(pom_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Update POM dependencies from Camel 2 to Camel 4.
    
    Args:
        pom_path: Path to the input pom.xml file
        output_path: Optional path for the output file (defaults to overwriting input)
        
    Returns:
        Dictionary with update status and details
    """
    try:
        # Parse the POM file
        pom_info = parse_pom_file(pom_path)
        if pom_info["status"] == "Failure":
            return pom_info
        
        tree = pom_info["tree"]
        root = pom_info["root"]
        namespace = pom_info["namespace"]
        
        removed_dependencies = []
        added_dependencies = []
        updated_dependencies = []
        
        # Update Camel version property
        props_elem = root.find('.//m:properties', namespace)
        if props_elem is not None:
            # Update Camel version
            for prop in props_elem:
                prop_name = prop.tag.split('}')[-1] if '}' in prop.tag else prop.tag
                if 'camel' in prop_name.lower() and 'version' in prop_name.lower():
                    old_version = prop.text
                    prop.text = "4.0.0"
                    updated_dependencies.append(f"Updated {prop_name} from {old_version} to 4.0.0")
                elif prop_name == "spring-boot.version" or prop_name == "spring.boot.version":
                    old_version = prop.text
                    prop.text = "3.1.0"
                    updated_dependencies.append(f"Updated {prop_name} from {old_version} to 3.1.0")
        
        # Update parent if it's Spring Boot
        parent = root.find('.//m:parent', namespace)
        if parent is not None:
            parent_artifact = parent.find('m:artifactId', namespace)
            parent_version = parent.find('m:version', namespace)
            if parent_artifact is not None and 'spring-boot' in parent_artifact.text:
                if parent_version is not None:
                    old_version = parent_version.text
                    parent_version.text = "3.1.0"
                    updated_dependencies.append(f"Updated parent Spring Boot from {old_version} to 3.1.0")
        
        # Process dependencies
        deps_elem = root.find('.//m:dependencies', namespace)
        if deps_elem is not None:
            dependencies_to_remove = []
            dependencies_to_add = []
            
            for dep in deps_elem.findall('m:dependency', namespace):
                dep_group = dep.find('m:groupId', namespace)
                dep_artifact = dep.find('m:artifactId', namespace)
                dep_version = dep.find('m:version', namespace)
                
                if dep_group is not None and dep_artifact is not None:
                    group_id = dep_group.text
                    artifact_id = dep_artifact.text
                    
                    # Check if it's a Camel dependency
                    if group_id == "org.apache.camel" or (group_id == "org.apache.camel.springboot" and "starter" in artifact_id):
                        # Check for deprecated dependencies
                        if artifact_id in DEPRECATED_DEPENDENCIES:
                            dependencies_to_remove.append(dep)
                            removed_dependencies.append(f"{group_id}:{artifact_id}")
                        
                        # Check for dependencies that need updating
                        elif artifact_id in CAMEL_DEPENDENCY_MAPPINGS:
                            mapping = CAMEL_DEPENDENCY_MAPPINGS[artifact_id]
                            
                            if isinstance(mapping, list):
                                # Replace with multiple dependencies
                                dependencies_to_remove.append(dep)
                                removed_dependencies.append(f"{group_id}:{artifact_id}")
                                
                                for new_artifact in mapping:
                                    new_dep = ET.SubElement(deps_elem, f"{{{namespace['m']}}}dependency")
                                    ET.SubElement(new_dep, f"{{{namespace['m']}}}groupId").text = group_id
                                    ET.SubElement(new_dep, f"{{{namespace['m']}}}artifactId").text = new_artifact
                                    if dep_version is not None:
                                        ET.SubElement(new_dep, f"{{{namespace['m']}}}version").text = "${camel.version}"
                                    dependencies_to_add.append(f"{group_id}:{new_artifact}")
                                    added_dependencies.append(f"{group_id}:{new_artifact}")
                            else:
                                # Simple replacement
                                if artifact_id != mapping:
                                    old_artifact = artifact_id
                                    dep_artifact.text = mapping
                                    updated_dependencies.append(f"Updated {group_id}:{old_artifact} to {group_id}:{mapping}")
                        
                        # Update version to use property
                        if dep_version is not None and not dep_version.text.startswith("${"):
                            dep_version.text = "${camel.version}"
            
            # Remove deprecated dependencies
            for dep in dependencies_to_remove:
                deps_elem.remove(dep)
            
            # Add Spring Boot 3 dependencies if needed
            has_spring_boot = any(
                d["artifactId"] == "spring-boot-starter-web" 
                for d in pom_info["dependencies"] 
                if d["groupId"] == "org.springframework.boot"
            )
            
            if not has_spring_boot and any("spring-boot" in d for d in added_dependencies):
                new_dep = ET.SubElement(deps_elem, f"{{{namespace['m']}}}dependency")
                ET.SubElement(new_dep, f"{{{namespace['m']}}}groupId").text = "org.springframework.boot"
                ET.SubElement(new_dep, f"{{{namespace['m']}}}artifactId").text = "spring-boot-starter-web"
                added_dependencies.append("org.springframework.boot:spring-boot-starter-web")
        
        # Format the XML properly
        ET.indent(tree, space="    ")
        
        # Save the updated POM
        if output_path is None:
            output_path = pom_path
        
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        # Generate summary report
        summary = []
        if removed_dependencies:
            summary.append(f"Removed {len(removed_dependencies)} deprecated dependencies:")
            for dep in removed_dependencies:
                summary.append(f"  - {dep}")
        
        if added_dependencies:
            summary.append(f"\nAdded {len(added_dependencies)} new dependencies:")
            for dep in added_dependencies:
                summary.append(f"  - {dep}")
        
        if updated_dependencies:
            summary.append(f"\nUpdated {len(updated_dependencies)} dependencies:")
            for update in updated_dependencies:
                summary.append(f"  - {update}")
        
        return {
            "status": "Success",
            "modified_pom_file_path": output_path,
            "removed_dependencies": removed_dependencies,
            "added_dependencies": added_dependencies,
            "updated_dependencies": updated_dependencies,
            "summary_report": "\n".join(summary),
            "message": f"Successfully updated POM file with {len(removed_dependencies)} removals, {len(added_dependencies)} additions, and {len(updated_dependencies)} updates"
        }
        
    except Exception as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Failed to update POM dependencies: {str(e)}"
        }


def run_maven_command(
    command: str,
    project_path: str,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Run a Maven command in a project directory.
    
    Args:
        command: Maven command to run (e.g., "clean compile", "test")
        project_path: Path to the Maven project
        timeout: Command timeout in seconds
        
    Returns:
        Dictionary with command execution results
    """
    try:
        full_command = f"mvn {command}"
        success, stdout, stderr = run_command(full_command, cwd=project_path)
        
        # Parse Maven output for common patterns
        build_success = "BUILD SUCCESS" in stdout
        build_failure = "BUILD FAILURE" in stdout or "BUILD FAILURE" in stderr
        compilation_error = "COMPILATION ERROR" in stdout or "COMPILATION ERROR" in stderr
        test_failure = "Tests run:" in stdout and "Failures:" in stdout and not "Failures: 0" in stdout
        
        return {
            "status": "Success" if success and build_success else "Failure",
            "command": full_command,
            "build_success": build_success,
            "build_failure": build_failure,
            "compilation_error": compilation_error,
            "test_failure": test_failure,
            "stdout": stdout,
            "stderr": stderr,
            "message": "Maven command executed successfully" if build_success else "Maven command failed"
        }
        
    except Exception as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Failed to run Maven command: {str(e)}"
        }


def validate_pom_file(pom_path: str) -> Dict[str, Any]:
    """
    Validate a POM file for common issues.
    
    Args:
        pom_path: Path to the pom.xml file
        
    Returns:
        Dictionary with validation results
    """
    try:
        pom_info = parse_pom_file(pom_path)
        if pom_info["status"] == "Failure":
            return pom_info
        
        issues = []
        warnings = []
        
        # Check for required elements
        if not pom_info.get("groupId") and not pom_info.get("parent"):
            issues.append("Missing groupId (no parent defined)")
        
        if not pom_info.get("artifactId"):
            issues.append("Missing artifactId")
        
        if not pom_info.get("version") and not pom_info.get("parent"):
            issues.append("Missing version (no parent defined)")
        
        # Check for Camel version property
        camel_version = None
        for key, value in pom_info.get("properties", {}).items():
            if "camel" in key.lower() and "version" in key.lower():
                camel_version = value
                break
        
        if not camel_version:
            warnings.append("No Camel version property found")
        elif camel_version.startswith("2."):
            issues.append(f"Using Camel 2.x version ({camel_version})")
        
        # Check for conflicting dependencies
        camel_deps = [d for d in pom_info.get("dependencies", []) 
                     if d.get("groupId") == "org.apache.camel"]
        
        if len(camel_deps) > 0:
            camel_versions = set()
            for dep in camel_deps:
                if dep.get("version") and not dep["version"].startswith("${"):
                    camel_versions.add(dep["version"])
            
            if len(camel_versions) > 1:
                issues.append(f"Multiple Camel versions found: {camel_versions}")
        
        return {
            "status": "Valid" if not issues else "Invalid",
            "issues": issues,
            "warnings": warnings,
            "camel_version": camel_version,
            "dependency_count": len(pom_info.get("dependencies", [])),
            "message": "POM file is valid" if not issues else f"POM file has {len(issues)} issues"
        }
        
    except Exception as e:
        return {
            "status": "Failure",
            "error": str(e),
            "message": f"Failed to validate POM file: {str(e)}"
        }
