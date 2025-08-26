"""
JDK Agent - Manages Java Development Kit installation and validation
Ensures JDK 21 is available for the migration process
"""

import json
import os
import sys
import platform
import subprocess
import requests
import tarfile
import zipfile
from typing import Dict, Any, Optional
from pathlib import Path
from crewai import Agent, Task
from crewai.tools import tool

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.llm_config import get_llm


class JDKAgent:
    """
    Agent responsible for JDK 21 management and validation
    """

    def __init__(self):
        """Initialize the JDK Agent with tools and configuration"""
        self.agent = Agent(
            role="JDK Manager",
            goal="Ensure JDK 21 is properly installed and configured for the migration process",
            backstory=self._load_backstory(),
            verbose=True,
            allow_delegation=False,
            tools=[
                self.check_java_version_tool,
                self.download_jdk_tool,
                self.install_jdk_tool,
                self.validate_installation_tool
            ],
            llm=get_llm()
        )

    def _load_backstory(self) -> str:
        """Load agent backstory from prompt file"""
        try:
            prompt_path = Path(__file__).parent.parent / "prompts" / "jdk_agent_prompt.txt"
            with open(prompt_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "You are a JDK Manager responsible for ensuring proper Java development environment setup."

    @tool("Check Java Version")
    def check_java_version_tool(self, path_override: str = None) -> str:
        """
        Check if Java 21+ is available on the system.
        
        Args:
            path_override: Optional custom JAVA_HOME path to check
            
        Returns:
            JSON string with version information
        """
        result = self.check_java_version(path_override)
        return json.dumps(result, indent=2)

    @tool("Download JDK")
    def download_jdk_tool(self, install_path: str, os_type: str = None) -> str:
        """
        Download JDK 21 from Adoptium for the current OS.
        
        Args:
            install_path: Directory where to download JDK
            os_type: Override OS detection (linux, windows, mac)
            
        Returns:
            JSON string with download result
        """
        result = self.download_jdk21(install_path, os_type)
        return json.dumps(result, indent=2)

    @tool("Install JDK")
    def install_jdk_tool(self, archive_path: str, install_path: str) -> str:
        """
        Extract and install JDK from downloaded archive.
        
        Args:
            archive_path: Path to downloaded JDK archive
            install_path: Directory where to extract JDK
            
        Returns:
            JSON string with installation result
        """
        result = self.install_jdk(archive_path, install_path)
        return json.dumps(result, indent=2)

    @tool("Validate Installation")
    def validate_installation_tool(self, java_home: str) -> str:
        """
        Validate that JDK installation is working correctly.
        
        Args:
            java_home: Path to JAVA_HOME directory
            
        Returns:
            JSON string with validation result
        """
        result = self.validate_jdk_installation(java_home)
        return json.dumps(result, indent=2)

    def check_java_version(self, path_override: str = None) -> Dict[str, Any]:
        """Check current Java version and availability"""
        try:
            # Set custom JAVA_HOME if provided
            env = os.environ.copy()
            if path_override:
                env['JAVA_HOME'] = path_override
                env['PATH'] = f"{path_override}/bin:{env.get('PATH', '')}"

            # Try to get Java version
            result = subprocess.run(
                ['java', '-version'], 
                capture_output=True, 
                text=True, 
                env=env
            )
            
            if result.returncode != 0:
                return {
                    "status": "not_found",
                    "message": "Java not found in PATH",
                    "version": None,
                    "java_home": env.get('JAVA_HOME'),
                    "meets_requirements": False
                }

            # Parse version from stderr (Java outputs version info to stderr)
            version_output = result.stderr
            version_line = version_output.split('\n')[0]
            
            # Extract version number
            if 'openjdk version' in version_line:
                version_str = version_line.split('"')[1]
            elif 'java version' in version_line:
                version_str = version_line.split('"')[1]
            else:
                version_str = "unknown"

            # Check if it's Java 21+
            major_version = None
            if version_str != "unknown":
                try:
                    if version_str.startswith('1.'):
                        major_version = int(version_str.split('.')[1])
                    else:
                        major_version = int(version_str.split('.')[0])
                except:
                    major_version = 0

            meets_requirements = major_version is not None and major_version >= 21

            return {
                "status": "found",
                "version": version_str,
                "major_version": major_version,
                "java_home": env.get('JAVA_HOME'),
                "meets_requirements": meets_requirements,
                "message": f"Java {version_str} found" + (
                    " (meets requirements)" if meets_requirements 
                    else f" (requires Java 21+, found {major_version})"
                )
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error checking Java version: {str(e)}",
                "meets_requirements": False
            }

    def get_adoptium_download_url(self, os_type: str = None) -> Dict[str, Any]:
        """Get the appropriate JDK 21 download URL from Adoptium API"""
        if not os_type:
            system = platform.system().lower()
            if system == "darwin":
                os_type = "mac"
            elif system == "windows":
                os_type = "windows"
            else:
                os_type = "linux"

        # Architecture detection
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64"]:
            adoptium_arch = "x64"
        elif arch in ["aarch64", "arm64"]:
            adoptium_arch = "aarch64"
        else:
            adoptium_arch = "x64"  # Default fallback

        try:
            # Use Adoptium API to get latest JDK 21 release
            api_url = f"https://api.adoptium.net/v3/binary/latest/21/ga/{os_type}/{adoptium_arch}/jdk/hotspot/normal/eclipse"
            
            response = requests.head(api_url, allow_redirects=True)
            if response.status_code == 200:
                download_url = response.url
                
                # Extract filename from Content-Disposition header if available
                filename = None
                content_disposition = response.headers.get('content-disposition')
                if content_disposition:
                    import re
                    match = re.search(r'filename\s*=\s*"?([^";]+)"?', content_disposition)
                    if match:
                        filename = match.group(1)
                
                # If no filename from header, create a clean one based on OS/arch
                if not filename:
                    if os_type == "windows":
                        filename = f"OpenJDK21U-jdk_{adoptium_arch}_windows_hotspot_21.0.8_9.zip"
                    elif os_type == "mac":
                        filename = f"OpenJDK21U-jdk_{adoptium_arch}_mac_hotspot_21.0.8_9.tar.gz"
                    else:
                        filename = f"OpenJDK21U-jdk_{adoptium_arch}_linux_hotspot_21.0.8_9.tar.gz"
                
                return {
                    "status": "success",
                    "url": download_url,
                    "filename": filename,
                    "os": os_type,
                    "architecture": adoptium_arch
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get download URL from Adoptium API: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error accessing Adoptium API: {str(e)}"
            }

    def download_jdk21(self, install_path: str, os_type: str = None) -> Dict[str, Any]:
        """Download JDK 21 from Adoptium"""
        try:
            # Get download URL
            url_info = self.get_adoptium_download_url(os_type)
            if url_info["status"] != "success":
                return url_info

            download_url = url_info["url"]
            
            # Extract clean filename from Content-Disposition header or URL
            # First try to get filename from the original URL info
            filename = url_info["filename"]
            
            # If filename contains query parameters or is too long, create a clean one
            if '?' in filename or len(filename) > 100:
                # Determine OS-specific filename
                if not os_type:
                    system = platform.system().lower()
                    if system == "darwin":
                        os_type = "mac"
                    elif system == "windows":
                        os_type = "windows"
                    else:
                        os_type = "linux"
                
                arch = platform.machine().lower()
                if arch in ["x86_64", "amd64"]:
                    arch_name = "x64"
                elif arch in ["aarch64", "arm64"]:
                    arch_name = "aarch64"
                else:
                    arch_name = "x64"
                
                # Create clean filename
                if os_type == "windows":
                    filename = f"OpenJDK21U-jdk_{arch_name}_windows_hotspot_21.0.8_9.zip"
                elif os_type == "mac":
                    filename = f"OpenJDK21U-jdk_{arch_name}_mac_hotspot_21.0.8_9.tar.gz"
                else:
                    filename = f"OpenJDK21U-jdk_{arch_name}_linux_hotspot_21.0.8_9.tar.gz"
            
            # Create install directory
            os.makedirs(install_path, exist_ok=True)
            archive_path = os.path.join(install_path, filename)

            print(f"Downloading JDK 21 from Adoptium...")
            print(f"Download URL: {download_url}")
            print(f"Saving to: {archive_path}")
            
            # Download with progress
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(archive_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"Progress: {progress:.1f}%", end='\r')

            print(f"\nDownload completed: {archive_path}")
            print(f"File size: {round(downloaded / (1024 * 1024), 2)} MB")
            
            # Verify file exists and has content
            if not os.path.exists(archive_path) or os.path.getsize(archive_path) == 0:
                return {
                    "status": "error",
                    "message": "Downloaded file is empty or missing"
                }
            
            return {
                "status": "success",
                "archive_path": archive_path,
                "filename": filename,
                "size_mb": round(downloaded / (1024 * 1024), 2),
                "message": "JDK 21 downloaded successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to download JDK 21: {str(e)}"
            }

    def install_jdk(self, archive_path: str, install_path: str) -> Dict[str, Any]:
        """Extract and install JDK from archive"""
        try:
            if not os.path.exists(archive_path):
                return {
                    "status": "error",
                    "message": f"Archive not found: {archive_path}"
                }

            print(f"Extracting JDK to {install_path}...")
            
            # Ensure install path exists and is writable
            try:
                os.makedirs(install_path, exist_ok=True)
                # Test write permissions
                test_file = os.path.join(install_path, ".test_write")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except PermissionError:
                return {
                    "status": "error",
                    "message": f"No write permission to install path: {install_path}"
                }
            
            # Remove existing JDK installation if present
            existing_jdk_dirs = [d for d in os.listdir(install_path) 
                               if os.path.isdir(os.path.join(install_path, d)) 
                               and ('jdk' in d.lower() or 'temurin' in d.lower())]
            
            for old_dir in existing_jdk_dirs:
                old_path = os.path.join(install_path, old_dir)
                try:
                    import shutil
                    print(f"Removing existing JDK installation: {old_path}")
                    shutil.rmtree(old_path)
                except Exception as e:
                    print(f"Warning: Could not remove existing JDK: {e}")
            
            # Determine extraction method based on file extension
            if archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                with tarfile.open(archive_path, 'r:gz') as tar:
                    # Extract with error handling
                    def safe_extract(tarinfo, path):
                        try:
                            tar.extract(tarinfo, path)
                        except PermissionError as e:
                            print(f"Warning: Permission error extracting {tarinfo.name}: {e}")
                        except Exception as e:
                            print(f"Warning: Error extracting {tarinfo.name}: {e}")
                    
                    for member in tar:
                        safe_extract(member, install_path)
                        
            elif archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(install_path)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported archive format: {archive_path}"
                }

            # Find the extracted JDK directory
            extracted_dirs = [d for d in os.listdir(install_path) 
                            if os.path.isdir(os.path.join(install_path, d)) 
                            and ('jdk' in d.lower() or 'temurin' in d.lower())]
            
            if not extracted_dirs:
                return {
                    "status": "error",
                    "message": "Could not find extracted JDK directory"
                }

            jdk_dir = os.path.join(install_path, extracted_dirs[0])
            
            # For macOS, the JDK might be nested in Contents/Home
            if platform.system().lower() == "darwin":
                contents_home = os.path.join(jdk_dir, "Contents", "Home")
                if os.path.exists(contents_home):
                    jdk_dir = contents_home

            print(f"JDK extracted to: {jdk_dir}")
            
            return {
                "status": "success",
                "java_home": jdk_dir,
                "message": "JDK 21 installed successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to install JDK: {str(e)}"
            }

    def validate_jdk_installation(self, java_home: str) -> Dict[str, Any]:
        """Validate JDK installation"""
        try:
            # Check if JAVA_HOME directory exists
            if not os.path.exists(java_home):
                return {
                    "status": "error",
                    "message": f"JAVA_HOME directory does not exist: {java_home}"
                }

            # Check if java executable exists
            java_bin = os.path.join(java_home, "bin", "java")
            if platform.system().lower() == "windows":
                java_bin += ".exe"
            
            if not os.path.exists(java_bin):
                return {
                    "status": "error",
                    "message": f"Java executable not found: {java_bin}"
                }

            # Test Java version with this installation
            version_check = self.check_java_version(java_home)
            
            if version_check["meets_requirements"]:
                return {
                    "status": "success",
                    "java_home": java_home,
                    "version": version_check["version"],
                    "message": f"JDK 21 validation successful: {version_check['version']}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"JDK validation failed: {version_check['message']}"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error validating JDK installation: {str(e)}"
            }

    def create_jdk_validation_task(self, install_path: str = "./jdk21") -> Task:
        """
        Create task for JDK validation and installation.
        
        Args:
            install_path: Directory where to install JDK if needed
            
        Returns:
            CrewAI Task for JDK management
        """
        return Task(
            description=f"""
            Ensure JDK 21 is available for the migration process:
            
            1. Check if Java 21+ is already installed and in PATH
            2. If not found or version is too old:
               a. Download JDK 21 from Adoptium (Eclipse Temurin)
               b. Extract it to: {install_path}
               c. Validate the installation
            3. Provide JAVA_HOME path for subsequent agents
            4. Generate activation script for setting environment variables
            
            The system must have Java 21+ available before proceeding with the migration.
            """,
            expected_output="A report with JDK status and JAVA_HOME path if installation was needed",
            agent=self.agent
        )


