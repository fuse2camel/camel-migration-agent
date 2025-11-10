"""
XML Configuration Parser for Jakarta EE migration.

This module provides parsing and transformation capabilities for XML
configuration files like persistence.xml, web.xml, beans.xml, etc.
"""

from lxml import etree
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class XmlConfigParser:
    """
    Parser for XML configuration files with namespace handling.
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the XML configuration parser.

        Args:
            file_path: Optional path to XML file
        """
        self.file_path = file_path
        self.tree = None
        self.root = None
        self.namespaces = {}

    def parse(self, content: Optional[str] = None) -> etree.Element:
        """
        Parse XML content.

        Args:
            content: Optional XML content string. If None, reads from file_path

        Returns:
            Root element of the parsed XML
        """
        if content is None:
            if self.file_path is None:
                raise ValueError("Either content or file_path must be provided")
            self.tree = etree.parse(self.file_path)
        else:
            self.tree = etree.fromstring(content.encode('utf-8'))

        self.root = self.tree.getroot() if hasattr(self.tree, 'getroot') else self.tree
        self.namespaces = self._extract_namespaces()

        return self.root

    def _extract_namespaces(self) -> Dict[str, str]:
        """
        Extract namespace mappings from the XML.

        Returns:
            Dictionary of namespace prefixes to URIs
        """
        return dict(self.root.nsmap) if hasattr(self.root, 'nsmap') else {}

    def get_namespace_uri(self, prefix: Optional[str] = None) -> Optional[str]:
        """
        Get namespace URI for a prefix.

        Args:
            prefix: Namespace prefix. None for default namespace

        Returns:
            Namespace URI or None
        """
        return self.namespaces.get(prefix)

    def update_namespace(self, old_uri: str, new_uri: str) -> int:
        """
        Update namespace URI throughout the document.

        Args:
            old_uri: Old namespace URI
            new_uri: New namespace URI

        Returns:
            Number of elements updated
        """
        count = 0

        # Update root namespace
        if self.root.nsmap.get(None) == old_uri:
            # Create new root with updated namespace
            new_nsmap = dict(self.root.nsmap)
            new_nsmap[None] = new_uri

            new_root = etree.Element(
                self.root.tag.replace(f'{{{old_uri}}}', f'{{{new_uri}}}'),
                nsmap=new_nsmap,
                attrib=self.root.attrib
            )

            # Copy children
            for child in self.root:
                new_root.append(child)

            self.root = new_root
            self.tree = etree.ElementTree(self.root)
            count += 1

        # Update all elements
        for elem in self.root.iter():
            if elem.tag.startswith(f'{{{old_uri}}}'):
                elem.tag = elem.tag.replace(f'{{{old_uri}}}', f'{{{new_uri}}}')
                count += 1

        # Update namespace map
        self.namespaces = self._extract_namespaces()

        return count

    def update_schema_location(self, old_xsd: str, new_xsd: str) -> bool:
        """
        Update xsi:schemaLocation attribute.

        Args:
            old_xsd: Old schema file name
            new_xsd: New schema file name

        Returns:
            True if schema location was updated
        """
        schema_loc_attr = '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'

        if schema_loc_attr in self.root.attrib:
            old_value = self.root.attrib[schema_loc_attr]
            new_value = old_value.replace(old_xsd, new_xsd)
            self.root.attrib[schema_loc_attr] = new_value
            return old_value != new_value

        return False

    def find_elements(self, xpath: str) -> List[etree.Element]:
        """
        Find elements using XPath.

        Args:
            xpath: XPath expression

        Returns:
            List of matching elements
        """
        return self.root.xpath(xpath, namespaces=self.namespaces)

    def to_string(self, pretty_print: bool = True) -> str:
        """
        Convert XML back to string.

        Args:
            pretty_print: Whether to format with indentation

        Returns:
            XML content as string
        """
        return etree.tostring(
            self.root if not hasattr(self.tree, 'getroot') else self.tree.getroot(),
            encoding='unicode',
            pretty_print=pretty_print,
            xml_declaration=True
        )

    def save(self, file_path: Optional[str] = None, pretty_print: bool = True):
        """
        Save XML to file.

        Args:
            file_path: Optional file path. Uses self.file_path if None
            pretty_print: Whether to format with indentation
        """
        path = file_path or self.file_path
        if path is None:
            raise ValueError("File path must be provided")

        if hasattr(self.tree, 'write'):
            self.tree.write(
                path,
                encoding='utf-8',
                xml_declaration=True,
                pretty_print=pretty_print
            )
        else:
            with open(path, 'wb') as f:
                f.write(etree.tostring(
                    self.root,
                    encoding='utf-8',
                    xml_declaration=True,
                    pretty_print=pretty_print
                ))


