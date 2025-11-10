"""
Configuration File Parser for migration transformations.

This module provides parsing and transformation capabilities for various
configuration file formats used in Spring Boot and Camel applications.
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import OrderedDict


class PropertiesParser:
    """
    Parser for .properties files with comment preservation.
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the properties parser.

        Args:
            file_path: Optional path to properties file
        """
        self.file_path = file_path
        self.properties: OrderedDict[str, str] = OrderedDict()
        self.comments: Dict[str, List[str]] = {}
        self.lines: List[str] = []

    def parse(self, content: Optional[str] = None) -> Dict[str, str]:
        """
        Parse properties file content.

        Args:
            content: Optional content string. If None, reads from file_path

        Returns:
            Dictionary of properties
        """
        if content is None:
            if self.file_path is None:
                raise ValueError("Either content or file_path must be provided")
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        self.lines = content.split('\n')
        self.properties = OrderedDict()
        self.comments = {}

        current_comments = []

        for line_num, line in enumerate(self.lines):
            stripped = line.strip()

            # Handle comments
            if stripped.startswith('#') or stripped.startswith('!'):
                current_comments.append(line)
                continue

            # Handle blank lines
            if not stripped:
                current_comments = []
                continue

            # Parse property
            if '=' in stripped or ':' in stripped:
                # Split on first occurrence of = or :
                separator = '=' if '=' in stripped else ':'
                key, value = stripped.split(separator, 1)
                key = key.strip()
                value = value.strip()

                self.properties[key] = value
                if current_comments:
                    self.comments[key] = current_comments
                    current_comments = []

        return dict(self.properties)

    def get_property(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a property value.

        Args:
            key: Property key
            default: Default value if key not found

        Returns:
            Property value or default
        """
        return self.properties.get(key, default)

    def set_property(self, key: str, value: str, comment: Optional[str] = None):
        """
        Set a property value.

        Args:
            key: Property key
            value: Property value
            comment: Optional comment for the property
        """
        self.properties[key] = value
        if comment:
            self.comments[key] = [f"# {comment}"]

    def rename_property(self, old_key: str, new_key: str) -> bool:
        """
        Rename a property key.

        Args:
            old_key: Old property key
            new_key: New property key

        Returns:
            True if property was renamed
        """
        if old_key in self.properties:
            value = self.properties[old_key]
            comments = self.comments.get(old_key, [])

            # Remove old
            del self.properties[old_key]
            if old_key in self.comments:
                del self.comments[old_key]

            # Add new
            self.properties[new_key] = value
            if comments:
                self.comments[new_key] = comments

            return True
        return False

    def remove_property(self, key: str) -> bool:
        """
        Remove a property.

        Args:
            key: Property key to remove

        Returns:
            True if property was removed
        """
        if key in self.properties:
            del self.properties[key]
            if key in self.comments:
                del self.comments[key]
            return True
        return False

    def to_string(self) -> str:
        """
        Convert properties back to string format.

        Returns:
            Properties file content as string
        """
        lines = []

        for key, value in self.properties.items():
            # Add comments if present
            if key in self.comments:
                lines.extend(self.comments[key])

            # Add property
            lines.append(f"{key}={value}")
            lines.append("")  # Blank line for readability

        return '\n'.join(lines)

    def save(self, file_path: Optional[str] = None):
        """
        Save properties to file.

        Args:
            file_path: Optional file path. Uses self.file_path if None
        """
        path = file_path or self.file_path
        if path is None:
            raise ValueError("File path must be provided")

        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_string())


class YamlParser:
    """
    Parser for YAML files with comment preservation.
    Uses ruamel.yaml for comment preservation.
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the YAML parser.

        Args:
            file_path: Optional path to YAML file
        """
        try:
            from ruamel.yaml import YAML
            self.yaml = YAML()
            self.yaml.preserve_quotes = True
            self.yaml.default_flow_style = False
        except ImportError:
            raise ImportError("ruamel.yaml is required for YAML parsing. Install it with: pip install ruamel.yaml")

        self.file_path = file_path
        self.data = None

    def parse(self, content: Optional[str] = None) -> Dict:
        """
        Parse YAML content.

        Args:
            content: Optional YAML content string. If None, reads from file_path

        Returns:
            Parsed YAML data as dictionary
        """
        if content is None:
            if self.file_path is None:
                raise ValueError("Either content or file_path must be provided")
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = self.yaml.load(f)
        else:
            from io import StringIO
            self.data = self.yaml.load(StringIO(content))

        return self.data

    def get_value(self, path: str, default=None):
        """
        Get a value from YAML using dot notation.

        Args:
            path: Dot-separated path (e.g., 'spring.datasource.url')
            default: Default value if path not found

        Returns:
            Value at path or default
        """
        if self.data is None:
            return default

        keys = path.split('.')
        current = self.data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def set_value(self, path: str, value):
        """
        Set a value in YAML using dot notation.

        Args:
            path: Dot-separated path (e.g., 'spring.datasource.url')
            value: Value to set
        """
        if self.data is None:
            self.data = {}

        keys = path.split('.')
        current = self.data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def rename_key(self, old_path: str, new_path: str) -> bool:
        """
        Rename a YAML key.

        Args:
            old_path: Old dot-separated path
            new_path: New dot-separated path

        Returns:
            True if key was renamed
        """
        value = self.get_value(old_path)
        if value is not None:
            self.set_value(new_path, value)
            self.remove_value(old_path)
            return True
        return False

    def remove_value(self, path: str) -> bool:
        """
        Remove a value from YAML.

        Args:
            path: Dot-separated path

        Returns:
            True if value was removed
        """
        if self.data is None:
            return False

        keys = path.split('.')
        current = self.data

        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False

        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            return True

        return False

    def to_string(self) -> str:
        """
        Convert YAML data back to string.

        Returns:
            YAML content as string
        """
        from io import StringIO
        stream = StringIO()
        self.yaml.dump(self.data, stream)
        return stream.getvalue()

    def save(self, file_path: Optional[str] = None):
        """
        Save YAML to file.

        Args:
            file_path: Optional file path. Uses self.file_path if None
        """
        path = file_path or self.file_path
        if path is None:
            raise ValueError("File path must be provided")

        with open(path, 'w', encoding='utf-8') as f:
            self.yaml.dump(self.data, f)


