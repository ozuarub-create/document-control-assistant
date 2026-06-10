from pathlib import Path

from app.repository import get_version_history, ingest_document, search_documents
from app.search_engine import natural_language_search, semantic_search

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_documents"


def test_repository_stores_metadata_and_tracks_versions(tmp_path):
    db_path = tmp_path / "test_register.db"
    sample = SAMPLE_DIR / "sample_001_drawing.pdf"

    first = ingest_document(sample, db_path=db_path)
    second = ingest_document(sample, db_path=db_path)

    assert first["document_title"] == "Ground Floor Architectural Drawing"
    assert first["document_type"] == "Drawing"
    assert first["version"] == 1
    assert second["version"] == 2

    versions = get_version_history(second["id"], db_path=db_path)
    assert len(versions) == 2
    assert versions[0]["is_latest"] is True


def test_metadata_and_semantic_search(tmp_path):
    db_path = tmp_path / "test_search.db"
    ingest_document(SAMPLE_DIR / "sample_001_drawing.pdf", db_path=db_path)
    ingest_document(SAMPLE_DIR / "sample_007_specification.pdf", db_path=db_path)
    ingest_document(SAMPLE_DIR / "sample_041_meeting_minutes.pdf", db_path=db_path)

    metadata_results = search_documents(document_type="Drawing", discipline="Architectural", db_path=db_path)
    assert len(metadata_results) == 1
    assert metadata_results[0]["document_type"] == "Drawing"

    semantic_results = semantic_search("floor layout plan drawing", db_path=db_path)
    assert semantic_results
    assert semantic_results[0]["document_type"] == "Drawing"

    nl_results = natural_language_search("Show latest architectural drawings", db_path=db_path)
    assert nl_results["results"]
    assert nl_results["results"][0]["document_type"] == "Drawing"
