# Week 22 User Guide

## 1. Purpose

The AI Document Control Assistant is a standalone construction-document platform. It allows users to upload PDF and DOCX files, classify and register them, search and review documents, check compliance, manage workflow states, explore relationships, and ask cited questions about project content.

## 2. Start the Application

### Local start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Docker start

```bash
cp .env.example .env
docker compose up --build
```

Open `http://127.0.0.1:8000`.

## 3. First Login

Open:

```text
http://127.0.0.1:8000/auth/login-page
```

Development defaults:

```text
Username: admin
Password: Admin123!
```

For Docker, use the credentials configured in `.env`. Change the default password before a public deployment.

The login response contains a Bearer token. In Swagger UI, click **Authorize** and enter the token.

## 4. Basic User Management

- Register a standard user with `POST /auth/register`.
- Log in with `POST /auth/login`.
- View the current account with `GET /auth/me`.
- Administrators can list users through `GET /auth/users`.
- Administrators can activate or deactivate accounts with `PATCH /auth/users/{user_id}/active`.
- Log out with `POST /auth/logout`.

## 5. Upload and Register a Document

1. Open `/docs`.
2. Select `POST /upload`.
3. Click **Try it out**.
4. Upload a PDF or DOCX document.
5. Click **Execute**.

The response includes classification, metadata, review, compliance, workflow, and document-register data.

## 6. Search Documents

Use:

- `GET /documents/search` for metadata filtering.
- `POST /documents/semantic-search` for meaning-based retrieval.
- `POST /documents/query` for simple natural-language search.
- `POST /conversation/ask` for cited conversational answers.

## 7. Conversation History and Citations

The first response from `/conversation/ask` returns a `session_id`. Reuse it for follow-up questions. Supported answers contain structured citations with document title, filename, relevance score, and supporting excerpt.

## 8. Review, Compliance, and Workflow

- `POST /documents/review-upload` produces a quality review.
- `POST /documents/compliance-check` produces a compliance score and report.
- `POST /documents/{document_id}/workflow` changes lifecycle state.
- `GET /documents/{document_id}/versions` shows version history.

## 9. Relationships and Knowledge Graph

Open:

```text
http://127.0.0.1:8000/relationships/viewer
```

The viewer shows linked RFIs, drawings, specifications, meeting minutes, and action items.

## 10. Dashboard and Readiness

- Dashboard: `/dashboard`
- Analytics JSON: `/documents/analytics`
- Production readiness: `/production/readiness`
- Release manifest: `/production/manifest`

## 11. Troubleshooting

### `python` is not found

Use:

```bash
python3 -m uvicorn app.main:app --reload
```

### Authentication error

Log in again and use the new Bearer token.

### Port 8000 is in use

Stop the old server with `Control + C`, or run on another port:

```bash
python -m uvicorn app.main:app --port 8001
```

### Docker application does not start

Run:

```bash
docker compose logs -f
```

Confirm `.env` exists and contains valid values.