def jdk_agent(state):
    """
    JDK agent function for LangGraph workflow compatibility.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with JDK validation/installation results
    """
    try:
        # Initialize JDK agent
        agent = JDKAgent()
        
        # Check current Java version
        java_check = agent.check_java_version()
        
        tasks_completed = list(state.get("tasks_completed", []))
        artifacts = dict(state.get("artifacts", {}))
        
        if java_check["meets_requirements"]:
            # Java 21+ is already available
            tasks_completed.append(f"JDK validation successful: {java_check['version']}")
            artifacts.update({
                "jdk_status": "already_installed",
                "java_version": java_check["version"],
                "java_home": java_check.get("java_home"),
                "jdk_validation": java_check
            })
        else:
            # Need to install JDK 21 - get install path from GUI settings
            install_path = "./artifacts/jdk21"  # Default path
            
            # Try to read JDK install path from GUI settings
            try:
                settings_path = "./artifacts/gui_settings.json"
                if os.path.exists(settings_path):
                    with open(settings_path, 'r') as f:
                        settings = json.load(f)
                        install_path = settings.get("jdk_install_path", install_path)
            except Exception:
                pass  # Use default path if settings can't be read
            
            # Download JDK 21
            download_result = agent.download_jdk21(install_path)
            if download_result["status"] != "success":
                return {"error": f"JDK download failed: {download_result['message']}"}
            
            # Install JDK
            install_result = agent.install_jdk(download_result["archive_path"], install_path)
            if install_result["status"] != "success":
                return {"error": f"JDK installation failed: {install_result['message']}"}
            
            # Validate installation
            validation_result = agent.validate_jdk_installation(install_result["java_home"])
            if validation_result["status"] != "success":
                return {"error": f"JDK validation failed: {validation_result['message']}"}
            
            # Create activation script
            java_home = install_result["java_home"]
            activation_script = f"""#!/bin/bash
# JDK 21 Environment Setup
export JAVA_HOME="{java_home}"
export PATH="$JAVA_HOME/bin:$PATH"
echo "JDK 21 environment activated"
java -version
"""
            
            script_path = "./artifacts/activate_java.sh"
            with open(script_path, 'w') as f:
                f.write(activation_script)
            os.chmod(script_path, 0o755)
            
            tasks_completed.extend([
                "JDK 21 downloaded successfully",
                f"JDK 21 installed to: {java_home}",
                f"JDK validation successful: {validation_result['version']}",
                f"Activation script created: {script_path}"
            ])
            
            artifacts.update({
                "jdk_status": "newly_installed",
                "java_home": java_home,
                "java_version": validation_result["version"],
                "activation_script": script_path,
                "download_info": download_result,
                "install_info": install_result,
                "validation_info": validation_result
            })
        
        return {
            "tasks_completed": tasks_completed,
            "artifacts": artifacts
        }
        
    except Exception as e:
        return {"error": f"JDK agent failed: {str(e)}"}