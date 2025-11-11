"""
Java Refactoring Utilities for Camel 4 Migration
Provides helper functions for transforming Java code from Camel 2/3 to Camel 4 APIs
"""

import re
from typing import List, Dict


def refactor_java_for_camel4(java_content: str) -> str:
    """
    Refactor Java code from Camel 2/3 to Camel 4 APIs.
    Based on Red Hat Camel 4.10 migration guidelines.

    Args:
        java_content: Original Java source code

    Returns:
        Refactored Java source code with Camel 4 APIs
    """
    refactored_content = java_content

    # Update Exchange API calls (most important change)
    refactored_content = re.sub(r'\.getIn\(\)', '.getMessage()', refactored_content)
    refactored_content = re.sub(r'\.getOut\(\)', '.getMessage()', refactored_content)

    # Update imports for relocated classes
    import_mappings = {
        'org.apache.camel.impl.DefaultCamelContext': 'org.apache.camel.CamelContext',
        'org.apache.camel.impl.SimpleRegistry': 'org.apache.camel.support.SimpleRegistry',
        'org.apache.camel.util.CamelContextHelper': 'org.apache.camel.support.CamelContextHelper',
        'org.apache.camel.impl.DefaultMessage': 'org.apache.camel.support.DefaultMessage',
        'org.apache.camel.impl.DefaultExchange': 'org.apache.camel.support.DefaultExchange'
    }

    for old_import, new_import in import_mappings.items():
        refactored_content = refactored_content.replace(
            f'import {old_import}',
            f'import {new_import}'
        )

    # Update component URIs that changed in Camel 4
    uri_mappings = {
        'http4:': 'http:',
        'jetty9:': 'jetty:',
        'netty4:': 'netty:'
    }

    for old_uri, new_uri in uri_mappings.items():
        refactored_content = refactored_content.replace(f'"{old_uri}', f'"{new_uri}')
        refactored_content = refactored_content.replace(f"'{old_uri}", f"'{new_uri}")

    # Update deprecated method calls
    refactored_content = refactored_content.replace(
        '.getContext().getRegistry()',
        '.getCamelContext().getRegistry()'
    )

    # Add Spring Boot annotations for modern Camel 4
    if 'extends RouteBuilder' in refactored_content and '@Component' not in refactored_content:
        # Add @Component annotation to RouteBuilder classes (any class name)
        refactored_content = re.sub(
            r'(public class \w+ extends RouteBuilder)',
            r'@Component\n\1',
            refactored_content
        )

        # Add import for @Component if not present
        if 'import org.springframework.stereotype.Component' not in refactored_content:
            if 'import org.apache.camel' in refactored_content:
                refactored_content = refactored_content.replace(
                    'import org.apache.camel',
                    'import org.springframework.stereotype.Component;\nimport org.apache.camel',
                    1  # Only replace first occurrence
                )

    return refactored_content


def is_file_already_camel4(java_content: str) -> bool:
    """
    Check if a Java file already uses Camel 4 APIs.

    Args:
        java_content: Java file content

    Returns:
        True if file appears to already be using Camel 4 patterns
    """
    # Check for Camel 4 patterns
    has_get_message = '.getMessage()' in java_content

    # Check for old Camel 2/3 patterns
    has_get_in = '.getIn()' in java_content
    has_get_out = '.getOut()' in java_content
    has_old_uris = any(uri in java_content for uri in ['http4:', 'jetty9:', 'netty4:'])
    has_old_imports = 'org.apache.camel.impl.' in java_content

    # If it has old patterns, it needs migration
    if has_get_in or has_get_out or has_old_uris or has_old_imports:
        return False

    # If it has getMessage() and no old patterns, it's likely Camel 4
    if has_get_message:
        return True

    # For RouteBuilder classes without Exchange API usage:
    # Check if they have any migration indicators
    if 'extends RouteBuilder' in java_content:
        # If no old patterns and has modern Spring annotations, likely OK
        if '@Component' in java_content:
            return True
        # Otherwise, unclear - let migration process handle it
        return False

    # For non-RouteBuilder classes without Exchange API, assume OK
    return True


def analyze_refactoring_changes(original: str, refactored: str) -> List[str]:
    """
    Analyze what changes were made during refactoring.

    Args:
        original: Original Java content
        refactored: Refactored Java content

    Returns:
        List of change descriptions
    """
    changes = []

    if '.getIn()' in original and '.getMessage()' in refactored:
        changes.append("Updated Exchange.getIn() to getMessage() for Camel 4 compatibility")

    if '.getOut()' in original and '.getMessage()' in refactored:
        changes.append("Updated Exchange.getOut() to getMessage() for Camel 4 compatibility")

    if 'http4:' in original and 'http:' in refactored:
        changes.append("Updated HTTP component URI from http4: to http:")

    if 'jetty9:' in original and 'jetty:' in refactored:
        changes.append("Updated Jetty component URI from jetty9: to jetty:")

    if 'netty4:' in original and 'netty:' in refactored:
        changes.append("Updated Netty component URI from netty4: to netty:")

    if '@Component' in refactored and '@Component' not in original:
        changes.append("Added @Component annotation for Spring Boot integration")

    if 'org.apache.camel.impl.' in original and 'org.apache.camel.support.' in refactored:
        changes.append("Updated imports for relocated Camel support classes")

    if '.getContext().getRegistry()' in original and '.getCamelContext().getRegistry()' in refactored:
        changes.append("Updated deprecated getContext() to getCamelContext()")

    return changes


