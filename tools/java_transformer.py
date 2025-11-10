"""
Java Code Transformation Engine.

This module provides format-preserving code transformations for Java migration.
It maintains comments, whitespace, and formatting while performing precise
code modifications based on agent decisions.
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Transformation:
    """Represents a code transformation."""
    start_pos: int
    end_pos: int
    old_text: str
    new_text: str
    description: str
    confidence: float = 1.0


class JavaTransformer:
    """
    Format-preserving code transformation engine.

    Applies transformations to Java source code while maintaining formatting,
    comments, and code structure.
    """

    def __init__(self, source_code: str):
        """
        Initialize the transformer with source code.

        Args:
            source_code: Original Java source code
        """
        self.original_source = source_code
        self.current_source = source_code
        self.transformations: List[Transformation] = []
        self.applied_transformations: List[Transformation] = []

    def replace_import(self, old_import: str, new_import: str, description: str = "") -> bool:
        """
        Replace an import statement.

        Args:
            old_import: Old import path (e.g., 'javax.persistence.*')
            new_import: New import path (e.g., 'jakarta.persistence.*')
            description: Description of the transformation

        Returns:
            True if replacement was found and queued
        """
        pattern = rf'import\s+{re.escape(old_import)}\s*;'
        replacement = f'import {new_import};'

        for match in re.finditer(pattern, self.current_source):
            self.transformations.append(Transformation(
                start_pos=match.start(),
                end_pos=match.end(),
                old_text=match.group(0),
                new_text=replacement,
                description=description or f"Replace import {old_import} -> {new_import}"
            ))

        return len(self.transformations) > 0

    def replace_package_reference(self, old_package: str, new_package: str) -> int:
        """
        Replace all references to a package in the code.

        Args:
            old_package: Old package path (e.g., 'javax.persistence')
            new_package: New package path (e.g., 'jakarta.persistence')

        Returns:
            Number of replacements found
        """
        count = 0

        # Find fully qualified references
        pattern = rf'\b{re.escape(old_package)}\b'

        for match in re.finditer(pattern, self.current_source):
            # Check if it's not in a comment
            if not self._is_in_comment(match.start()):
                self.transformations.append(Transformation(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    old_text=old_package,
                    new_text=new_package,
                    description=f"Replace package reference {old_package} -> {new_package}"
                ))
                count += 1

        return count

    def replace_method_call(self, old_method: str, new_method: str,
                           context_pattern: Optional[str] = None) -> int:
        """
        Replace method calls.

        Args:
            old_method: Old method name (e.g., 'getIn')
            new_method: New method name (e.g., 'getMessage')
            context_pattern: Optional regex pattern for context matching

        Returns:
            Number of replacements found
        """
        count = 0

        # Pattern for method call
        pattern = rf'\.{re.escape(old_method)}\s*\('

        for match in re.finditer(pattern, self.current_source):
            if not self._is_in_comment(match.start()):
                # Apply context filter if provided
                if context_pattern:
                    context_start = max(0, match.start() - 100)
                    context = self.current_source[context_start:match.end()]
                    if not re.search(context_pattern, context):
                        continue

                # Find the full method call including the dot
                old_text = match.group(0)
                new_text = f'.{new_method}('

                self.transformations.append(Transformation(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    old_text=old_text,
                    new_text=new_text,
                    description=f"Replace method call {old_method}() -> {new_method}()"
                ))
                count += 1

        return count

    def replace_annotation(self, old_annotation: str, new_annotation: str) -> int:
        """
        Replace annotation usage.

        Args:
            old_annotation: Old annotation (e.g., '@NotNull')
            new_annotation: New annotation (e.g., '@jakarta.validation.constraints.NotNull')

        Returns:
            Number of replacements found
        """
        count = 0

        # Handle both simple and fully qualified annotations
        old_simple = old_annotation.lstrip('@')
        pattern = rf'@{re.escape(old_simple)}\b'

        for match in re.finditer(pattern, self.current_source):
            if not self._is_in_comment(match.start()):
                self.transformations.append(Transformation(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    old_text=match.group(0),
                    new_text=new_annotation if new_annotation.startswith('@') else f'@{new_annotation}',
                    description=f"Replace annotation {old_annotation} -> {new_annotation}"
                ))
                count += 1

        return count

    def convert_anonymous_to_lambda(self, interface_name: str,
                                    method_name: str,
                                    start_pos: int,
                                    end_pos: int,
                                    lambda_expr: str) -> bool:
        """
        Convert anonymous inner class to lambda expression.

        Args:
            interface_name: Functional interface name
            method_name: Method being implemented
            start_pos: Start position of anonymous class
            end_pos: End position of anonymous class
            lambda_expr: Lambda expression replacement

        Returns:
            True if transformation was queued
        """
        old_text = self.current_source[start_pos:end_pos]

        self.transformations.append(Transformation(
            start_pos=start_pos,
            end_pos=end_pos,
            old_text=old_text,
            new_text=lambda_expr,
            description=f"Convert {interface_name} anonymous class to lambda"
        ))

        return True

    def add_import(self, import_path: str) -> bool:
        """
        Add a new import statement.

        Args:
            import_path: Import path to add

        Returns:
            True if import was added
        """
        # Check if import already exists
        if f'import {import_path};' in self.current_source:
            return False

        # Find the last import statement
        import_pattern = r'import\s+[\w.]+\s*;'
        matches = list(re.finditer(import_pattern, self.current_source))

        if matches:
            # Insert after the last import
            last_import = matches[-1]
            insert_pos = last_import.end()
            new_text = f'\nimport {import_path};'
        else:
            # Find package declaration and insert after it
            package_match = re.search(r'package\s+[\w.]+\s*;', self.current_source)
            if package_match:
                insert_pos = package_match.end()
                new_text = f'\n\nimport {import_path};'
            else:
                # Insert at the beginning
                insert_pos = 0
                new_text = f'import {import_path};\n\n'

        self.transformations.append(Transformation(
            start_pos=insert_pos,
            end_pos=insert_pos,
            old_text='',
            new_text=new_text,
            description=f"Add import {import_path}"
        ))

        return True

    def remove_import(self, import_path: str) -> bool:
        """
        Remove an import statement.

        Args:
            import_path: Import path to remove

        Returns:
            True if import was found and queued for removal
        """
        pattern = rf'import\s+{re.escape(import_path)}\s*;\n?'

        for match in re.finditer(pattern, self.current_source):
            self.transformations.append(Transformation(
                start_pos=match.start(),
                end_pos=match.end(),
                old_text=match.group(0),
                new_text='',
                description=f"Remove import {import_path}"
            ))
            return True

        return False

    def replace_text(self, old_text: str, new_text: str, description: str = "") -> int:
        """
        Replace exact text occurrences.

        Args:
            old_text: Text to replace
            new_text: Replacement text
            description: Description of the transformation

        Returns:
            Number of replacements found
        """
        count = 0

        for match in re.finditer(re.escape(old_text), self.current_source):
            if not self._is_in_comment(match.start()):
                self.transformations.append(Transformation(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    old_text=old_text,
                    new_text=new_text,
                    description=description or f"Replace text"
                ))
                count += 1

        return count

    def apply_transformations(self) -> str:
        """
        Apply all queued transformations.

        Returns:
            Transformed source code
        """
        if not self.transformations:
            return self.current_source

        # Sort transformations by position (reverse order to maintain positions)
        sorted_transforms = sorted(self.transformations,
                                   key=lambda t: t.start_pos,
                                   reverse=True)

        result = self.current_source

        for transform in sorted_transforms:
            # Apply the transformation
            result = (result[:transform.start_pos] +
                     transform.new_text +
                     result[transform.end_pos:])

            self.applied_transformations.append(transform)

        self.current_source = result
        self.transformations = []

        return result

    def get_transformation_report(self) -> str:
        """
        Generate a report of all applied transformations.

        Returns:
            Human-readable transformation report
        """
        if not self.applied_transformations:
            return "No transformations applied."

        report = ["Transformation Report", "=" * 50, ""]

        for i, transform in enumerate(self.applied_transformations, 1):
            report.append(f"{i}. {transform.description}")
            report.append(f"   Old: {transform.old_text[:50]}...")
            report.append(f"   New: {transform.new_text[:50]}...")
            report.append(f"   Confidence: {transform.confidence:.2%}")
            report.append("")

        return "\n".join(report)

    def reset(self):
        """Reset to original source code and clear transformations."""
        self.current_source = self.original_source
        self.transformations = []
        self.applied_transformations = []

    def _is_in_comment(self, position: int) -> bool:
        """
        Check if a position is inside a comment.

        Args:
            position: Character position in source code

        Returns:
            True if position is in a comment
        """
        # Check for line comments
        line_start = self.current_source.rfind('\n', 0, position) + 1
        line_to_pos = self.current_source[line_start:position]

        if '//' in line_to_pos:
            return True

        # Check for block comments (simplified)
        before_pos = self.current_source[:position]
        last_block_start = before_pos.rfind('/*')
        last_block_end = before_pos.rfind('*/')

        if last_block_start > last_block_end:
            return True

        return False

    def get_current_source(self) -> str:
        """Get the current source code."""
        return self.current_source


class BatchTransformer:
    """
    Batch transformation utilities for multiple files.
    """

    @staticmethod
    def transform_files(file_paths: List[str],
                       transformation_func,
                       backup: bool = True) -> Dict[str, bool]:
        """
        Apply transformations to multiple files.

        Args:
            file_paths: List of file paths to transform
            transformation_func: Function that takes JavaTransformer and applies transformations
            backup: Whether to create backup files

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}

        for file_path in file_paths:
            try:
                # Read source
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()

                # Create backup if requested
                if backup:
                    backup_path = f"{file_path}.backup"
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(source)

                # Transform
                transformer = JavaTransformer(source)
                transformation_func(transformer)
                transformed = transformer.apply_transformations()

                # Write result
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(transformed)

                results[file_path] = True

            except Exception as e:
                print(f"Error transforming {file_path}: {e}")
                results[file_path] = False

        return results


def create_transformer(source_code: str) -> JavaTransformer:
    """
    Convenience function to create a JavaTransformer.

    Args:
        source_code: Java source code

    Returns:
        JavaTransformer instance
    """
    return JavaTransformer(source_code)
