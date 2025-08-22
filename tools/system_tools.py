"""
System Tools for environment validation and command execution
"""

import subprocess
import re
import json
from typing import Dict, Any, Optional, Tuple
import shutil


def run_command(command: str, cwd: Optional[str] = None) -> Tuple[bool, str, str]:
    """
    Execute a system command and return the result.
    
    Args:
        command: Command to execute
        cwd: Working directory for command execution
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def check_java_version() -> Dict[str, Any]:
    """
    Check Java installation and version.
    
    Returns:
        Dictionary with status and version information
    """
    try:
        # Check if Java is installed
        java_path = shutil.which("java")
        if not java_path:
            return {
                "installed": False,
                "error": "Java not found in PATH"
            }
        
        # Get Java version
        success, stdout, stderr = run_command("java -version")
        if not success and stderr:
            # Java outputs version to stderr
            version_output = stderr
        else:
            version_output = stdout if stdout else stderr
            
        # Parse version from output
        version_match = re.search(r'version "?(\d+)\.?(\d+)?', version_output)
        if version_match:
            major_version = int(version_match.group(1))
            # Handle both old (1.8) and new (11, 17) version numbering
            if major_version == 1:
                major_version = int(version_match.group(2)) if version_match.group(2) else 8
            
            return {
                "installed": True,
                "version": major_version,
                "full_version": version_output.split('\n')[0],
                "path": java_path,
                "meets_requirement": major_version >= 17
            }
        
        return {
            "installed": True,
            "version": "unknown",
            "full_version": version_output,
            "path": java_path,
            "meets_requirement": False
        }
        
    except Exception as e:
        return {
            "installed": False,
            "error": str(e)
        }


def check_maven_version() -> Dict[str, Any]:
    """
    Check Maven installation and version.
    
    Returns:
        Dictionary with status and version information
    """
    try:
        # Check if Maven is installed
        mvn_path = shutil.which("mvn")
        if not mvn_path:
            return {
                "installed": False,
                "error": "Maven not found in PATH"
            }
        
        # Get Maven version
        success, stdout, stderr = run_command("mvn --version")
        if not success:
            return {
                "installed": True,
                "error": f"Could not get Maven version: {stderr}"
            }
        
        # Parse version from output
        version_match = re.search(r'Apache Maven (\d+)\.(\d+)\.(\d+)', stdout)
        if version_match:
            major = int(version_match.group(1))
            minor = int(version_match.group(2))
            patch = int(version_match.group(3))
            version_string = f"{major}.{minor}.{patch}"
            
            # Check if meets minimum requirement (3.8.0)
            meets_requirement = (major > 3) or (major == 3 and minor >= 8)
            
            return {
                "installed": True,
                "version": version_string,
                "major": major,
                "minor": minor,
                "patch": patch,
                "full_output": stdout.split('\n')[0],
                "path": mvn_path,
                "meets_requirement": meets_requirement
            }
        
        return {
            "installed": True,
            "version": "unknown",
            "full_output": stdout,
            "path": mvn_path,
            "meets_requirement": False
        }
        
    except Exception as e:
        return {
            "installed": False,
            "error": str(e)
        }


def check_git_version() -> Dict[str, Any]:
    """
    Check Git installation and version.
    
    Returns:
        Dictionary with status and version information
    """
    try:
        # Check if Git is installed
        git_path = shutil.which("git")
        if not git_path:
            return {
                "installed": False,
                "error": "Git not found in PATH"
            }
        
        # Get Git version
        success, stdout, stderr = run_command("git --version")
        if not success:
            return {
                "installed": True,
                "error": f"Could not get Git version: {stderr}"
            }
        
        # Parse version from output
        version_match = re.search(r'git version (\d+)\.(\d+)\.(\d+)', stdout)
        if version_match:
            major = int(version_match.group(1))
            minor = int(version_match.group(2))
            patch = int(version_match.group(3))
            version_string = f"{major}.{minor}.{patch}"
            
            return {
                "installed": True,
                "version": version_string,
                "major": major,
                "minor": minor,
                "patch": patch,
                "full_output": stdout.strip(),
                "path": git_path,
                "meets_requirement": True  # Any recent Git version is fine
            }
        
        return {
            "installed": True,
            "version": "unknown",
            "full_output": stdout,
            "path": git_path,
            "meets_requirement": True
        }
        
    except Exception as e:
        return {
            "installed": False,
            "error": str(e)
        }


def check_docker_version() -> Dict[str, Any]:
    """
    Check Docker or Podman installation and version.
    
    Returns:
        Dictionary with status and version information
    """
    # Try Docker first
    docker_path = shutil.which("docker")
    if docker_path:
        try:
            success, stdout, stderr = run_command("docker --version")
            if success:
                version_match = re.search(r'Docker version (\d+)\.(\d+)\.(\d+)', stdout)
                if version_match:
                    return {
                        "installed": True,
                        "engine": "docker",
                        "version": f"{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}",
                        "full_output": stdout.strip(),
                        "path": docker_path,
                        "meets_requirement": True
                    }
        except Exception:
            pass
    
    # Try Podman as alternative
    podman_path = shutil.which("podman")
    if podman_path:
        try:
            success, stdout, stderr = run_command("podman --version")
            if success:
                version_match = re.search(r'podman version (\d+)\.(\d+)\.(\d+)', stdout)
                if version_match:
                    return {
                        "installed": True,
                        "engine": "podman",
                        "version": f"{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}",
                        "full_output": stdout.strip(),
                        "path": podman_path,
                        "meets_requirement": True
                    }
        except Exception:
            pass
    
    return {
        "installed": False,
        "error": "Neither Docker nor Podman found in PATH"
    }


def validate_environment(requirements: Dict[str, str]) -> Dict[str, Any]:
    """
    Validate the entire environment against requirements.
    
    Args:
        requirements: Dictionary of tool requirements
        
    Returns:
        Comprehensive validation report
    """
    report = {
        "overall_status": "Success",
        "checks": []
    }
    
    # Check Java
    java_check = check_java_version()
    java_status = {
        "tool": "Java JDK",
        "required_version": requirements.get("java", "17"),
        "installed": java_check.get("installed", False),
        "current_version": java_check.get("version", "Not installed"),
        "meets_requirement": java_check.get("meets_requirement", False),
        "details": java_check.get("full_version", java_check.get("error", ""))
    }
    report["checks"].append(java_status)
    
    # Check Maven
    maven_check = check_maven_version()
    maven_status = {
        "tool": "Maven",
        "required_version": requirements.get("maven", "3.8.0"),
        "installed": maven_check.get("installed", False),
        "current_version": maven_check.get("version", "Not installed"),
        "meets_requirement": maven_check.get("meets_requirement", False),
        "details": maven_check.get("full_output", maven_check.get("error", ""))
    }
    report["checks"].append(maven_status)
    
    # Check Git
    git_check = check_git_version()
    git_status = {
        "tool": "Git",
        "required_version": requirements.get("git", "Any"),
        "installed": git_check.get("installed", False),
        "current_version": git_check.get("version", "Not installed"),
        "meets_requirement": git_check.get("meets_requirement", False),
        "details": git_check.get("full_output", git_check.get("error", ""))
    }
    report["checks"].append(git_status)
    
    # Check Container Engine
    docker_check = check_docker_version()
    docker_status = {
        "tool": "Container Engine",
        "required_version": requirements.get("docker", "Any"),
        "installed": docker_check.get("installed", False),
        "current_version": docker_check.get("version", "Not installed"),
        "engine_type": docker_check.get("engine", "None"),
        "meets_requirement": docker_check.get("meets_requirement", False),
        "details": docker_check.get("full_output", docker_check.get("error", ""))
    }
    report["checks"].append(docker_status)
    
    # Determine overall status
    all_met = all(check.get("meets_requirement", False) for check in report["checks"])
    report["overall_status"] = "Success" if all_met else "Failure"
    
    return report
