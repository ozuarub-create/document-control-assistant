# Week 23 Accuracy Report and Limitations

## Benchmark Dataset

The repository contains 20 synthetic one-page construction PDFs:

- Drawings
- Specifications
- RFIs
- Meeting minutes
- Inspection reports

Pages 1-10 are image-only PDFs. Pages 11-20 are hybrid PDFs with a small text layer plus visually embedded title blocks, tables, stamps, notes, symbols, and revision annotations.

## Offline Benchmark Result

The saved report is generated with the deterministic fixture provider so automated tests are repeatable.

Key comparison:

- Text-only shared-field recall: approximately 8.3%
- Multimodal fixture shared-field recall: 100%
- Visual-category recall: 100%
- Pages where visual analysis added information: 20 of 20
- Visual-only findings: 60

These numbers validate the pipeline and benchmark schema. They are not a claim about real model accuracy.

## Visual Information Missed by Text Extraction

The benchmark demonstrates that a normal PDF text layer can miss:

- Raster title blocks
- Red approval and review stamps
- Revision clouds
- Drawing callout symbols
- Table structure in scanned pages
- Note-box grouping
- Meaning based on color, shape, and page location

## Real Vision-Model Evaluation

For a production evaluation:

1. Set `OPENAI_API_KEY`.
2. Run `demo_week23.py --provider openai`.
3. Compare the generated output against manually reviewed ground truth.
4. Measure exact-field accuracy, partial matches, false positives, and confidence calibration.
5. Repeat across scan qualities and document types.

## Limitations

- Synthetic pages do not represent every real construction drawing convention.
- Small text may require higher rendering DPI.
- Handwriting and low-quality scans may reduce accuracy.
- Dense drawings may benefit from page-region cropping.
- Vision models may confuse similar symbols without a project-specific legend.
- Color-dependent annotations can be lost in black-and-white scans.
- Confidence is model-reported and should be calibrated using real documents.
- Human review is required for safety-critical engineering decisions.
- External AI processing may require organizational approval for confidential documents.