class JakartaXmlMigrator:
    """
    Migrate XML configuration files from Java EE to Jakarta EE.
    """

    # Namespace migrations
    NAMESPACE_MAPPINGS = {
        'http://xmlns.jcp.org/xml/ns/persistence': 'https://jakarta.ee/xml/ns/persistence',
        'http://xmlns.jcp.org/xml/ns/javaee': 'https://jakarta.ee/xml/ns/jakartaee',
        'http://java.sun.com/xml/ns/persistence': 'https://jakarta.ee/xml/ns/persistence',
        'http://java.sun.com/xml/ns/javaee': 'https://jakarta.ee/xml/ns/jakartaee',
    }

    # Schema version updates
    SCHEMA_MAPPINGS = {
        'persistence_2_0.xsd': 'persistence_3_0.xsd',
        'persistence_2_1.xsd': 'persistence_3_0.xsd',
        'persistence_2_2.xsd': 'persistence_3_0.xsd',
        'web-app_3_0.xsd': 'web-app_5_0.xsd',
        'web-app_3_1.xsd': 'web-app_5_0.xsd',
        'web-app_4_0.xsd': 'web-app_5_0.xsd',
    }

    # Version attribute updates
    VERSION_UPDATES = {
        'persistence.xml': {
            '2.0': '3.0',
            '2.1': '3.0',
            '2.2': '3.0'
        },
        'web.xml': {
            '3.0': '5.0',
            '3.1': '5.0',
            '4.0': '5.0'
        }
    }

    @staticmethod
    def migrate_xml_file(parser: XmlConfigParser) -> Dict[str, int]:
        """
        Migrate an XML configuration file.

        Args:
            parser: XmlConfigParser instance

        Returns:
            Dictionary with migration statistics
        """
        stats = {
            'namespaces_updated': 0,
            'schemas_updated': 0,
            'versions_updated': 0
        }

        # Update namespaces
        for old_ns, new_ns in JakartaXmlMigrator.NAMESPACE_MAPPINGS.items():
            count = parser.update_namespace(old_ns, new_ns)
            stats['namespaces_updated'] += count

        # Update schema locations
        for old_xsd, new_xsd in JakartaXmlMigrator.SCHEMA_MAPPINGS.items():
            if parser.update_schema_location(old_xsd, new_xsd):
                stats['schemas_updated'] += 1

        # Update version attributes
        if 'version' in parser.root.attrib:
            old_version = parser.root.attrib['version']

            # Determine file type from root element
            root_tag = parser.root.tag.split('}')[-1]  # Remove namespace

            if root_tag == 'persistence':
                version_map = JakartaXmlMigrator.VERSION_UPDATES.get('persistence.xml', {})
            elif root_tag == 'web-app':
                version_map = JakartaXmlMigrator.VERSION_UPDATES.get('web.xml', {})
            else:
                version_map = {}

            if old_version in version_map:
                parser.root.attrib['version'] = version_map[old_version]
                stats['versions_updated'] += 1

        return stats

    @staticmethod
    def migrate_persistence_xml(file_path: str, backup: bool = True) -> Dict[str, any]:
        """
        Migrate persistence.xml from Java EE to Jakarta EE.

        Args:
            file_path: Path to persistence.xml
            backup: Whether to create backup

        Returns:
            Migration results
        """
        try:
            # Create backup if requested
            if backup:
                import shutil
                backup_path = f"{file_path}.backup"
                shutil.copy2(file_path, backup_path)

            # Parse and migrate
            parser = XmlConfigParser(file_path)
            parser.parse()

            stats = JakartaXmlMigrator.migrate_xml_file(parser)

            # Save if changes were made
            total_changes = sum(stats.values())
            if total_changes > 0:
                parser.save()

            return {
                "status": "success",
                "file": file_path,
                "statistics": stats,
                "total_changes": total_changes,
                "backup_created": backup
            }
        except Exception as e:
            return {
                "status": "error",
                "file": file_path,
                "error": str(e)
            }

    @staticmethod
    def migrate_web_xml(file_path: str, backup: bool = True) -> Dict[str, any]:
        """
        Migrate web.xml from Java EE to Jakarta EE.

        Args:
            file_path: Path to web.xml
            backup: Whether to create backup

        Returns:
            Migration results
        """
        return JakartaXmlMigrator.migrate_persistence_xml(file_path, backup)

    @staticmethod
    def migrate_beans_xml(file_path: str, backup: bool = True) -> Dict[str, any]:
        """
        Migrate beans.xml from Java EE to Jakarta EE.

        Args:
            file_path: Path to beans.xml
            backup: Whether to create backup

        Returns:
            Migration results
        """
        return JakartaXmlMigrator.migrate_persistence_xml(file_path, backup)


def migrate_all_xml_configs(directory: str, backup: bool = True) -> List[Dict[str, any]]:
    """
    Migrate all XML configuration files in a directory.

    Args:
        directory: Root directory to search
        backup: Whether to create backups

    Returns:
        List of migration results
    """
    import os
    results = []

    # Common XML config file patterns
    patterns = {
        'persistence.xml': JakartaXmlMigrator.migrate_persistence_xml,
        'web.xml': JakartaXmlMigrator.migrate_web_xml,
        'beans.xml': JakartaXmlMigrator.migrate_beans_xml,
    }

    for root, dirs, files in os.walk(directory):
        for file in files:
            for pattern, migrate_func in patterns.items():
                if file == pattern:
                    file_path = os.path.join(root, file)
                    result = migrate_func(file_path, backup)
                    results.append(result)

    return results


def detect_jakarta_migration_needed(file_path: str) -> bool:
    """
    Detect if an XML file needs Jakarta EE migration.

    Args:
        file_path: Path to XML file

    Returns:
        True if migration is needed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for Java EE namespaces
        for old_ns in JakartaXmlMigrator.NAMESPACE_MAPPINGS.keys():
            if old_ns in content:
                return True

        # Check for old schema versions
        for old_xsd in JakartaXmlMigrator.SCHEMA_MAPPINGS.keys():
            if old_xsd in content:
                return True

        return False
    except Exception:
        return False
