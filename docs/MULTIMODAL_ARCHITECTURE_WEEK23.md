# Week 23 Multimodal Architecture

## Purpose

The Week 23 module adds visual page understanding to the existing AI Document Control Assistant. It treats a PDF page as both a text source and an image.

## Processing Flow

```text
PDF Upload
   |
   v
PDF Validation
   |
   +--------------------------+
   |                          |
   v                          v
Text-Layer Extraction     Page Rendering
(PyMuPDF)                 (PNG, configurable DPI)
   |                          |
   v                          v
Text Baseline             Vision Provider
(regex fields)            (OpenAI image input)
   |                          |
   +------------+-------------+
                |
                v
       Structured Normalization
                |
                v
       Text vs Multimodal Comparison
                |
                v
  JSON: page, confidence, evidence, visual-only findings
```

## Main Modules

### `app/pdf_visualizer.py`

- Validates page selections
- Renders PDF pages to PNG
- Extracts the PDF text layer
- Creates the text-only baseline

### `app/vision_provider.py`

- Defines the provider interface
- Implements the OpenAI vision provider
- Implements the deterministic fixture provider for synthetic tests

### `app/multimodal_engine.py`

- Orchestrates rendering and extraction
- Normalizes model output
- Compares text-only and visual results
- Produces page-level and document-level summaries

### `app/multimodal_api.py`

- Exposes upload and comparison APIs
- Returns structured JSON
- Provides capability, test-data, and accuracy-report endpoints

### `app/multimodal_standalone.py`

- Runs the Week 23 service independently on its own port

## Output Contract

Each page contains:

```json
{
  "page_number": 1,
  "text_only": {},
  "multimodal": {
    "title_block": {},
    "tables": [],
    "drawing_notes": [],
    "stamps": [],
    "revision_information": [],
    "symbols_and_annotations": [],
    "visual_only_findings": [],
    "overall_confidence": 0.0
  },
  "comparison": {},
  "evidence": {}
}
```

## Provider Strategy

- `openai`: Real vision-capable model for uploaded project PDFs
- `fixture`: Repeatable synthetic benchmark only
- `auto`: OpenAI when an API key exists; otherwise fixture only for bundled PDFs

## Security and Data Notes

- Uploaded files are processed through temporary files and deleted after analysis.
- Rendered images are temporary by default.
- `keep_images=true` is optional and should be used only when evidence images are required.
- Project teams must review data-governance requirements before sending confidential pages to an external model provider.
