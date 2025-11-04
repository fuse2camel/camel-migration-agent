"""
Dependency Agent - Updates Maven POM dependencies for Camel 4 migration
Refactored to separate agent and task creation from crew execution
"""

import json
import os
import sys
from typing import Dict, Any, List
from crewai import Agent, Task
from crewai.tools import tool
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.maven_tools import (
    parse_pom_file,
    update_pom_dependencies,
    validate_pom_file
)
from config.llm_config import get_llm


class DependencyAgent:
    """
    Agent responsible for updating Maven dependencies from Camel 2 to Camel 4
    Only creates agents and tasks, does not execute crews
    """
    
    def __init__(self):
        """Initialize the Dependency Agent with LLM and tools"""
        self.llm = get_llm()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompts',
            'dependency_checker_prompt.txt'
        )
        
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
        
        return Agent(
            role='Project Build Expert',
            goal='Complete POM transformation from Fuse 6.x to Red Hat Camel 4.10 Spring Boot',
            backstory=system_prompt,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                self.parse_pom_tool,
                self.update_dependencies_tool,
                self.transform_pom_structure_tool
            ]
        )
    
    @tool("Parse POM File")
    def parse_pom_tool(self, pom_path: str) -> str:
        """
        Parse a Maven POM file.
        
        Args:
            pom_path: Path to the pom.xml file
            
        Returns:
            JSON string with POM information
        """
        result = parse_pom_file(pom_path)
        # Remove non-serializable elements
        if 'tree' in result:
            del result['tree']
        if 'root' in result:
            del result['root']
        if 'namespace' in result:
            del result['namespace']
        return json.dumps(result, indent=2)
    
    @tool("Update POM Dependencies")
    def update_dependencies_tool(self, pom_path: str, output_path: str = None) -> str:
        """
        Transform dependencies from Fuse 6.x to Apache Camel 4.x Spring Boot starters.
        
        Args:
            pom_path: Path to the input pom.xml file
            output_path: Optional output path
            
        Returns:
            JSON string with update results
        """
        try:
            import xml.etree.ElementTree as ET
            from xml.dom import minidom
            
            # Read the POM file
            tree = ET.parse(pom_path)
            root = tree.getroot()
            
            # Define namespace
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            transformations = []
            
            # 1. Update dependencyManagement with correct Camel Spring Boot BOM
            dependency_mgmt = root.find('./maven:dependencyManagement', ns)
            if dependency_mgmt is not None:
                dependencies = dependency_mgmt.find('./maven:dependencies', ns)
                if dependencies is not None:
                    # Remove old BOM entries
                    for dependency in dependencies.findall('./maven:dependency', ns):
                        group_id = dependency.find('./maven:groupId', ns)
                        artifact_id = dependency.find('./maven:artifactId', ns)
                        if (group_id is not None and 
                            ('jboss.fuse' in group_id.text or 'com.redhat.camel.springboot' in group_id.text or 'com.redhat.camel.springboot.platform' in group_id.text)):
                            dependencies.remove(dependency)
                            transformations.append(f"Removed old BOM: {group_id.text}:{artifact_id.text if artifact_id is not None else ''}")
                    
                    # Add Red Hat build of Apache Camel 4.10.3.redhat-00019 Spring Boot BOM with correct coordinates
                    camel_bom = ET.Element('dependency')
                    group_id = ET.SubElement(camel_bom, 'groupId')
                    group_id.text = 'com.redhat.camel.springboot.platform'
                    artifact_id = ET.SubElement(camel_bom, 'artifactId')
                    artifact_id.text = 'camel-spring-boot-bom'
                    version = ET.SubElement(camel_bom, 'version')
                    version.text = '4.10.3.redhat-00019'
                    type_elem = ET.SubElement(camel_bom, 'type')
                    type_elem.text = 'pom'
                    scope = ET.SubElement(camel_bom, 'scope')
                    scope.text = 'import'
                    dependencies.append(camel_bom)
                    transformations.append("Added Red Hat Camel 4.10.3.redhat-00019 Spring Boot BOM with platform groupId")
            
            # 2. Transform dependencies section
            deps_section = root.find('./maven:dependencies', ns)
            if deps_section is not None:
                # Dependency mapping from old to Red Hat Camel Spring Boot starters
                dependency_mappings = {
                    ('org.apache.camel', 'camel-core'): ('org.apache.camel.springboot', 'camel-spring-boot-starter'),
                    ('org.apache.camel', 'camel-spring'): ('org.apache.camel.springboot', 'camel-spring-boot-starter'),
                    ('org.apache.camel', 'camel-jackson'): ('org.apache.camel.springboot', 'camel-jackson-starter'),
                    ('org.apache.camel', 'camel-test-spring'): ('org.apache.camel', 'camel-test-spring-junit5'),
                    ('org.apache.activemq', 'activemq-camel'): ('org.apache.camel.springboot', 'camel-jms-starter'),
                }
                
                # Dependencies to remove (conflicts with Spring Boot)
                dependencies_to_remove = [
                    ('org.slf4j', 'slf4j-log4j12'),
                    ('log4j', 'log4j'),
                    ('org.slf4j', 'slf4j-api'),  # Spring Boot manages this
                ]
                
                # Remove problematic dependencies
                for dependency in list(deps_section.findall('./maven:dependency', ns)):
                    group_id_elem = dependency.find('./maven:groupId', ns)
                    artifact_id_elem = dependency.find('./maven:artifactId', ns)
                    
                    if group_id_elem is not None and artifact_id_elem is not None:
                        dep_key = (group_id_elem.text, artifact_id_elem.text)
                        if dep_key in dependencies_to_remove:
                            deps_section.remove(dependency)
                            transformations.append(f"Removed conflicting dependency: {dep_key[0]}:{dep_key[1]}")
                            continue
                
                # Transform existing dependencies
                for dependency in deps_section.findall('./maven:dependency', ns):
                    group_id_elem = dependency.find('./maven:groupId', ns)
                    artifact_id_elem = dependency.find('./maven:artifactId', ns)
                    
                    if group_id_elem is not None and artifact_id_elem is not None:
                        old_key = (group_id_elem.text, artifact_id_elem.text)
                        
                        if old_key in dependency_mappings:
                            new_group, new_artifact = dependency_mappings[old_key]
                            group_id_elem.text = new_group
                            artifact_id_elem.text = new_artifact
                            transformations.append(f"Transformed {old_key[0]}:{old_key[1]} → {new_group}:{new_artifact}")
                            
                            # Special case: camel-test-spring needs additional spring-boot-starter-test
                            if old_key == ('org.apache.camel', 'camel-test-spring'):
                                # Add scope=test to the camel-test-spring-junit5 dependency
                                test_scope_elem = dependency.find('./maven:scope', ns)
                                if test_scope_elem is None:
                                    test_scope_elem = ET.SubElement(dependency, 'scope')
                                test_scope_elem.text = 'test'
                                
                                # Add spring-boot-starter-test as well
                                spring_test_starter = ET.Element('dependency')
                                test_group_id = ET.SubElement(spring_test_starter, 'groupId')
                                test_group_id.text = 'org.springframework.boot'
                                test_artifact_id = ET.SubElement(spring_test_starter, 'artifactId')
                                test_artifact_id.text = 'spring-boot-starter-test'
                                test_scope = ET.SubElement(spring_test_starter, 'scope')
                                test_scope.text = 'test'
                                deps_section.append(spring_test_starter)
                                transformations.append("Added spring-boot-starter-test for testing")
                        
                        # Remove version elements (managed by BOM)
                        version_elem = dependency.find('./maven:version', ns)
                        if version_elem is not None and group_id_elem.text in ['org.apache.camel.springboot', 'org.apache.camel', 'org.springframework.boot']:
                            dependency.remove(version_elem)
                            transformations.append(f"Removed version for {group_id_elem.text}:{artifact_id_elem.text} (managed by BOM)")
                
                # Red Hat Camel Spring Boot starters provide all necessary functionality
                # No need to add additional Spring Boot starters as per Red Hat documentation
                
                # Add required Red Hat camel-spring-boot-starter if not present
                camel_starter_exists = False
                for dependency in deps_section.findall('./maven:dependency', ns):
                    group_id_elem = dependency.find('./maven:groupId', ns)
                    artifact_id_elem = dependency.find('./maven:artifactId', ns)
                    if (group_id_elem is not None and group_id_elem.text == 'org.apache.camel.springboot' and
                        artifact_id_elem is not None and artifact_id_elem.text == 'camel-spring-boot-starter'):
                        camel_starter_exists = True
                        break
                        
                if not camel_starter_exists:
                    camel_starter = ET.Element('dependency')
                    group_id = ET.SubElement(camel_starter, 'groupId')
                    group_id.text = 'org.apache.camel.springboot'
                    artifact_id = ET.SubElement(camel_starter, 'artifactId')
                    artifact_id.text = 'camel-spring-boot-starter'
                    deps_section.insert(1, camel_starter)
                    transformations.append("Added required Red Hat camel-spring-boot-starter dependency")
            
            # 3. Update/Add Red Hat Maven repositories
            repositories = root.find('./maven:repositories', ns)
            if repositories is None:
                # Create repositories section
                repositories = ET.Element('repositories')
                # Insert before build section or at the end
                build = root.find('./maven:build', ns)
                if build is not None:
                    build_index = list(root).index(build)
                    root.insert(build_index, repositories)
                else:
                    root.append(repositories)
                transformations.append("Created repositories section")
            
            # Add Red Hat GA repository
            redhat_ga_exists = False
            redhat_ea_exists = False
            for repo in repositories.findall('./maven:repository', ns):
                repo_id = repo.find('./maven:id', ns)
                if repo_id is not None:
                    if 'red-hat-ga' in repo_id.text or 'redhat-ga' in repo_id.text:
                        redhat_ga_exists = True
                    elif 'red-hat-earlyaccess' in repo_id.text or 'redhat-earlyaccess' in repo_id.text:
                        redhat_ea_exists = True
            
            if not redhat_ga_exists:
                redhat_ga_repo = ET.Element('repository')
                repo_id = ET.SubElement(redhat_ga_repo, 'id')
                repo_id.text = 'red-hat-ga-repository'
                repo_name = ET.SubElement(redhat_ga_repo, 'name')
                repo_name.text = 'Red Hat GA Repository'
                repo_url = ET.SubElement(redhat_ga_repo, 'url')
                repo_url.text = 'https://maven.repository.redhat.com/ga'
                repositories.append(redhat_ga_repo)
                transformations.append("Added Red Hat GA repository")
            
            if not redhat_ea_exists:
                redhat_ea_repo = ET.Element('repository')
                repo_id = ET.SubElement(redhat_ea_repo, 'id')
                repo_id.text = 'red-hat-earlyaccess-repository'
                repo_name = ET.SubElement(redhat_ea_repo, 'name')
                repo_name.text = 'Red Hat Early Access Repository'
                repo_url = ET.SubElement(redhat_ea_repo, 'url')
                repo_url.text = 'https://maven.repository.redhat.com/earlyaccess/all'
                repositories.append(redhat_ea_repo)
                transformations.append("Added Red Hat Early Access repository")
            
            # 4. Update/Add Red Hat Maven plugin repositories
            plugin_repos = root.find('./maven:pluginRepositories', ns)
            if plugin_repos is None:
                # Create pluginRepositories section
                plugin_repos = ET.Element('pluginRepositories')
                # Insert after repositories
                repositories_index = list(root).index(repositories)
                root.insert(repositories_index + 1, plugin_repos)
                transformations.append("Created pluginRepositories section")
            
            # Add Red Hat plugin repositories
            redhat_plugin_ga_exists = False
            redhat_plugin_ea_exists = False
            for repo in plugin_repos.findall('./maven:pluginRepository', ns):
                repo_id = repo.find('./maven:id', ns)
                if repo_id is not None:
                    if 'red-hat-ga' in repo_id.text or 'redhat-ga' in repo_id.text:
                        redhat_plugin_ga_exists = True
                    elif 'red-hat-earlyaccess' in repo_id.text or 'redhat-earlyaccess' in repo_id.text:
                        redhat_plugin_ea_exists = True
            
            if not redhat_plugin_ga_exists:
                redhat_plugin_ga_repo = ET.Element('pluginRepository')
                repo_id = ET.SubElement(redhat_plugin_ga_repo, 'id')
                repo_id.text = 'red-hat-ga-plugin-repository'
                repo_name = ET.SubElement(redhat_plugin_ga_repo, 'name')
                repo_name.text = 'Red Hat GA Plugin Repository'
                repo_url = ET.SubElement(redhat_plugin_ga_repo, 'url')
                repo_url.text = 'https://maven.repository.redhat.com/ga'
                plugin_repos.append(redhat_plugin_ga_repo)
                transformations.append("Added Red Hat GA plugin repository")
            
            if not redhat_plugin_ea_exists:
                redhat_plugin_ea_repo = ET.Element('pluginRepository')
                repo_id = ET.SubElement(redhat_plugin_ea_repo, 'id')
                repo_id.text = 'red-hat-earlyaccess-plugin-repository'
                repo_name = ET.SubElement(redhat_plugin_ea_repo, 'name')
                repo_name.text = 'Red Hat Early Access Plugin Repository'
                repo_url = ET.SubElement(redhat_plugin_ea_repo, 'url')
                repo_url.text = 'https://maven.repository.redhat.com/earlyaccess/all'
                plugin_repos.append(redhat_plugin_ea_repo)
                transformations.append("Added Red Hat Early Access plugin repository")
            
            # Write the transformed POM with proper namespace handling
            # Set the default namespace to avoid ns0: prefixes
            ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')
            
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty = reparsed.toprettyxml(indent="  ")
            
            # Clean up the XML output
            lines = []
            for line in pretty.split('\n'):
                if line.strip():  # Remove empty lines
                    # Remove ns0: prefixes for cleaner output
                    clean_line = line.replace('ns0:', '').replace(' xmlns:ns0="http://maven.apache.org/POM/4.0.0"', '')
                    lines.append(clean_line)
            
            # Fix XML declaration
            if lines and lines[0].startswith('<?xml'):
                lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
            
            with open(pom_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return json.dumps({
                "status": "success",
                "transformations": transformations,
                "dependencies_updated": len([t for t in transformations if "Transformed" in t]),
                "message": f"Successfully transformed {len(transformations)} dependency configurations"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to transform dependencies: {str(e)}"
            }, indent=2)
    
    def _transform_pom_structure_internal(self, pom_path: str) -> str:
        """Internal method for POM structural transformation - can be called directly"""
        try:
            import xml.etree.ElementTree as ET
            from xml.dom import minidom
            
            # Read the POM file
            tree = ET.parse(pom_path)
            root = tree.getroot()
            
            # Define namespace
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            transformations = []
            
            # 1. Change packaging from bundle to jar
            packaging_elem = root.find('.//maven:packaging', ns)
            if packaging_elem is not None and packaging_elem.text == 'bundle':
                packaging_elem.text = 'jar'
                transformations.append("Changed packaging from 'bundle' to 'jar'")
            
            # 2. Add Spring Boot parent (if not exists)
            parent_elem = root.find('./maven:parent', ns)
            if parent_elem is None:
                # Insert parent after modelVersion
                model_version = root.find('./maven:modelVersion', ns)
                parent = ET.Element('parent')
                parent_group = ET.SubElement(parent, 'groupId')
                parent_group.text = 'org.springframework.boot'
                parent_artifact = ET.SubElement(parent, 'artifactId')  
                parent_artifact.text = 'spring-boot-starter-parent'
                parent_version = ET.SubElement(parent, 'version')
                parent_version.text = '3.2.0'
                parent_relative = ET.SubElement(parent, 'relativePath')
                
                # Insert parent after modelVersion
                model_version_index = list(root).index(model_version)
                root.insert(model_version_index + 1, parent)
                transformations.append("Added Spring Boot parent POM")
            
            # 3. Update Java version in properties
            properties = root.find('./maven:properties', ns)
            if properties is not None:
                # Update Java version properties
                for java_prop in ['maven.compiler.source', 'maven.compiler.target', 'java.version']:
                    java_elem = properties.find(f'./maven:{java_prop}', ns)
                    if java_elem is not None:
                        if java_elem.text in ['1.7', '1.8', '11']:
                            java_elem.text = '21'
                            transformations.append(f"Updated {java_prop} to Java 21")
                    else:
                        # Add Java version property
                        new_elem = ET.SubElement(properties, java_prop)
                        new_elem.text = '21'
                        transformations.append(f"Added {java_prop} property with Java 21")
            
            # 4. Remove OSGi bundle plugin
            build = root.find('./maven:build', ns)
            if build is not None:
                plugins = build.find('./maven:plugins', ns)
                if plugins is not None:
                    for plugin in plugins.findall('./maven:plugin', ns):
                        artifact_id = plugin.find('./maven:artifactId', ns)
                        if artifact_id is not None and artifact_id.text == 'maven-bundle-plugin':
                            plugins.remove(plugin)
                            transformations.append("Removed maven-bundle-plugin")
                        elif artifact_id is not None and artifact_id.text == 'maven-compiler-plugin':
                            # Update compiler plugin version and Java version
                            version_elem = plugin.find('./maven:version', ns)
                            if version_elem is not None:
                                version_elem.text = '3.11.0'
                            config = plugin.find('./maven:configuration', ns)
                            if config is not None:
                                source = config.find('./maven:source', ns)
                                target = config.find('./maven:target', ns)
                                if source is not None:
                                    source.text = '21'
                                if target is not None:
                                    target.text = '21'
                                transformations.append("Updated maven-compiler-plugin for Java 21")
            
            # 5. Add Spring Boot Maven plugin
            if build is not None:
                plugins = build.find('./maven:plugins', ns)
                if plugins is not None:
                    # Check if Spring Boot plugin already exists
                    spring_boot_exists = False
                    for plugin in plugins.findall('./maven:plugin', ns):
                        group_id = plugin.find('./maven:groupId', ns)
                        artifact_id = plugin.find('./maven:artifactId', ns)
                        if (group_id is not None and group_id.text == 'org.springframework.boot' and
                            artifact_id is not None and artifact_id.text == 'spring-boot-maven-plugin'):
                            spring_boot_exists = True
                            break
                    
                    if not spring_boot_exists:
                        spring_boot_plugin = ET.Element('plugin')
                        group_id = ET.SubElement(spring_boot_plugin, 'groupId')
                        group_id.text = 'org.springframework.boot'
                        artifact_id = ET.SubElement(spring_boot_plugin, 'artifactId')
                        artifact_id.text = 'spring-boot-maven-plugin'
                        # Add version explicitly to ensure plugin resolution
                        version = ET.SubElement(spring_boot_plugin, 'version')
                        version.text = '3.2.0'
                        
                        # Add configuration section for executable JAR and repackage goal
                        configuration = ET.SubElement(spring_boot_plugin, 'configuration')
                        
                        # Add executions for repackage goal with proper phase
                        executions = ET.SubElement(spring_boot_plugin, 'executions')
                        execution = ET.SubElement(executions, 'execution')
                        # Add execution ID for clarity
                        exec_id = ET.SubElement(execution, 'id')
                        exec_id.text = 'repackage'
                        # Add phase - CRITICAL for executable JAR
                        phase = ET.SubElement(execution, 'phase')
                        phase.text = 'package'
                        # Add goals
                        goals = ET.SubElement(execution, 'goals')
                        goal = ET.SubElement(goals, 'goal')
                        goal.text = 'repackage'
                        
                        plugins.append(spring_boot_plugin)
                        transformations.append("Added Spring Boot Maven plugin v3.2.0 with repackage configuration")
            
            # Write the transformed POM with proper namespace handling
            # Set the default namespace to avoid ns0: prefixes
            ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')
            
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty = reparsed.toprettyxml(indent="  ")
            
            # Clean up the XML output
            lines = []
            for line in pretty.split('\n'):
                if line.strip():  # Remove empty lines
                    # Remove ns0: prefixes for cleaner output
                    clean_line = line.replace('ns0:', '').replace(' xmlns:ns0="http://maven.apache.org/POM/4.0.0"', '')
                    lines.append(clean_line)
            
            # Fix XML declaration
            if lines and lines[0].startswith('<?xml'):
                lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
            
            # Write to file
            with open(pom_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return json.dumps({
                "status": "success",
                "transformations": transformations,
                "pom_path": pom_path,
                "message": f"Successfully transformed POM structure with {len(transformations)} changes"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to transform POM structure: {str(e)}"
            }, indent=2)

    @tool("Transform POM Structure")
    def transform_pom_structure_tool(self, pom_path: str) -> str:
        """
        Transform complete POM structure from Fuse/OSGi bundle to Spring Boot application.
        
        Args:
            pom_path: Path to the pom.xml file
            
        Returns:
            JSON string with transformation results
        """
        return self._transform_pom_structure_internal(pom_path)
    
    def _get_component_dependency_mappings(self) -> Dict[str, str]:
        """
        Get mapping of Camel component names for dependency transformation
        
        Returns:
            Dictionary mapping old to new dependency coordinates
        """
        return {
            "camel-core": "camel-core-model",
            "camel-http4": "camel-http",
            "camel-jetty9": "camel-jetty",
            "camel-rabbitmq": "camel-spring-rabbitmq",
            "camel-kafka": "camel-kafka",
            "camel-activemq": "camel-jms"
        }
        
    def create_spring_boot_main_class_logic(self, project_path: str, package_name: str = None) -> str:
        """Core logic for creating Spring Boot main class - can be called directly"""
        try:
            import os
            from pathlib import Path
            import xml.etree.ElementTree as ET
            
            # If package name not provided, detect from POM
            if not package_name:
                pom_path = os.path.join(project_path, 'pom.xml')
                if os.path.exists(pom_path):
                    tree = ET.parse(pom_path)
                    root = tree.getroot()
                    ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
                    
                    # Try to get groupId
                    group_id_elem = root.find('./maven:groupId', ns)
                    if group_id_elem is None:
                        # Try parent groupId
                        group_id_elem = root.find('./maven:parent/maven:groupId', ns)
                    
                    if group_id_elem is not None:
                        package_name = group_id_elem.text
                    else:
                        package_name = "com.redhat.camel.demo"  # Default fallback
                else:
                    package_name = "com.redhat.camel.demo"  # Default fallback
            
            # Create package directory structure
            src_main_java = os.path.join(project_path, 'src', 'main', 'java')
            package_dirs = package_name.split('.')
            package_path = os.path.join(src_main_java, *package_dirs)
            
            # Create directories if they don't exist
            Path(package_path).mkdir(parents=True, exist_ok=True)
            
            # Create MainRunner.java
            main_class_path = os.path.join(package_path, 'MainRunner.java')
            
            main_class_content = f'''package {package_name};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Spring Boot Main Application Class
 * Generated for Red Hat build of Apache Camel 4.10 migration
 */
@SpringBootApplication
public class MainRunner {{

    public static void main(String[] args) {{
        SpringApplication.run(MainRunner.class, args);
    }}
}}
'''
            
            # Write the main class
            with open(main_class_path, 'w', encoding='utf-8') as f:
                f.write(main_class_content)
            
            # Now update the POM to include the main class in Spring Boot plugin
            pom_path = os.path.join(project_path, 'pom.xml')
            if os.path.exists(pom_path):
                tree = ET.parse(pom_path)
                root = tree.getroot()
                ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
                
                # Find Spring Boot plugin and add main class configuration
                build = root.find('./maven:build', ns)
                if build is not None:
                    plugins = build.find('./maven:plugins', ns)
                    if plugins is not None:
                        for plugin in plugins.findall('./maven:plugin', ns):
                            group_id = plugin.find('./maven:groupId', ns)
                            artifact_id = plugin.find('./maven:artifactId', ns)
                            
                            if (group_id is not None and group_id.text == 'org.springframework.boot' and
                                artifact_id is not None and artifact_id.text == 'spring-boot-maven-plugin'):
                                
                                # Add configuration with main class
                                config = plugin.find('./maven:configuration', ns)
                                if config is None:
                                    config = ET.SubElement(plugin, 'configuration')
                                
                                main_class = config.find('./maven:mainClass', ns)
                                if main_class is None:
                                    main_class = ET.SubElement(config, 'mainClass')
                                
                                main_class.text = f"{package_name}.MainRunner"
                                break
                
                # Write updated POM
                from xml.dom import minidom
                rough_string = ET.tostring(root, 'utf-8')
                reparsed = minidom.parseString(rough_string)
                pretty = reparsed.toprettyxml(indent="  ")
                
                # Clean up the XML output
                lines = []
                for line in pretty.split('\n'):
                    if line.strip():  # Remove empty lines
                        # Remove ns0: prefixes for cleaner output
                        clean_line = line.replace('ns0:', '').replace(' xmlns:ns0="http://maven.apache.org/POM/4.0.0"', '')
                        lines.append(clean_line)
                
                # Fix XML declaration
                if lines and lines[0].startswith('<?xml'):
                    lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
                
                with open(pom_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
            
            return json.dumps({
                "status": "success",
                "main_class_path": main_class_path,
                "package_name": package_name,
                "main_class": f"{package_name}.MainRunner",
                "message": f"Created Spring Boot main class at {main_class_path}"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to create Spring Boot main class: {str(e)}"
            }, indent=2)

    @tool("Create Spring Boot Main Class")
    def create_spring_boot_main_class_tool(self, project_path: str, package_name: str = None) -> str:
        """
        Creates a Spring Boot main class for the application.
        
        Args:
            project_path: Path to the project root
            package_name: Optional package name (e.g., 'mx.redhat.fuse.demo'). If not provided, will detect from POM
            
        Returns:
            JSON string with creation results
        """
        return self.create_spring_boot_main_class_logic(project_path, package_name)


def dependency_agent(state):
    """
    Dependency agent function for LangGraph workflow compatibility.
    Updates Maven dependencies from Fuse6/7 to Red Hat build of Camel 4.10.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with dependency migration results
    """
    try:
        # Get git repository path from previous git_agent
        git_repo_path = state.get("artifacts", {}).get("git_repo_path")
        if not git_repo_path:
            return {"error": "Git repository path not found from git_agent"}
        
        # Initialize dependency agent
        agent = DependencyAgent()

        # Find POM files in the repository
        import os
        from tools.code_tools import batch_files

        pom_files = []
        for root, dirs, files in os.walk(git_repo_path):
            for file in files:
                if file == "pom.xml":
                    pom_files.append(os.path.join(root, file))

        if not pom_files:
            return {"error": "No pom.xml files found in the repository"}

        tasks_completed = list(state.get("tasks_completed", []))
        artifacts = dict(state.get("artifacts", {}))

        # Solution 1: Batch processing for multi-module projects
        BATCH_SIZE = 5  # Process 5 POM files per batch
        pom_batches = batch_files(pom_files, BATCH_SIZE)

        print(f"Processing {len(pom_files)} POM files in {len(pom_batches)} batches...")

        # Update each POM file
        updated_poms = []
        for batch_idx, batch in enumerate(pom_batches):
            print(f"Processing batch {batch_idx + 1}/{len(pom_batches)} ({len(batch)} POMs)...")

            for pom_file in batch:
                try:
                    print(f"Processing POM: {pom_file}")

                    # STEP 1: Apply structural transformation (bundle→jar, add Spring Boot plugin, etc.)
                    from tools.maven_tools import parse_pom_file

                    # Check if this is a Fuse/OSGi bundle POM that needs structural transformation
                    pom_info = parse_pom_file(pom_file)
                    if pom_info.get("status") == "Success":
                        packaging = pom_info.get("packaging", "")
                        if packaging == "bundle" or "maven-bundle-plugin" in str(pom_info):
                            print(f"🔧 Applying structural transformation (OSGi bundle → Spring Boot)")
                            # Apply the transformation logic directly
                            import json
                            # Apply the transformation logic by calling the internal method
                            structural_result_str = agent._transform_pom_structure_internal(pom_file)
                            structural_result = json.loads(structural_result_str)
                            if structural_result.get("status") == "success":
                                print(f"✅ Structural transformation completed")
                                print(f"   Transformations: {', '.join(structural_result.get('transformations', []))}")
                            else:
                                print(f"⚠️  Structural transformation issues: {structural_result.get('message', 'Unknown')}")
                        else:
                            print(f"ℹ️  POM already has proper structure, skipping structural transformation")
                    else:
                        print(f"⚠️  Could not parse POM for structural analysis")

                    # STEP 2: Apply dependency updates
                    with open(pom_file, 'r') as f:
                        pom_content = f.read()

                    # Apply Red Hat Camel 4.10 dependency updates
                    updated_content = update_camel_dependencies_to_redhat_4_10(pom_content)

                    # Write updated content
                    if updated_content != pom_content:
                        with open(pom_file, 'w') as f:
                            f.write(updated_content)
                        updated_poms.append(pom_file)
                        print(f"✅ Updated POM: {pom_file}")
                    else:
                        print(f"ℹ️  No dependency changes needed: {pom_file}")
                        tasks_completed.append(f"Updated dependencies in: {os.path.relpath(pom_file, git_repo_path)}")

                except Exception as e:
                    tasks_completed.append(f"Error updating {os.path.relpath(pom_file, git_repo_path)}: {str(e)}")
        
        if updated_poms:
            tasks_completed.append(f"Successfully updated {len(updated_poms)} POM files for Red Hat Camel 4.10")
        else:
            tasks_completed.append("No dependency updates needed")
        
        artifacts.update({
            "dependency_migration": {
                "pom_files_found": len(pom_files),
                "pom_files_updated": len(updated_poms),
                "updated_files": updated_poms
            }
        })
        
        return {
            "tasks_completed": tasks_completed,
            "artifacts": artifacts
        }
        
    except Exception as e:
        return {"error": f"Dependency agent failed: {str(e)}"}


def update_camel_dependencies_to_redhat_4_10(pom_content: str) -> str:
    """
    Update POM content from Fuse6/7 dependencies to Red Hat build of Camel 4.10
    Based on Red Hat documentation: https://docs.redhat.com/en/documentation/red_hat_build_of_apache_camel/4.10
    """
    import re
    
    updated_content = pom_content
    
    # Update parent POM to Spring Boot parent
    parent_pattern = r'<parent>\s*<groupId>org\.apache\.camel\.springboot</groupId>\s*<artifactId>camel-spring-boot-bom</artifactId>\s*<version>[^<]+</version>\s*</parent>'
    spring_boot_parent = '''<parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>'''
    
    if re.search(parent_pattern, updated_content, re.MULTILINE):
        updated_content = re.sub(parent_pattern, spring_boot_parent, updated_content, flags=re.MULTILINE)
    
    # Update dependency management section with CORRECT Red Hat platform BOM
    bom_pattern = r'<dependencyManagement>.*?</dependencyManagement>'
    redhat_bom = '''<dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>com.redhat.camel.springboot.platform</groupId>
                <artifactId>camel-spring-boot-bom</artifactId>
                <version>4.10.3.redhat-00019</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>'''
    
    if re.search(bom_pattern, updated_content, re.MULTILINE | re.DOTALL):
        updated_content = re.sub(bom_pattern, redhat_bom, updated_content, flags=re.MULTILINE | re.DOTALL)
    
    # Track transformed dependencies to avoid duplicates
    transformed_dependencies = set()
    
    # Update specific Camel dependencies to Red Hat Spring Boot starters
    # Both camel-core and camel-spring should result in a single camel-spring-boot-starter
    dependency_mappings = {
        r'<groupId>org\.apache\.camel</groupId>\s*<artifactId>camel-core</artifactId>': 
            ('org.apache.camel.springboot', 'camel-spring-boot-starter'),
        r'<groupId>org\.apache\.camel</groupId>\s*<artifactId>camel-spring</artifactId>': 
            ('org.apache.camel.springboot', 'camel-spring-boot-starter'),
        r'<groupId>org\.apache\.camel</groupId>\s*<artifactId>camel-jackson</artifactId>': 
            ('org.apache.camel.springboot', 'camel-jackson-starter'),
        r'<groupId>org\.apache\.camel</groupId>\s*<artifactId>camel-test-spring</artifactId>': 
            ('org.apache.camel', 'camel-test-spring-junit5'),
        r'<groupId>org\.apache\.activemq</groupId>\s*<artifactId>activemq-camel</artifactId>': 
            ('org.apache.camel.springboot', 'camel-jms-starter')
    }
    
    # First remove all matched dependencies to avoid duplicates
    dependencies_to_remove = []
    for old_pattern, (new_group, new_artifact) in dependency_mappings.items():
        if re.search(old_pattern, updated_content, re.MULTILINE):
            dependencies_to_remove.append(old_pattern)
            transformed_dependencies.add((new_group, new_artifact))
            
            # Special case: camel-test-spring needs BOTH camel-test-spring-junit5 AND spring-boot-starter-test
            if 'camel-test-spring' in old_pattern:
                transformed_dependencies.add(('org.springframework.boot', 'spring-boot-starter-test'))
    
    # Remove all old dependencies that will be transformed
    for pattern in dependencies_to_remove:
        # Remove the entire dependency block
        full_pattern = r'<dependency>\s*' + pattern + r'.*?</dependency>'
        updated_content = re.sub(full_pattern, '', updated_content, flags=re.MULTILINE | re.DOTALL)
    
    # Only add Red Hat Camel dependencies - Spring Boot starter is not needed as per Red Hat docs
    
    # Add the transformed dependencies (no duplicates)
    if transformed_dependencies:
        dependency_insertions = []
        for group_id, artifact_id in transformed_dependencies:
            # Add scope=test for test dependencies
            if 'test' in artifact_id:
                dep_xml = f'''
        <dependency>
            <groupId>{group_id}</groupId>
            <artifactId>{artifact_id}</artifactId>
            <scope>test</scope>
        </dependency>'''
            else:
                dep_xml = f'''
        <dependency>
            <groupId>{group_id}</groupId>
            <artifactId>{artifact_id}</artifactId>
        </dependency>'''
            dependency_insertions.append(dep_xml)
        
        # Insert after the main <dependencies> tag (not in dependencyManagement)
        # Find all <dependencies> tags and use the one NOT inside <dependencyManagement>
        import re
        dep_mgmt_pattern = r'<dependencyManagement>.*?</dependencyManagement>'
        dep_mgmt_match = re.search(dep_mgmt_pattern, updated_content, re.DOTALL)
        
        if dep_mgmt_match:
            # Find dependencies section outside of dependencyManagement
            dep_mgmt_end = dep_mgmt_match.end()
            remaining_content = updated_content[dep_mgmt_end:]
            deps_start_in_remaining = remaining_content.find('<dependencies>')
            
            if deps_start_in_remaining != -1:
                actual_deps_start = dep_mgmt_end + deps_start_in_remaining
                deps_end = updated_content.find('>', actual_deps_start) + 1
                updated_content = updated_content[:deps_end] + ''.join(dependency_insertions) + updated_content[deps_end:]
            else:
                # No main dependencies section found, create one
                insertion_point = updated_content.find('</project>')
                if insertion_point != -1:
                    deps_section = '\n    <dependencies>' + ''.join(dependency_insertions) + '\n    </dependencies>\n'
                    updated_content = updated_content[:insertion_point] + deps_section + updated_content[insertion_point:]
        else:
            # No dependencyManagement, use first dependencies tag
            deps_start = updated_content.find('<dependencies>')
            if deps_start != -1:
                deps_end = updated_content.find('>', deps_start) + 1
                updated_content = updated_content[:deps_end] + ''.join(dependency_insertions) + updated_content[deps_end:]
    
    # Remove problematic dependencies that conflict with Spring Boot
    problematic_deps = [
        r'<dependency>\s*<groupId>log4j</groupId>\s*<artifactId>log4j</artifactId>.*?</dependency>',
        r'<dependency>\s*<groupId>org\.slf4j</groupId>\s*<artifactId>slf4j-log4j12</artifactId>.*?</dependency>',
        r'<dependency>\s*<groupId>org\.slf4j</groupId>\s*<artifactId>slf4j-api</artifactId>.*?</dependency>'
    ]
    
    for problematic_pattern in problematic_deps:
        updated_content = re.sub(problematic_pattern, '', updated_content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove version elements from Red Hat dependencies (managed by BOM)
    redhat_version_patterns = [
        r'(<groupId>org\.apache\.camel\.springboot</groupId>\s*<artifactId>[^<]+</artifactId>)\s*<version>[^<]+</version>',
        r'(<groupId>org\.apache\.camel</groupId>\s*<artifactId>camel-test-spring-junit5</artifactId>)\s*<version>[^<]+</version>'
    ]
    for pattern in redhat_version_patterns:
        updated_content = re.sub(pattern, r'\1', updated_content, flags=re.MULTILINE)
    
    
    # Update Camel version properties to correct version
    version_pattern = r'<camel\.version>[^<]+</camel\.version>'
    if re.search(version_pattern, updated_content):
        updated_content = re.sub(version_pattern, '<camel.version>4.10.3.redhat-00019</camel.version>', updated_content)
    
    # Add Red Hat repositories if not present (both GA and Early Access)
    if '<repositories>' not in updated_content:
        repo_section = '''
    <repositories>
        <repository>
            <id>redhat-ga</id>
            <name>Red Hat GA Repository</name>
            <url>https://maven.repository.redhat.com/ga</url>
            <releases>
                <enabled>true</enabled>
            </releases>
            <snapshots>
                <enabled>false</enabled>
            </snapshots>
        </repository>
        <repository>
            <id>redhat-earlyaccess</id>
            <name>Red Hat Early Access Repository</name>
            <url>https://maven.repository.redhat.com/earlyaccess/all</url>
            <releases>
                <enabled>true</enabled>
            </releases>
            <snapshots>
                <enabled>false</enabled>
            </snapshots>
        </repository>
    </repositories>'''
        
        # Insert before </project>
        updated_content = updated_content.replace('</project>', repo_section + '\n</project>')
    
    return updated_content