class SpringBootPropertyMigrator:
    """
    Migrate Spring Boot properties from 2.x to 3.x.
    """

    # Property mappings from Spring Boot 2.x to 3.x
    PROPERTY_MAPPINGS = {
        'server.use-forward-headers': 'server.forward-headers-strategy',
        'server.max-http-header-size': 'server.max-http-request-header-size',
        'spring.resources.static-locations': 'spring.web.resources.static-locations',
        'spring.resources.cache.period': 'spring.web.resources.cache.period',
        'spring.resources.cache.cachecontrol': 'spring.web.resources.cache.cachecontrol',
        'spring.resources.chain.enabled': 'spring.web.resources.chain.enabled',
        'spring.mvc.locale': 'spring.web.locale',
        'spring.mvc.locale-resolver': 'spring.web.locale-resolver',
    }

    # Value transformations
    VALUE_TRANSFORMATIONS = {
        'server.forward-headers-strategy': {
            'true': 'framework',
            'false': 'none'
        }
    }

    @staticmethod
    def migrate_properties(properties_parser: PropertiesParser) -> int:
        """
        Migrate Spring Boot properties.

        Args:
            properties_parser: PropertiesParser instance

        Returns:
            Number of properties migrated
        """
        count = 0

        for old_key, new_key in SpringBootPropertyMigrator.PROPERTY_MAPPINGS.items():
            if old_key in properties_parser.properties:
                old_value = properties_parser.get_property(old_key)

                # Apply value transformation if needed
                if new_key in SpringBootPropertyMigrator.VALUE_TRANSFORMATIONS:
                    transformations = SpringBootPropertyMigrator.VALUE_TRANSFORMATIONS[new_key]
                    new_value = transformations.get(old_value, old_value)
                else:
                    new_value = old_value

                # Rename property
                properties_parser.rename_property(old_key, new_key)
                if old_value != new_value:
                    properties_parser.set_property(new_key, new_value)

                count += 1

        return count

    @staticmethod
    def migrate_yaml(yaml_parser: YamlParser) -> int:
        """
        Migrate Spring Boot YAML configuration.

        Args:
            yaml_parser: YamlParser instance

        Returns:
            Number of properties migrated
        """
        count = 0

        for old_key, new_key in SpringBootPropertyMigrator.PROPERTY_MAPPINGS.items():
            if yaml_parser.get_value(old_key) is not None:
                old_value = yaml_parser.get_value(old_key)

                # Apply value transformation if needed
                if new_key in SpringBootPropertyMigrator.VALUE_TRANSFORMATIONS:
                    transformations = SpringBootPropertyMigrator.VALUE_TRANSFORMATIONS[new_key]
                    new_value = transformations.get(str(old_value), old_value)
                else:
                    new_value = old_value

                # Rename key
                yaml_parser.rename_key(old_key, new_key)
                if old_value != new_value:
                    yaml_parser.set_value(new_key, new_value)

                count += 1

        return count


def migrate_application_properties(file_path: str, backup: bool = True) -> Dict[str, any]:
    """
    Migrate application.properties file from Spring Boot 2.x to 3.x.

    Args:
        file_path: Path to application.properties file
        backup: Whether to create a backup file

    Returns:
        Migration results dictionary
    """
    try:
        # Create backup if requested
        if backup:
            import shutil
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)

        # Parse and migrate
        parser = PropertiesParser(file_path)
        parser.parse()

        count = SpringBootPropertyMigrator.migrate_properties(parser)

        # Save if changes were made
        if count > 0:
            parser.save()

        return {
            "status": "success",
            "file": file_path,
            "properties_migrated": count,
            "backup_created": backup
        }
    except Exception as e:
        return {
            "status": "error",
            "file": file_path,
            "error": str(e)
        }


def migrate_application_yaml(file_path: str, backup: bool = True) -> Dict[str, any]:
    """
    Migrate application.yml file from Spring Boot 2.x to 3.x.

    Args:
        file_path: Path to application.yml file
        backup: Whether to create a backup file

    Returns:
        Migration results dictionary
    """
    try:
        # Create backup if requested
        if backup:
            import shutil
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)

        # Parse and migrate
        parser = YamlParser(file_path)
        parser.parse()

        count = SpringBootPropertyMigrator.migrate_yaml(parser)

        # Save if changes were made
        if count > 0:
            parser.save()

        return {
            "status": "success",
            "file": file_path,
            "properties_migrated": count,
            "backup_created": backup
        }
    except Exception as e:
        return {
            "status": "error",
            "file": file_path,
            "error": str(e)
        }
