#!/usr/bin/env python3
"""
Manual document ingestion script for the Camel Knowledge Base
Run this to ingest PDF documentation into the vector database
"""

import os
import sys
from pathlib import Path
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path (go up one level from knowledge folder)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.camel_knowledge_base import get_knowledge_base, initialize_knowledge_base


def main():
    parser = argparse.ArgumentParser(
        description="Ingest PDF documentation into the Camel Knowledge Base"
    )
    parser.add_argument(
        "--docs-path",
        default="knowledge/docs",
        help="Path to directory containing PDF files (default: knowledge/docs)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion even if index already exists"
    )
    args = parser.parse_args()

    print("="*70)
    print("Camel Knowledge Base - Document Ingestion")
    print("="*70)

    # Check if docs directory exists
    docs_path = Path(args.docs_path)
    if not docs_path.exists():
        print(f"\n✗ Error: Directory '{docs_path}' does not exist")
        print(f"  Please create it and add PDF files, or specify a different path with --docs-path")
        return 1

    # Check for PDF files
    pdf_files = list(docs_path.glob("*.pdf"))
    if not pdf_files:
        print(f"\n⚠️ Warning: No PDF files found in '{docs_path}'")
        print(f"  Place Red Hat Camel documentation PDFs in this directory")
        return 1

    print(f"\nFound {len(pdf_files)} PDF files:")
    for pdf in pdf_files[:5]:  # Show first 5
        print(f"  • {pdf.name}")
    if len(pdf_files) > 5:
        print(f"  ... and {len(pdf_files) - 5} more")

    # Check if index already exists
    kb = get_knowledge_base()
    if kb.index is not None and kb.index.ntotal > 0 and not args.force:
        print(f"\n⚠️ Index already exists with {kb.index.ntotal} vectors")
        print("  Use --force to rebuild the index")
        response = input("\nContinue anyway? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted")
            return 0

    # Perform ingestion
    print(f"\n{'Re-ingesting' if args.force else 'Ingesting'} documents...")
    print("This may take a few minutes depending on the size of PDFs...")

    result = initialize_knowledge_base(
        docs_path=str(docs_path),
        force_reingest=args.force
    )

    # Display results
    print("\n" + "="*70)
    if result["status"] == "success":
        print("✓ Ingestion Successful!")
        print(f"  • Chunks indexed: {result.get('chunks_indexed', 0)}")
        print(f"  • Files processed: {result.get('files_processed', 0)}")
        print(f"\nThe knowledge base is now ready for vector search queries.")
        print("DSL agents will automatically use the indexed documentation.")
        return 0

    elif result["status"] == "skipped":
        print("ℹ️ Ingestion Skipped")
        print(f"  {result.get('message', 'Index already exists')}")
        print("\nUse --force to rebuild the index if needed.")
        return 0

    else:
        print("✗ Ingestion Failed")
        print(f"  Error: {result.get('message', 'Unknown error')}")
        print("\nThe system will continue to work with fallback patterns.")
        return 1


if __name__ == "__main__":
    sys.exit(main())