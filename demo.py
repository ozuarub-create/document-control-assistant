"""Run a simple demonstration on the 50 sample documents.

Usage:
    python demo.py
"""

from __future__ import annotations

import json
from pathlib import Path

from app.document_processor import process_file

ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT / "sample_documents"
MANIFEST_PATH = SAMPLE_DIR / "dataset_manifest.json"
OUTPUT_PATH = ROOT / "demo_results.json"


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    expected_by_file = {item["filename"]: item["expected_document_type"] for item in manifest}

    results = []
    correct = 0

    print("AI Document Control Assistant - Demo")
    print("=" * 78)
    print(f"{'File':40} {'Expected':18} {'Predicted':18} {'Conf.'}")
    print("-" * 78)

    for file_path in sorted(SAMPLE_DIR.glob("sample_*.pdf")) + sorted(SAMPLE_DIR.glob("sample_*.docx")):
        result = process_file(file_path)
        expected = expected_by_file[file_path.name]
        predicted = result["classification"]["document_type"]
        confidence = result["classification"]["confidence_score"]
        is_correct = predicted == expected
        correct += int(is_correct)

        results.append({
            "filename": file_path.name,
            "expected": expected,
            "predicted": predicted,
            "confidence_score": confidence,
            "metadata": result["metadata"],
            "correct": is_correct,
        })

        print(f"{file_path.name[:39]:40} {expected[:17]:18} {predicted[:17]:18} {confidence:.2f}")

    accuracy = correct / len(results) if results else 0
    print("-" * 78)
    print(f"Documents tested: {len(results)}")
    print(f"Correct classifications: {correct}")
    print(f"Accuracy: {accuracy:.0%}")
    print(f"Results saved to: {OUTPUT_PATH.name}")

    OUTPUT_PATH.write_text(json.dumps({
        "documents_tested": len(results),
        "correct_classifications": correct,
        "accuracy": accuracy,
        "results": results,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
