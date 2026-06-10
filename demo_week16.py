"""Week 16 demonstration: document register, metadata search, and semantic search.

Usage:
    python demo_week16.py
"""

from __future__ import annotations

import json
from pathlib import Path

from app.database import DATABASE_PATH, reset_database
from app.repository import get_version_history, ingest_document, ingest_folder, search_documents
from app.search_engine import natural_language_search, semantic_search

ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT / "sample_documents"
OUTPUT_PATH = ROOT / "demo_week16_results.json"


def print_results(title: str, results: list[dict], score_field: str | None = None) -> None:
    print("\n" + title)
    print("-" * 88)
    print(f"{'ID':4} {'Type':20} {'Title':35} {'Project':24} {'Score':>6}")
    print("-" * 88)
    for item in results:
        score = item.get(score_field, "") if score_field else ""
        print(
            f"{item['id']:<4} "
            f"{item['document_type'][:19]:20} "
            f"{(item.get('document_title') or '')[:34]:35} "
            f"{(item.get('project_name') or '')[:23]:24} "
            f"{score!s:>6}"
        )


def main() -> None:
    print("Week 16 - Intelligent Document Register & Search Demo")
    print("=" * 88)

    reset_database(DATABASE_PATH)
    documents = ingest_folder(SAMPLE_DIR)
    print(f"Metadata repository created: {DATABASE_PATH.name}")
    print(f"Sample documents loaded into register: {len(documents)}")

    # Demonstrate version tracking by uploading the same document again.
    new_version = ingest_document(SAMPLE_DIR / "sample_001_drawing.pdf")
    version_history = get_version_history(new_version["id"])
    print(
        f"Version tracking demo: document ID {new_version['id']} is version "
        f"{new_version['version']} and has {len(version_history)} version records."
    )

    traditional = search_documents(
        document_type="Drawing",
        discipline="Architectural",
        latest_only=True,
        limit=5,
    )
    print_results("Traditional metadata search: Drawing + Architectural", traditional)

    contractor_search = search_documents(
        contractor="Gulf Build Contractors",
        latest_only=True,
        limit=5,
    )
    print_results("Traditional metadata search: Contractor = Gulf Build Contractors", contractor_search)

    semantic = semantic_search(
        "Find layout plans and architectural drawings for floor work",
        limit=5,
        latest_only=True,
    )
    print_results("AI semantic search: layout plans and architectural drawings", semantic, "semantic_score")

    nl_query = natural_language_search(
        "Show me the latest architectural drawings",
        limit=5,
    )
    print("\nNatural language query")
    print("-" * 88)
    print(nl_query["question"])
    print(nl_query["answer"])
    print_results("Natural language query results", nl_query["results"], "semantic_score")

    output = {
        "documents_loaded": len(documents),
        "version_tracking": {
            "document_id": new_version["id"],
            "current_version": new_version["version"],
            "version_records": len(version_history),
        },
        "traditional_metadata_search": traditional,
        "contractor_search": contractor_search,
        "semantic_search": semantic,
        "natural_language_query": nl_query,
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nResults saved to: {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
