#!/usr/bin/env python3
"""
Dedicated Document Indexing Script for CarbonIQ Sustainability Knowledge Base.
Allows administrators and data engineers to index, update, inspect, or delete
sustainability documents without restarting the FastAPI application.

Usage:
    # Index all documents in backend/knowledge_base
    python backend/scripts/index_knowledge_docs.py

    # Show vector database collection statistics
    python backend/scripts/index_knowledge_docs.py --stats

    # Index a specific document
    python backend/scripts/index_knowledge_docs.py --file backend/knowledge_base/electricity_and_energy_efficiency/cea_grid_standard.md

    # Force reindex all documents
    python backend/scripts/index_knowledge_docs.py --force

    # Delete an indexed document by ID
    python backend/scripts/index_knowledge_docs.py --delete <doc_id>
"""

import argparse
import logging
import os
from pathlib import Path
import sys

# Ensure backend root is on sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("carboniq.indexer")

from app.core.config import settings
from app.services.document_service import DocumentService
from app.services.vector_db_service import VectorDbService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CarbonIQ Sustainability Knowledge Base Indexer"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Path to the knowledge directory (defaults to settings.KNOWLEDGE_BASE_DIR)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Index a specific file into Qdrant",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Optional category override for the indexed file",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Document title override",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Document source citation override",
    )
    parser.add_argument(
        "--version",
        dest="document_version",
        type=str,
        default=None,
        help="Document version (e.g. 22.0)",
    )
    parser.add_argument(
        "--reporting-period",
        type=str,
        default=None,
        help="Reporting period (e.g. FY 2025-26)",
    )
    parser.add_argument(
        "--publication-date",
        type=str,
        default=None,
        help="Publication date (e.g. August 2026)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reindexing of documents even if content hash matches",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display vector database status, dimension, and total vector count",
    )
    parser.add_argument(
        "--delete",
        type=str,
        default=None,
        help="Delete all vectors associated with the given document ID",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("CarbonIQ RAG Knowledge Base Manager")
    print("=" * 70)

    # 1. Stats action
    if args.stats:
        status = VectorDbService.get_status()
        print(f"Collection:       {status['collection_name']}")
        print(f"Status:           {'CONNECTED' if status['is_available'] else 'OFFLINE'}")
        print(f"Collection Exists: {status['collection_exists']}")
        print(f"Storage Mode:     {status['mode']}")
        print(f"Vector Dimension: {status['vector_dimension']}")
        print(f"Similarity:       {status['vector_distance'] or 'not verified'}")
        print(f"Total Vectors:    {status['total_vectors']}")
        if status.get("storage_path"):
            print(f"Storage Path:     {status['storage_path']}")
        if status.get("qdrant_url"):
            print(f"Qdrant URL:       {status['qdrant_url']}")
        if status.get("init_error"):
            print(f"Notice:           {status['init_error']}")
        return

    # 2. Delete action
    if args.delete:
        print(f"Deleting document with doc_id: '{args.delete}'...")
        success = VectorDbService.delete_document(args.delete)
        if success:
            print("Document vectors successfully deleted.")
        else:
            print("Failed to delete document or document not found.")
        return

    # 3. Single file indexing
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            if (backend_dir / args.file).exists():
                file_path = backend_dir / args.file
            elif (Path.cwd() / args.file).exists():
                file_path = Path.cwd() / args.file
        print(f"Indexing single file: {file_path}...")
        result = DocumentService.index_single_document(
            file_path=file_path,
            category=args.category,
            source=args.source,
            title=args.title,
            document_version=args.document_version,
            reporting_period=args.reporting_period,
            publication_date=args.publication_date,
            force_reindex=args.force,
        )
        print(f"Result: {result}")
        return

    # 4. Directory indexing
    target_dir = Path(args.dir) if args.dir else (backend_dir / settings.KNOWLEDGE_BASE_DIR)
    print(f"Indexing knowledge directory: {target_dir}")
    print(f"Target Qdrant Collection:   {settings.QDRANT_COLLECTION_NAME}")

    result = DocumentService.index_knowledge_directory(
        knowledge_dir=target_dir,
        force_reindex=args.force,
    )

    print("\n--- Indexing Summary ---")
    print(f"Status:                {result.get('status')}")
    print(f"Files Processed:       {result.get('files_processed', 0)}")
    print(f"Total Chunks Indexed:  {result.get('total_chunks_indexed', 0)}")
    if result.get("details"):
        print("\nIndexed Documents:")
        for doc in result["details"]:
            print(f" - [{doc.get('category')}] {doc.get('title')} ({doc.get('chunks_indexed')} chunks)")
    if result.get("errors"):
        print("\nErrors Encountered:")
        for err in result["errors"]:
            print(f" - {err}")
    print("=" * 70)


if __name__ == "__main__":
    main()
