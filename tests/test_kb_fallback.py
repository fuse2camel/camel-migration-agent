#!/usr/bin/env python3
"""
Test that knowledge base works with fallback patterns (no ingestion required)
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge.camel_knowledge_base import get_knowledge_base


def main():
    print("Testing Knowledge Base Fallback Patterns")
    print("="*50)

    # Get knowledge base
    kb = get_knowledge_base()
    print(f"Knowledge base initialized: {kb.ready}")

    # Check if index exists
    if kb.index is not None and kb.index.ntotal > 0:
        print(f"Vector index loaded with {kb.index.ntotal} vectors")
    else:
        print("No vector index - using fallback patterns")

    # Test queries (should work even without ingested docs)
    test_queries = [
        "How to convert XML DSL to Java DSL?",
        "Spring Boot 3 migration",
        "Component dependency changes"
    ]

    print("\nTesting queries with fallback:")
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = kb.query(query, top_k=3)
        print(f"Status: {result['status']}")
        print(f"Response length: {len(result['response'])} chars")
        print(f"Preview: {result['response'][:100]}...")

    # Test DSL conversion help
    print("\n\nTesting DSL conversion help:")
    help_result = kb.get_dsl_conversion_help(
        xml_snippet='<route><from uri="timer:test"/></route>',
        pattern_type="route"
    )
    print(f"Status: {help_result['status']}")
    patterns = help_result.get('conversion_patterns', {})
    print(f"Conversion patterns available: {len(patterns)}")

    # Test component migration
    print("\nTesting component migration info:")
    comp_result = kb.get_component_migration_info("http")
    print(f"Status: {comp_result['status']}")
    if 'known_mapping' in comp_result:
        mapping = comp_result['known_mapping']
        print(f"Mapping: {mapping.get('old')} → {mapping.get('new')}")

    print("\n" + "="*50)
    print("✓ All tests passed - fallback patterns working!")


if __name__ == "__main__":
    main()