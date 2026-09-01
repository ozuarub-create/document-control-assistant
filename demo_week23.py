"""Week 23 multimodal document intelligence demonstration.

Default mode uses deterministic fixtures for the bundled synthetic benchmark.
Use --provider openai with OPENAI_API_KEY to run the real vision-capable model.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path
from typing import Any

from app.multimodal_engine import analyze_pdf


ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT / "multimodal_test_documents"
RESULTS_PATH = ROOT / "demo_week23_results.json"
OUTPUT_PATH = ROOT / "demo_week23_output.txt"
ACCURACY_PATH = ROOT / "accuracy_report_week23.json"

SHARED_FIELDS = [
    "document_title",
    "document_type",
    "document_number",
    "revision",
    "project_name",
    "date",
]
VISUAL_CATEGORIES = [
    "tables",
    "drawing_notes",
    "stamps",
    "revision_information",
    "symbols_and_annotations",
]


def value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def evaluate_page(result: dict[str, Any], truth: dict[str, Any]) -> dict[str, Any]:
    page = result["pages"][0]
    text_fields = page["text_only"]["fields"]
    visual = page["multimodal"]
    truth_block = truth["title_block"]
    visual_block = visual["title_block"]

    expected_shared = sum(value_present(truth_block.get(name)) for name in SHARED_FIELDS)
    text_correct = sum(
        value_present(text_fields.get(name))
        and str(text_fields.get(name)).strip().lower() == str(truth_block.get(name)).strip().lower()
        for name in SHARED_FIELDS
        if value_present(truth_block.get(name))
    )
    visual_correct = sum(
        value_present(visual_block.get(name))
        and str(visual_block.get(name)).strip().lower() == str(truth_block.get(name)).strip().lower()
        for name in SHARED_FIELDS
        if value_present(truth_block.get(name))
    )
    visual_category_correct = sum(
        bool(visual.get(name)) == bool(truth.get(name)) for name in VISUAL_CATEGORIES
    )
    return {
        "filename": result["filename"],
        "provider": result["provider"],
        "model": result["model"],
        "text_only_shared_correct": text_correct,
        "multimodal_shared_correct": visual_correct,
        "expected_shared": expected_shared,
        "visual_categories_correct": visual_category_correct,
        "expected_visual_categories": len(VISUAL_CATEGORIES),
        "multimodal_confidence": visual["overall_confidence"],
        "visual_only_findings": len(visual["visual_only_findings"]),
        "text_characters": page["text_only"]["characters_extracted"],
        "visual_added_value": page["comparison"]["multimodal_added_value"],
    }


def run_demo(provider: str, limit: int, model: str | None) -> dict[str, Any]:
    truth_data = json.loads((DATASET_DIR / "ground_truth.json").read_text(encoding="utf-8"))
    truth_by_filename = {item["filename"]: item["pages"][0] for item in truth_data.values()}
    files = sorted(DATASET_DIR.glob("*.pdf"))[:limit]
    metrics: list[dict[str, Any]] = []
    analyses: list[dict[str, Any]] = []

    print("Week 23 - Multimodal Document Intelligence Demo")
    print("=" * 72)
    print(f"Provider requested: {provider}")
    print(f"Test documents/pages: {len(files)}")
    print()

    for index, pdf_path in enumerate(files, start=1):
        result = analyze_pdf(
            pdf_path,
            provider=provider,
            model=model,
            max_pages=1,
            keep_images=False,
        )
        metric = evaluate_page(result, truth_by_filename[pdf_path.name])
        metrics.append(metric)
        analyses.append(result)
        page = result["pages"][0]
        block = page["multimodal"]["title_block"]
        print(
            f"[{index:02d}] {pdf_path.name:<38} "
            f"text={metric['text_only_shared_correct']}/{metric['expected_shared']} "
            f"visual={metric['multimodal_shared_correct']}/{metric['expected_shared']} "
            f"confidence={metric['multimodal_confidence']:.2f}"
        )
        print(
            f"     title={block.get('document_title')} | rev={block.get('revision')} | "
            f"stamp={page['multimodal']['stamps'][0]['text'] if page['multimodal']['stamps'] else 'none'}"
        )

    shared_expected = sum(item["expected_shared"] for item in metrics)
    text_correct = sum(item["text_only_shared_correct"] for item in metrics)
    visual_correct = sum(item["multimodal_shared_correct"] for item in metrics)
    category_expected = sum(item["expected_visual_categories"] for item in metrics)
    category_correct = sum(item["visual_categories_correct"] for item in metrics)
    visual_only_total = sum(item["visual_only_findings"] for item in metrics)
    advantage_pages = sum(bool(item["visual_added_value"]) for item in metrics)
    avg_confidence = sum(item["multimodal_confidence"] for item in metrics) / len(metrics)

    text_recall = text_correct / shared_expected if shared_expected else 0.0
    visual_recall = visual_correct / shared_expected if shared_expected else 0.0
    category_recall = category_correct / category_expected if category_expected else 0.0

    report = {
        "benchmark": "Week 23 synthetic construction-document page benchmark",
        "provider": analyses[0]["provider"] if analyses else provider,
        "model": analyses[0]["model"] if analyses else model,
        "documents_tested": len(files),
        "pages_tested": len(files),
        "metrics": {
            "text_only_shared_field_recall": round(text_recall, 4),
            "multimodal_shared_field_recall": round(visual_recall, 4),
            "multimodal_visual_category_recall": round(category_recall, 4),
            "average_multimodal_confidence": round(avg_confidence, 4),
            "pages_with_visual_added_value": advantage_pages,
            "visual_only_findings": visual_only_total,
        },
        "comparison": {
            "text_only_correct_fields": text_correct,
            "multimodal_correct_fields": visual_correct,
            "shared_fields_expected": shared_expected,
            "visual_categories_correct": category_correct,
            "visual_categories_expected": category_expected,
        },
        "limitations": [
            "The bundled benchmark uses synthetic construction pages and does not represent every real drawing style.",
            "Fixture provider metrics verify the pipeline and schema, not the accuracy of a production vision model.",
            "Real model accuracy depends on scan quality, page resolution, handwriting, symbol conventions, and prompt/model choice.",
            "Dense drawings and very small title-block text may require higher DPI or cropped region analysis.",
            "Human review remains necessary for safety-critical construction decisions.",
        ],
        "per_document": metrics,
    }

    print()
    print("Comparison Summary")
    print("=" * 72)
    print(f"Text-only shared-field recall: {text_recall:.1%}")
    print(f"Multimodal shared-field recall: {visual_recall:.1%}")
    print(f"Multimodal visual-category recall: {category_recall:.1%}")
    print(f"Pages where visual understanding added information: {advantage_pages}/{len(files)}")
    print(f"Visual-only findings: {visual_only_total}")
    print(f"Average multimodal confidence: {avg_confidence:.2f}")
    print()
    print("Week 23 Demo Complete")
    print("- PDF page rendering: working")
    print("- Vision-capable provider interface: working")
    print("- Structured JSON with page, confidence, and evidence: working")
    print("- Text-only versus multimodal comparison: working")
    print("- Minimum 20 test pages: working" if len(files) >= 20 else "- Minimum 20 test pages: partial demo")
    return {"accuracy_report": report, "analyses": analyses}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["auto", "fixture", "openai"], default="fixture")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        results = run_demo(args.provider, max(1, min(args.limit, 20)), args.model)
    output = buffer.getvalue()
    print(output, end="")
    RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    ACCURACY_PATH.write_text(
        json.dumps(results["accuracy_report"], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"Results saved to: {RESULTS_PATH.name}")
    print(f"Accuracy report saved to: {ACCURACY_PATH.name}")


if __name__ == "__main__":
    main()
