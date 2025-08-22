"""
Tools Module for Camel Migration
Contains utility tools used by agents
"""

from .system_tools import (
    check_java_version,
    check_maven_version,
    check_git_version,
    check_docker_version,
    run_command
)

from .git_tools import (
    clone_repository,
    create_branch,
    commit_changes,
    push_changes
)

from .maven_tools import (
    update_pom_dependencies,
    run_maven_command,
    parse_pom_file
)

from .code_tools import (
    parse_xml_routes,
    convert_xml_to_java_dsl,
    refactor_java_code,
    analyze_java_files
)

from .docker_tools import (
    generate_dockerfile,
    build_docker_image
)

__all__ = [
    'check_java_version',
    'check_maven_version',
    'check_git_version',
    'check_docker_version',
    'run_command',
    'clone_repository',
    'create_branch',
    'commit_changes',
    'push_changes',
    'update_pom_dependencies',
    'run_maven_command',
    'parse_pom_file',
    'parse_xml_routes',
    'convert_xml_to_java_dsl',
    'refactor_java_code',
    'analyze_java_files',
    'generate_dockerfile',
    'build_docker_image'
]
