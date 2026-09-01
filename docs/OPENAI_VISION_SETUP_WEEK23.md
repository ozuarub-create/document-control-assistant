# Week 23 Vision Model Setup

## Environment Variables

Create or update `.env` in the project root:

```text
OPENAI_API_KEY=your-api-key
OPENAI_VISION_MODEL=gpt-4.1-mini
```

The model name is configurable so another vision-capable model can be used without changing the code.

## Install Dependencies

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Test One Real PDF

Start the standalone service:

```bash
python -m uvicorn app.multimodal_standalone:app --reload --port 8001
```

Open `/docs`, expand `POST /multimodal/analyze`, choose a PDF, and use:

```text
provider = openai
max_pages = 1
keep_images = false
```

## Cost Control

- Start with one page.
- Use only relevant page numbers.
- Keep the default 150 DPI unless small text needs higher resolution.
- Avoid analyzing all pages when only title-block or revision pages are relevant.

## Troubleshooting

### Missing key

```text
OPENAI_API_KEY is required for provider=openai.
```

Add the key to `.env` or export it in the terminal.

### Model returns invalid JSON

Retry the page. If the issue continues, use a different supported vision model or reduce the page complexity by analyzing a crop.

### Text is too small

Increase `dpi` to 200 or 250 and analyze only the required page.
