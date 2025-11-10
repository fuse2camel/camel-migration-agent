"""
Java AST Parser for migration transformations.

This module provides comprehensive Java source code parsing and transformation
capabilities using Abstract Syntax Trees (AST). It supports Java 7/8/11/17/21
syntax and enables precise code modifications while preserving formatting.
"""

import javalang
import re
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImportStatement:
    """Represents a Java import statement."""
    path: str
    static: bool = False
    wildcard: bool = False
    line_number: Optional[int] = None


@dataclass
class ClassInfo:
    """Information about a Java class."""
    name: str
    package: Optional[str]
    imports: List[ImportStatement]
    extends: Optional[str] = None
    implements: List[str] = None
    annotations: List[str] = None
    modifiers: Set[str] = None


@dataclass
class MethodInfo:
    """Information about a Java method."""
    name: str
    return_type: str
    parameters: List[Tuple[str, str]]  # [(type, name), ...]
    modifiers: Set[str]
    annotations: List[str]
    throws: List[str] = None


class JavaParser:
    """
    AST-based Java parser with transformation capabilities.

    Supports parsing Java source code into AST representation and provides
    utilities for code analysis and transformation across Java versions.
    """

    def __init__(self):
        """Initialize the Java parser."""
        self.tree = None
        self.source_code = None
        self.lines = []
        self.package_name = None
        self.imports = []

    def parse_file(self, file_path: str) -> bool:
        """
        Parse a Java source file.

        Args:
            file_path: Path to the Java source file

        Returns:
            True if parsing succeeded, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.source_code = f.read()
            return self.parse_source(self.source_code)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return False

    def parse_source(self, source_code: str) -> bool:
        """
        Parse Java source code string.

        Args:
            source_code: Java source code as string

        Returns:
            True if parsing succeeded, False otherwise
        """
        try:
            self.source_code = source_code
            self.lines = source_code.split('\n')
            self.tree = javalang.parse.parse(source_code)

            # Extract package and imports
            self.package_name = self.tree.package.name if self.tree.package else None
            self.imports = self._extract_imports()

            return True
        except javalang.parser.JavaSyntaxError as e:
            print(f"Java syntax error: {e}")
            return False
        except Exception as e:
            print(f"Error parsing Java source: {e}")
            return False

    def _extract_imports(self) -> List[ImportStatement]:
        """Extract all import statements from the parsed tree."""
        imports = []
        if self.tree and self.tree.imports:
            for imp in self.tree.imports:
                imports.append(ImportStatement(
                    path=imp.path,
                    static=imp.static,
                    wildcard=imp.wildcard
                ))
        return imports

    def get_class_info(self) -> List[ClassInfo]:
        """
        Extract information about all classes in the source.

        Returns:
            List of ClassInfo objects
        """
        classes = []
        if not self.tree:
            return classes

        for path, node in self.tree.filter(javalang.tree.ClassDeclaration):
            class_info = ClassInfo(
                name=node.name,
                package=self.package_name,
                imports=self.imports,
                extends=node.extends.name if node.extends else None,
                implements=[impl.name for impl in (node.implements or [])],
                annotations=[self._format_annotation(ann) for ann in (node.annotations or [])],
                modifiers=set(node.modifiers or [])
            )
            classes.append(class_info)

        return classes

    def get_method_info(self) -> List[MethodInfo]:
        """
        Extract information about all methods in the source.

        Returns:
            List of MethodInfo objects
        """
        methods = []
        if not self.tree:
            return methods

        for path, node in self.tree.filter(javalang.tree.MethodDeclaration):
            params = []
            if node.parameters:
                for param in node.parameters:
                    param_type = self._format_type(param.type)
                    params.append((param_type, param.name))

            method_info = MethodInfo(
                name=node.name,
                return_type=self._format_type(node.return_type) if node.return_type else 'void',
                parameters=params,
                modifiers=set(node.modifiers or []),
                annotations=[self._format_annotation(ann) for ann in (node.annotations or [])],
                throws=[t.name for t in (node.throws or [])]
            )
            methods.append(method_info)

        return methods

    def find_package_usage(self, package_prefix: str) -> List[str]:
        """
        Find all usages of a specific package prefix.

        Args:
            package_prefix: Package prefix to search for (e.g., 'javax.')

        Returns:
            List of full package paths found
        """
        usages = []

        # Check imports
        for imp in self.imports:
            if imp.path.startswith(package_prefix):
                usages.append(imp.path)

        # Check in source code for fully qualified names
        pattern = rf'\b{re.escape(package_prefix)}[\w.]+\b'
        matches = re.findall(pattern, self.source_code)
        usages.extend(matches)

        return list(set(usages))

    def find_annotations(self) -> List[str]:
        """
        Find all annotations used in the source code.

        Returns:
            List of annotation names
        """
        annotations = []
        if not self.tree:
            return annotations

        # Find annotations on classes, methods, fields
        for path, node in self.tree.filter(javalang.tree.Annotation):
            annotations.append(node.name)

        return list(set(annotations))

    def has_exchange_api_usage(self) -> bool:
        """
        Check if source uses Camel Exchange API patterns.

        Returns:
            True if Exchange API usage detected
        """
        patterns = [
            r'exchange\.getIn\(\)',
            r'exchange\.getOut\(\)',
            r'Message\s+in\s*=\s*exchange\.getIn',
            r'Message\s+out\s*=\s*exchange\.getOut'
        ]

        for pattern in patterns:
            if re.search(pattern, self.source_code):
                return True
        return False

    def find_lambda_candidates(self) -> List[Dict[str, Any]]:
        """
        Find anonymous inner classes that can be converted to lambdas.

        Returns:
            List of candidate locations with context
        """
        candidates = []

        # Pattern for simple anonymous classes with one method
        pattern = r'new\s+(\w+)\s*\(\s*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'

        for match in re.finditer(pattern, self.source_code):
            interface_name = match.group(1)
            body = match.group(2)

            # Check if it's a single method (common functional interface pattern)
            method_count = len(re.findall(r'public\s+\w+\s+\w+\s*\(', body))
            if method_count == 1:
                candidates.append({
                    'interface': interface_name,
                    'body': body.strip(),
                    'start': match.start(),
                    'end': match.end()
                })

        return candidates

    def _format_type(self, type_node) -> str:
        """Format a type node as a string."""
        if not type_node:
            return ''

        if isinstance(type_node, javalang.tree.ReferenceType):
            name = type_node.name
            if type_node.arguments:
                args = ', '.join(self._format_type(arg.type) for arg in type_node.arguments)
                return f"{name}<{args}>"
            return name
        elif isinstance(type_node, javalang.tree.BasicType):
            return type_node.name
        else:
            return str(type_node)

    def _format_annotation(self, annotation) -> str:
        """Format an annotation as a string."""
        if not annotation:
            return ''

        if isinstance(annotation, javalang.tree.Annotation):
            if annotation.element:
                return f"@{annotation.name}({annotation.element})"
            return f"@{annotation.name}"
        return str(annotation)

    def get_source_code(self) -> str:
        """Get the original source code."""
        return self.source_code

    def get_line(self, line_number: int) -> str:
        """Get a specific line from the source code."""
        if 0 <= line_number < len(self.lines):
            return self.lines[line_number]
        return ''


class JavaVersion:
    """Java version detection and feature support."""

    JAVA_7 = 7
    JAVA_8 = 8
    JAVA_11 = 11
    JAVA_17 = 17
    JAVA_21 = 21

    @staticmethod
    def detect_version(source_code: str) -> int:
        """
        Detect the minimum Java version required for the source code.

        Args:
            source_code: Java source code

        Returns:
            Minimum Java version number
        """
        version = JavaVersion.JAVA_7

        # Java 8 features
        if re.search(r'->', source_code):  # Lambda
            version = max(version, JavaVersion.JAVA_8)
        if re.search(r'::', source_code):  # Method reference
            version = max(version, JavaVersion.JAVA_8)
        if 'Optional<' in source_code:
            version = max(version, JavaVersion.JAVA_8)

        # Java 11+ features
        if 'var ' in source_code:
            version = max(version, JavaVersion.JAVA_11)

        # Java 17+ features
        if 'sealed class' in source_code or 'sealed interface' in source_code:
            version = max(version, JavaVersion.JAVA_17)

        # Java 21+ features
        if 'record ' in source_code:
            version = max(version, JavaVersion.JAVA_21)
        if re.search(r'String\s+\w+\s*=\s*"""', source_code):  # Text blocks
            version = max(version, JavaVersion.JAVA_21)
        if 'switch' in source_code and '->' in source_code:  # Switch expressions
            version = max(version, JavaVersion.JAVA_21)

        return version

    @staticmethod
    def supports_feature(version: int, feature: str) -> bool:
        """
        Check if a Java version supports a specific feature.

        Args:
            version: Java version number
            feature: Feature name ('lambda', 'records', 'var', etc.)

        Returns:
            True if feature is supported
        """
        feature_versions = {
            'lambda': JavaVersion.JAVA_8,
            'method_reference': JavaVersion.JAVA_8,
            'stream': JavaVersion.JAVA_8,
            'optional': JavaVersion.JAVA_8,
            'var': JavaVersion.JAVA_11,
            'sealed': JavaVersion.JAVA_17,
            'records': JavaVersion.JAVA_21,
            'text_blocks': JavaVersion.JAVA_21,
            'switch_expressions': JavaVersion.JAVA_21,
            'pattern_matching': JavaVersion.JAVA_21,
        }

        return version >= feature_versions.get(feature, JavaVersion.JAVA_21)


def parse_java_file(file_path: str) -> Optional[JavaParser]:
    """
    Convenience function to parse a Java file.

    Args:
        file_path: Path to Java source file

    Returns:
        JavaParser instance if successful, None otherwise
    """
    parser = JavaParser()
    if parser.parse_file(file_path):
        return parser
    return None


def find_javax_imports(file_path: str) -> List[str]:
    """
    Find all javax.* imports in a Java file.

    Args:
        file_path: Path to Java source file

    Returns:
        List of javax.* import paths
    """
    parser = parse_java_file(file_path)
    if parser:
        return parser.find_package_usage('javax.')
    return []
