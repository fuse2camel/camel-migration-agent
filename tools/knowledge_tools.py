"""
Knowledge Tools for Camel Migration Agents
Provides tools for querying Red Hat Camel documentation
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.camel_knowledge_base import get_knowledge_base, initialize_knowledge_base

logger = logging.getLogger(__name__)


def query_camel_knowledge(
    query: str,
    component_type: Optional[str] = None,
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Query the Camel knowledge base for migration guidance.

    Args:
        query: The query text
        component_type: Optional component type for specific guidance
        top_k: Number of top results to return

    Returns:
        Dictionary with query results and guidance
    """
    try:
        kb = get_knowledge_base()

        # Use component-specific query if provided
        if component_type:
            result = kb.get_migration_context(component_type, query)
        else:
            result = kb.query(query, top_k=top_k)

        return result

    except Exception as e:
        logger.error(f"Knowledge query failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def get_dsl_conversion_guidance(
    xml_snippet: str = "",
    pattern_type: str = ""
) -> Dict[str, Any]:
    """
    Get specific DSL conversion guidance from documentation.

    Args:
        xml_snippet: Optional XML snippet to analyze
        pattern_type: Type of pattern (e.g., "route", "processor", "error-handler")
        include_examples: Whether to include code examples

    Returns:
        DSL conversion guidance with examples
    """
    try:
        kb = get_knowledge_base()
        return kb.get_dsl_conversion_help(xml_snippet, pattern_type)

    except Exception as e:
        logger.error(f"DSL guidance query failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def get_component_migration_info(component_name: str) -> Dict[str, Any]:
    """
    Get specific component migration information.

    Args:
        component_name: Name of the Camel component (e.g., "http", "jms", "file")

    Returns:
        Component migration details
    """
    try:
        kb = get_knowledge_base()
        return kb.get_component_migration_info(component_name)

    except Exception as e:
        logger.error(f"Component migration query failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def get_spring_boot_migration_info() -> Dict[str, Any]:
    """
    Get Spring Boot 3 migration information for Camel applications.

    Returns:
        Spring Boot migration guidance
    """
    try:
        kb = get_knowledge_base()

        query = """
        Red Hat Camel 4.10 with Spring Boot 3 migration.
        Application properties changes.
        Configuration updates from Spring Boot 2 to 3.
        Camel Spring Boot starter changes.
        """

        return kb.query(query, top_k=4)

    except Exception as e:
        logger.error(f"Spring Boot migration query failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def search_error_solution(error_message: str) -> Dict[str, Any]:
    """
    Search for solutions to specific error messages during migration.

    Args:
        error_message: The error message to search for

    Returns:
        Potential solutions and guidance
    """
    try:
        kb = get_knowledge_base()

        query = f"""
        Red Hat Camel 4.10 migration error solution.
        Error: {error_message[:500]}
        Provide troubleshooting steps and solutions.
        """

        result = kb.query(query, top_k=3)

        # Add common error solutions
        if result["status"] == "success":
            result["common_solutions"] = _get_common_error_solutions(error_message)

        return result

    except Exception as e:
        logger.error(f"Error solution search failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def ensure_knowledge_base_ready() -> bool:
    """
    Check if the knowledge base is ready (but don't auto-ingest).
    This function is non-blocking - if KB fails, the system continues with fallback.

    NOTE: Document ingestion is manual. Use initialize_knowledge_base() separately.

    Returns:
        True if ready with vector search, False if using fallback mode
    """
    try:
        kb = get_knowledge_base()

        # Check if embeddings are ready
        if not kb.ready:
            logger.info("Embeddings not ready. Knowledge base will work in fallback mode.")
            return False

        # Check if index exists and has vectors
        if kb.index is None or kb.index.ntotal == 0:
            logger.info("No vector index found. Knowledge base will use fallback patterns.")
            logger.info("To enable vector search, manually ingest docs using initialize_knowledge_base()")
            return False

        logger.info(f"Knowledge base ready with {kb.index.ntotal} vectors")
        return True

    except Exception as e:
        logger.warning(f"Knowledge base check failed: {e}. Using fallback mode.")
        return False


def _get_common_conversion_patterns() -> Dict[str, str]:
    """Get common XML to Java DSL conversion patterns."""
    return {
        "route": "from().routeId().to()",
        "choice": "choice().when().otherwise().end()",
        "split": "split().body().streaming().to()",
        "aggregate": "aggregate().constant(true).completionSize().to()",
        "error_handler": "errorHandler(deadLetterChannel())",
        "processor": "process(exchange -> {})",
        "bean": "bean(MyBean.class, \"method\")",
        "transform": "transform().simple()",
        "filter": "filter().simple().to()",
        "multicast": "multicast().parallelProcessing().to()"
    }


def _get_component_mappings() -> Dict[str, Dict[str, str]]:
    """Get component dependency mappings for Camel 4."""
    return {
        "http": {
            "old": "camel-http4",
            "new": "camel-http",
            "groupId": "org.apache.camel",
            "notes": "HTTP4 component merged into HTTP in Camel 4"
        },
        "jetty": {
            "old": "camel-jetty9",
            "new": "camel-jetty",
            "groupId": "org.apache.camel",
            "notes": "Jetty9 component renamed to Jetty"
        },
        "rabbitmq": {
            "old": "camel-rabbitmq",
            "new": "camel-spring-rabbitmq",
            "groupId": "org.apache.camel.springboot",
            "notes": "Use Spring Boot starter for RabbitMQ"
        },
        "activemq": {
            "old": "camel-activemq",
            "new": "camel-jms",
            "groupId": "org.apache.camel.springboot",
            "notes": "Use JMS component with ActiveMQ connection factory"
        }
    }


def _get_common_error_solutions(error_message: str) -> Dict[str, str]:
    """Get common error solutions based on error patterns."""
    solutions = {}

    error_lower = error_message.lower()

    if "cannot find symbol" in error_lower:
        solutions["import_issue"] = "Check imports - many classes moved in Camel 4. Use org.apache.camel.support.* instead of org.apache.camel.impl.*"

    if "getmessage()" in error_lower or "getin()" in error_lower:
        solutions["exchange_api"] = "Use exchange.getMessage() instead of getIn()/getOut() in Camel 4"

    if "routebuilder" in error_lower:
        solutions["route_builder"] = "Ensure RouteBuilder extends org.apache.camel.builder.RouteBuilder and has @Component annotation"

    if "dependency" in error_lower or "artifact" in error_lower:
        solutions["dependency"] = "Update to Red Hat Camel 4.10 BOM: com.redhat.camel.springboot:camel-spring-boot-bom:4.10.0.redhat-00001"

    if "application.properties" in error_lower or "application.yml" in error_lower:
        solutions["config"] = "Update configuration properties for Spring Boot 3. Many properties have changed names."

    return solutions


# CrewAI tool wrapper for knowledge base
from crewai.tools import tool


@tool("Query Camel Knowledge Base")
def query_knowledge_tool(query: str) -> str:
    """
    Query the Red Hat Camel knowledge base for migration guidance.

    Args:
        query: The query to search for

    Returns:
        JSON string with query results
    """
    ensure_knowledge_base_ready()
    result = query_camel_knowledge(query)
    return json.dumps(result, indent=2)


@tool("Get DSL Conversion Help")
def dsl_conversion_help_tool(xml_snippet: str = "", pattern_type: str = "") -> str:
    """
    Get DSL conversion help from Red Hat Camel documentation.

    Args:
        xml_snippet: Optional XML snippet to analyze
        pattern_type: Type of pattern to convert

    Returns:
        JSON string with conversion guidance
    """
    ensure_knowledge_base_ready()
    result = get_dsl_conversion_guidance(xml_snippet, pattern_type)
    return json.dumps(result, indent=2)


@tool("Get Component Migration Info")
def component_migration_tool(component_name: str) -> str:
    """
    Get component-specific migration information.

    Args:
        component_name: Name of the Camel component

    Returns:
        JSON string with component migration details
    """
    ensure_knowledge_base_ready()
    result = get_component_migration_info(component_name)
    return json.dumps(result, indent=2)