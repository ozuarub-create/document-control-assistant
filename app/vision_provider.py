"""Vision provider implementations for Week 23 multimodal analysis.

The production provider uses the OpenAI Responses API with image input. A
fixture provider is included only for repeatable offline tests and the bundled
synthetic benchmark documents.
"""

from __future__ import annotations

import base64
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.pdf_visualizer import read_fixture_id

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


DEFAULT_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURE_PATH = ROOT_DIR / "multimodal_test_documents" / "ground_truth.json"


VISION_PROMPT = """
You are a construction-document vision analyst. Analyze the supplied PDF page
image visually. Do not rely only on OCR-like text reading: inspect page layout,
title blocks, tables, stamps, revision clouds, drawing notes, symbols, arrows,
callouts, and other visual annotations.

Return JSON only with this exact top-level structure:
{
  "page_summary": "short summary",
  "title_block": {
    "document_title": null,
    "document_type": null,
    "document_number": null,
    "revision": null,
    "project_name": null,
    "discipline": null,
    "date": null,
    "status": null,
    "confidence": 0.0,
    "evidence": "where it appears on the page"
  },
  "tables": [
    {
      "name": "table name",
      "headers": ["header"],
      "rows": [["cell"]],
      "confidence": 0.0,
      "evidence": "location and visible cues"
    }
  ],
  "drawing_notes": [
    {"text": "note", "confidence": 0.0, "evidence": "location"}
  ],
  "stamps": [
    {"text": "stamp text", "status": "approved/reviewed/etc", "confidence": 0.0, "evidence": "location/color/shape"}
  ],
  "revision_information": [
    {"revision": "value", "date": "value", "description": "value", "confidence": 0.0, "evidence": "location"}
  ],
  "symbols_and_annotations": [
    {"symbol": "symbol name", "meaning": "meaning", "confidence": 0.0, "evidence": "location/shape/color"}
  ],
  "visual_only_findings": [
    {"field": "field name", "value": "value", "reason_text_extraction_misses_it": "reason", "confidence": 0.0, "evidence": "location"}
  ],
  "overall_confidence": 0.0
}

Rules:
- Use null or an empty list when information is not visible.
- Confidence values must be numbers from 0 to 1.
- Evidence must identify the page region and visible cue.
- Never invent content that is not visible.
""".strip()


class VisionProvider(ABC):
    name: str
    model_name: str

    @abstractmethod
    def analyze_page(
        self,
        image_path: str | Path,
        *,
        pdf_path: str | Path,
        page_number: int,
        text_context: str = "",
    ) -> dict[str, Any]:
        raise NotImplementedError


class FixtureVisionProvider(VisionProvider):
    """Deterministic provider for the bundled synthetic benchmark only."""

    name = "fixture"
    model_name = "week23-synthetic-ground-truth"

    def __init__(self, fixture_path: str | Path | None = None) -> None:
        self.fixture_path = Path(fixture_path or DEFAULT_FIXTURE_PATH)
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Fixture data not found: {self.fixture_path}")
        self.data = json.loads(self.fixture_path.read_text(encoding="utf-8"))

    def analyze_page(
        self,
        image_path: str | Path,
        *,
        pdf_path: str | Path,
        page_number: int,
        text_context: str = "",
    ) -> dict[str, Any]:
        fixture_id = read_fixture_id(pdf_path)
        if not fixture_id or fixture_id not in self.data:
            raise ValueError(
                "Fixture mode works only with the bundled Week 23 test PDFs. "
                "Use provider=openai for other documents."
            )
        pages = self.data[fixture_id]["pages"]
        if page_number < 1 or page_number > len(pages):
            raise ValueError(f"No fixture data for page {page_number}.")
        result = json.loads(json.dumps(pages[page_number - 1]))
        result["provider_note"] = "Offline deterministic benchmark fixture; not a production vision model."
        return result


class OpenAIVisionProvider(VisionProvider):
    """Vision-capable provider using the OpenAI Responses API."""

    name = "openai"

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is required for provider=openai.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the openai package to use provider=openai.") from exc

        self.model_name = model or DEFAULT_MODEL
        self.client = OpenAI(api_key=key)

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        value = text.strip()
        if value.startswith("```"):
            value = value.split("\n", 1)[1] if "\n" in value else value
            if value.endswith("```"):
                value = value[:-3]
            value = value.strip()
            if value.lower().startswith("json"):
                value = value[4:].lstrip()
        try:
            result = json.loads(value)
        except json.JSONDecodeError as exc:
            start = value.find("{")
            end = value.rfind("}")
            if start >= 0 and end > start:
                result = json.loads(value[start : end + 1])
            else:
                raise ValueError("Vision model did not return valid JSON.") from exc
        if not isinstance(result, dict):
            raise ValueError("Vision model JSON must be an object.")
        return result

    def analyze_page(
        self,
        image_path: str | Path,
        *,
        pdf_path: str | Path,
        page_number: int,
        text_context: str = "",
    ) -> dict[str, Any]:
        image = Path(image_path)
        encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        prompt = VISION_PROMPT
        if text_context.strip():
            prompt += (
                "\n\nThe PDF text layer extracted the following optional context. "
                "Use it only as supporting context and verify visually:\n" + text_context[:2500]
            )
        response = self.client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{encoded}",
                            "detail": "high",
                        },
                    ],
                }
            ],
        )
        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise RuntimeError("Vision model returned no output text.")
        result = self._parse_json(output_text)
        result["provider_note"] = "OpenAI vision analysis of the rendered page image."
        return result


def get_vision_provider(
    provider: str = "auto",
    *,
    pdf_path: str | Path | None = None,
    model: str | None = None,
) -> VisionProvider:
    """Return the requested provider.

    auto mode uses OpenAI when a key is available. For bundled synthetic test
    PDFs only, it falls back to the deterministic fixture provider.
    """

    selected = provider.strip().lower()
    if selected not in {"auto", "openai", "fixture"}:
        raise ValueError("provider must be one of: auto, openai, fixture")
    if selected == "openai":
        return OpenAIVisionProvider(model=model)
    if selected == "fixture":
        return FixtureVisionProvider()
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIVisionProvider(model=model)
    if pdf_path and read_fixture_id(pdf_path):
        return FixtureVisionProvider()
    raise RuntimeError(
        "No vision provider is available. Set OPENAI_API_KEY for real document analysis, "
        "or use a bundled Week 23 test PDF with provider=fixture."
    )
