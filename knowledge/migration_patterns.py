"""
Enhanced Migration Patterns with Jakarta, Spring Boot 3, Camel 4, and Java 21 support.

This module extends the knowledge base with comprehensive migration patterns
loaded from JSON/YAML data files for LLM-powered agent decisions.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MigrationPatterns:
    """
    Centralized migration patterns for all supported migrations.
    Loads data from JSON/YAML files in the data/ directory.
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize migration patterns loader.

        Args:
            data_dir: Directory containing migration data files
        """
        self.data_dir = Path(data_dir)
        self.jakarta_mappings = {}
        self.springboot_mappings = {}
        self.camel4_mappings = {}
        self.java21_patterns = {}
        self._load_all_mappings()

    def _load_all_mappings(self):
        """Load all migration mapping files."""
        try:
            # Load Jakarta EE mappings
            jakarta_file = self.data_dir / "jakarta_mappings.json"
            if jakarta_file.exists():
                with open(jakarta_file, 'r') as f:
                    self.jakarta_mappings = json.load(f)
                logger.info("Loaded Jakarta EE mappings")
            else:
                logger.warning(f"Jakarta mappings file not found: {jakarta_file}")

            # Load Spring Boot 3 mappings
            springboot_file = self.data_dir / "springboot3_mappings.yaml"
            if springboot_file.exists():
                with open(springboot_file, 'r') as f:
                    self.springboot_mappings = yaml.safe_load(f)
                logger.info("Loaded Spring Boot 3 mappings")
            else:
                logger.warning(f"Spring Boot mappings file not found: {springboot_file}")

            # Load Camel 4 mappings
            camel_file = self.data_dir / "camel4_components.json"
            if camel_file.exists():
                with open(camel_file, 'r') as f:
                    self.camel4_mappings = json.load(f)
                logger.info("Loaded Camel 4 component mappings")
            else:
                logger.warning(f"Camel 4 mappings file not found: {camel_file}")

            # Load Java 21 patterns
            java21_file = self.data_dir / "java21_patterns.json"
            if java21_file.exists():
                with open(java21_file, 'r') as f:
                    self.java21_patterns = json.load(f)
                logger.info("Loaded Java 21 modernization patterns")
            else:
                logger.warning(f"Java 21 patterns file not found: {java21_file}")

        except Exception as e:
            logger.error(f"Error loading migration patterns: {e}")

    # Jakarta EE Migration Methods
    def get_jakarta_package_mapping(self, javax_package: str) -> Optional[str]:
        """
        Get Jakarta package mapping for a javax package.

        Args:
            javax_package: javax.* package name

        Returns:
            jakarta.* package name or None
        """
        return self.jakarta_mappings.get("package_mappings", {}).get(javax_package)

    def get_all_jakarta_packages(self) -> Dict[str, str]:
        """Get all javax to jakarta package mappings."""
        return self.jakarta_mappings.get("package_mappings", {})

    def get_jakarta_annotation_mapping(self, annotation: str) -> Optional[str]:
        """
        Get Jakarta annotation mapping.

        Args:
            annotation: Annotation name (with or without @)

        Returns:
            Jakarta annotation or None
        """
        if not annotation.startswith('@'):
            annotation = f'@{annotation}'
        return self.jakarta_mappings.get("annotation_mappings", {}).get(annotation)

    def get_jakarta_xml_namespace(self, old_namespace: str) -> Optional[str]:
        """
        Get Jakarta XML namespace mapping.

        Args:
            old_namespace: Old Java EE namespace

        Returns:
            New Jakarta namespace or None
        """
        return self.jakarta_mappings.get("xml_namespace_mappings", {}).get(old_namespace)

    def get_jakarta_schema_version(self, old_schema: str) -> Optional[str]:
        """
        Get Jakarta schema version mapping.

        Args:
            old_schema: Old schema version

        Returns:
            New schema version or None
        """
        return self.jakarta_mappings.get("schema_version_mappings", {}).get(old_schema)

    # Spring Boot 3 Migration Methods
    def get_springboot_property_mapping(self, old_property: str) -> Optional[str]:
        """
        Get Spring Boot 3 property mapping.

        Args:
            old_property: Spring Boot 2.x property name

        Returns:
            Spring Boot 3.x property name or None
        """
        return self.springboot_mappings.get("property_mappings", {}).get(old_property)

    def get_springboot_property_value_mapping(self, property_name: str, old_value: str) -> Optional[str]:
        """
        Get Spring Boot 3 property value mapping.

        Args:
            property_name: Property name
            old_value: Old property value

        Returns:
            New property value or None
        """
        value_mappings = self.springboot_mappings.get("property_value_mappings", {})
        if property_name in value_mappings:
            return value_mappings[property_name].get(str(old_value))
        return None

    def get_springboot_security_migration_pattern(self) -> Dict[str, str]:
        """Get Spring Security configuration migration patterns."""
        return self.springboot_mappings.get("security_config_migration", {})

    def get_all_springboot_properties(self) -> Dict[str, str]:
        """Get all Spring Boot property mappings."""
        return self.springboot_mappings.get("property_mappings", {})

    # Camel 4 Migration Methods
    def get_camel_component_mapping(self, old_component: str) -> Optional[Dict[str, Any]]:
        """
        Get Camel 4 component mapping.

        Args:
            old_component: Old component name (e.g., 'http4')

        Returns:
            Component mapping dictionary or None
        """
        return self.camel4_mappings.get("component_uri_mappings", {}).get(old_component)

    def get_camel_api_change(self, api_name: str, method_name: str) -> Optional[Dict[str, Any]]:
        """
        Get Camel 4 API change information.

        Args:
            api_name: API name (e.g., 'exchange')
            method_name: Method name (e.g., 'getIn')

        Returns:
            API change information or None
        """
        api_changes = self.camel4_mappings.get("api_changes", {})
        if api_name in api_changes:
            return api_changes[api_name].get(method_name)
        return None

    def get_camel_removed_component(self, component_name: str) -> Optional[Dict[str, str]]:
        """
        Get information about removed Camel components.

        Args:
            component_name: Component name

        Returns:
            Removal information with alternatives or None
        """
        return self.camel4_mappings.get("removed_components", {}).get(component_name)

    def get_camel_eip_pattern_update(self, pattern_name: str) -> Optional[Dict[str, str]]:
        """
        Get EIP pattern update information.

        Args:
            pattern_name: EIP pattern name (e.g., 'aggregate')

        Returns:
            Pattern update information or None
        """
        return self.camel4_mappings.get("eip_pattern_updates", {}).get(pattern_name)

    def get_camel_route_builder_patterns(self) -> Dict[str, Dict[str, str]]:
        """Get modern Camel 4 RouteBuilder patterns."""
        return self.camel4_mappings.get("route_builder_patterns", {})

    def get_camel_best_practices(self) -> List[str]:
        """Get Camel 4 best practices."""
        return self.camel4_mappings.get("best_practices", [])

    # Java 21 Modernization Methods
    def get_lambda_conversion_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """
        Get lambda conversion pattern.

        Args:
            pattern_name: Pattern name

        Returns:
            Lambda conversion pattern or None
        """
        lambda_conversions = self.java21_patterns.get("lambda_conversions", {})
        return lambda_conversions.get(pattern_name)

    def get_stream_api_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """
        Get Stream API conversion pattern.

        Args:
            pattern_name: Pattern name (e.g., 'for_loop_to_stream')

        Returns:
            Stream API pattern or None
        """
        stream_patterns = self.java21_patterns.get("stream_api_patterns", {})
        return stream_patterns.get(pattern_name)

    def get_var_inference_patterns(self) -> Dict[str, Any]:
        """Get var type inference patterns."""
        return self.java21_patterns.get("var_type_inference", {})

    def get_switch_expression_patterns(self) -> Dict[str, Any]:
        """Get switch expression patterns."""
        return self.java21_patterns.get("switch_expressions", {})

    def get_text_block_patterns(self) -> Dict[str, Any]:
        """Get text block patterns."""
        return self.java21_patterns.get("text_blocks", {})

    def get_record_patterns(self) -> Dict[str, Any]:
        """Get record conversion patterns."""
        return self.java21_patterns.get("records", {})

    def get_pattern_matching_patterns(self) -> Dict[str, Any]:
        """Get pattern matching for instanceof patterns."""
        return self.java21_patterns.get("pattern_matching", {})

    def get_java_modernization_strategy(self, strategy_name: str = "balanced") -> Dict[str, Any]:
        """
        Get Java modernization strategy.

        Args:
            strategy_name: Strategy name ('aggressive', 'conservative', 'balanced')

        Returns:
            Modernization strategy configuration
        """
        rules = self.java21_patterns.get("modernization_rules", {})
        return rules.get(strategy_name, rules.get("balanced", {}))

    # Comprehensive Query Methods
    def get_migration_summary(self) -> Dict[str, int]:
        """
        Get summary of loaded migration patterns.

        Returns:
            Dictionary with counts of different migration types
        """
        return {
            "jakarta_packages": len(self.jakarta_mappings.get("package_mappings", {})),
            "jakarta_annotations": len(self.jakarta_mappings.get("annotation_mappings", {})),
            "springboot_properties": len(self.springboot_mappings.get("property_mappings", {})),
            "camel_component_mappings": len(self.camel4_mappings.get("component_uri_mappings", {})),
            "camel_removed_components": len(self.camel4_mappings.get("removed_components", {})),
            "java21_pattern_types": len([k for k in self.java21_patterns.keys() if k != "modernization_rules"])
        }

    def search_patterns(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for patterns matching a query string.

        Args:
            query: Search query

        Returns:
            List of matching patterns
        """
        results = []
        query_lower = query.lower()

        # Search Jakarta patterns
        if "jakarta" in query_lower or "javax" in query_lower:
            for old, new in self.get_all_jakarta_packages().items():
                if query_lower in old.lower() or query_lower in new.lower():
                    results.append({
                        "type": "jakarta_package",
                        "old": old,
                        "new": new,
                        "confidence": 1.0
                    })

        # Search Spring Boot patterns
        if "spring" in query_lower:
            for old, new in self.get_all_springboot_properties().items():
                if query_lower in old.lower() or query_lower in new.lower():
                    results.append({
                        "type": "springboot_property",
                        "old": old,
                        "new": new,
                        "confidence": 1.0
                    })

        # Search Camel patterns
        if "camel" in query_lower or "exchange" in query_lower:
            for component, info in self.camel4_mappings.get("component_uri_mappings", {}).items():
                if query_lower in component.lower() or query_lower in info.get("new_uri", "").lower():
                    results.append({
                        "type": "camel_component",
                        "old": component,
                        "new": info.get("new_uri"),
                        "reason": info.get("reason"),
                        "confidence": info.get("confidence", 1.0)
                    })

        return results


# Singleton instance
_migration_patterns = None


def get_migration_patterns() -> MigrationPatterns:
    """Get or create the migration patterns singleton."""
    global _migration_patterns
    if _migration_patterns is None:
        _migration_patterns = MigrationPatterns()
    return _migration_patterns


def reload_migration_patterns(data_dir: str = "data") -> MigrationPatterns:
    """
    Reload migration patterns from data files.

    Args:
        data_dir: Directory containing migration data files

    Returns:
        MigrationPatterns instance
    """
    global _migration_patterns
    _migration_patterns = MigrationPatterns(data_dir)
    return _migration_patterns
