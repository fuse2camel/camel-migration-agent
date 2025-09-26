#!/usr/bin/env python3
"""
Test suite for the Camel Migration Knowledge Base
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.camel_knowledge_base import get_knowledge_base, initialize_knowledge_base
from tools.knowledge_tools import (
    query_camel_knowledge,
    get_dsl_conversion_guidance,
    get_component_migration_info,
    ensure_knowledge_base_ready
)


class TestCamelKnowledgeBase(unittest.TestCase):
    """Test cases for the Camel knowledge base."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once."""
        cls.kb = get_knowledge_base()

    def test_01_initialization(self):
        """Test knowledge base initialization."""
        self.assertIsNotNone(self.kb)
        self.assertEqual(self.kb.model_name, "all-MiniLM-L6-v2")
        self.assertEqual(self.kb.embed_dim, 384)
        print(f"✓ Knowledge base initialized (ready={self.kb.ready})")

    def test_02_fallback_responses(self):
        """Test fallback responses when no index is available."""
        # Test XML to Java DSL fallback
        result = self.kb.query("How to convert XML DSL to Java DSL?")
        self.assertIn("status", result)
        self.assertIn("response", result)
        self.assertIn("getMessage()", result["response"])
        print("✓ XML to Java DSL fallback working")

        # Test Spring Boot fallback
        result = self.kb.query("Spring Boot 3 migration")
        self.assertIn("camel-spring-boot-bom", result["response"])
        print("✓ Spring Boot fallback working")

        # Test component fallback
        result = self.kb.query("component dependencies")
        self.assertIn("camel-http4", result["response"])
        print("✓ Component mapping fallback working")

    def test_03_dsl_conversion_guidance(self):
        """Test DSL conversion guidance."""
        xml_snippet = '<route><from uri="file:input"/></route>'
        result = get_dsl_conversion_guidance(xml_snippet, "route")

        self.assertIn("status", result)
        self.assertIn("response", result)
        self.assertIn("conversion_patterns", result)
        self.assertIsInstance(result["conversion_patterns"], dict)
        print(f"✓ DSL conversion guidance (patterns: {len(result['conversion_patterns'])})")

    def test_04_component_migration(self):
        """Test component migration information."""
        components = ["http", "jetty", "rabbitmq"]

        for component in components:
            result = get_component_migration_info(component)
            self.assertIn("status", result)
            self.assertIn("response", result)

            if "known_mapping" in result:
                mapping = result["known_mapping"]
                self.assertIn("old", mapping)
                self.assertIn("new", mapping)
                print(f"✓ Component {component}: {mapping['old']} → {mapping['new']}")
            else:
                print(f"✓ Component {component}: fallback response")

    def test_05_query_knowledge(self):
        """Test general knowledge queries."""
        queries = [
            "Red Hat Camel 4.10 migration",
            "Exchange API changes",
            "Maven dependencies update"
        ]

        for query in queries:
            result = query_camel_knowledge(query)
            self.assertIn("status", result)
            self.assertIn("response", result)
            self.assertIsInstance(result["response"], str)
            self.assertGreater(len(result["response"]), 50)
            print(f"✓ Query '{query[:30]}...' returned {len(result['response'])} chars")

    def test_06_ensure_ready(self):
        """Test knowledge base readiness check."""
        ready = ensure_knowledge_base_ready()
        self.assertIsInstance(ready, bool)
        print(f"✓ Knowledge base ready check: {ready}")

    def test_07_conversion_patterns(self):
        """Test conversion patterns are available."""
        patterns = self.kb._get_conversion_patterns()
        self.assertIsInstance(patterns, dict)
        self.assertIn("route", patterns)
        self.assertIn("choice", patterns)
        self.assertIn("split", patterns)
        print(f"✓ Conversion patterns available: {len(patterns)}")

    def test_08_component_mappings(self):
        """Test component mappings are available."""
        mappings = self.kb._get_component_mappings()
        self.assertIsInstance(mappings, dict)
        self.assertIn("http", mappings)
        self.assertIn("jetty", mappings)
        print(f"✓ Component mappings available: {len(mappings)}")


def run_integration_test():
    """Run a simple integration test."""
    print("\n" + "="*60)
    print("Integration Test: DSL Conversion Agent with Knowledge Base")
    print("="*60)

    try:
        from agents.dsl_conversion_agent import DSLConversionAgent

        # Create agent
        agent = DSLConversionAgent()
        print(f"✓ DSL agent created (KB available: {agent.kb_available})")

        # Check tools
        tool_names = [tool.name for tool in agent.agent.tools]
        kb_tools = ["Query Camel Knowledge Base", "Get DSL Conversion Help", "Get Component Migration Info"]

        found = sum(1 for tool in kb_tools if tool in tool_names)
        print(f"✓ Knowledge tools integrated: {found}/{len(kb_tools)}")

        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Run unit tests
    print("Running Knowledge Base Tests")
    print("="*60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCamelKnowledgeBase)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    # Run integration test
    integration_success = run_integration_test()

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Unit tests: {result.testsRun} run, {len(result.failures)} failures, {len(result.errors)} errors")
    print(f"Integration test: {'✓ Passed' if integration_success else '✗ Failed'}")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() and integration_success else 1)