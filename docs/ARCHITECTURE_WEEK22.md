# Week 22 Architecture Documentation

## Architecture Style

The final application uses a modular layered architecture:

1. **Presentation Layer** – FastAPI endpoints, Swagger UI, dashboard, login page, and relationship viewer.
2. **Application Services** – document processing, search, review, compliance, relationships, conversation, workflow, authentication, and production diagnostics.
3. **Repository Layer** – SQLite persistence modules for documents, reviews, compliance, relationships, conversations, users, sessions, and audit events.
4. **Data Layer** – SQLite database, document files, compliance reports, and generated documentation.
5. **Deployment Layer** – Docker image, Docker Compose service, environment configuration, persistent volumes, and health checks.

## Main Modules

| Module | Responsibility |
|---|---|
| `app/main.py` | API composition and endpoint integration |
| `app/config.py` | Environment-based configuration |
| `app/auth_api.py` | Authentication and user-management routes |
| `app/auth_service.py` | Password hashing, login, token sessions, and roles |
| `app/auth_repository.py` | User, session, and audit persistence |
| `app/auth_middleware.py` | Optional application-wide Bearer-token enforcement |
| `app/document_processor.py` | PDF/DOCX ingestion and text extraction |
| `app/classifier.py` | Document classification and confidence |
| `app/metadata_extractor.py` | Construction metadata extraction |
| `app/repository.py` | Document register and version tracking |
| `app/search_engine.py` | Metadata, semantic, and natural-language search |
| `app/review_engine.py` | Quality checks, summaries, warnings, and recommendations |
| `app/compliance_engine.py` | Configurable compliance validation |
| `app/relationship_engine.py` | Cross-document references and action-item links |
| `app/conversation_engine.py` | Cited multi-document question answering |
| `app/workflow.py` | Lifecycle states and transition history |
| `app/analytics.py` | Platform metrics and reports |
| `app/production.py` | Readiness checks and release manifest |

## Authentication Flow

1. A user registers or is created by an administrator.
2. The password is stored as a salted PBKDF2-SHA256 hash.
3. Login creates a random opaque access token.
4. Only an HMAC-SHA256 token digest is stored in SQLite.
5. The client sends `Authorization: Bearer <token>`.
6. The middleware or endpoint dependency validates the token, account status, and expiry.
7. Logout revokes the stored session.

## Document Lifecycle Flow

```text
Upload
  → Text extraction
  → Classification
  → Metadata extraction
  → Register/version
  → Review
  → Compliance
  → Workflow
  → Search and relationships
  → Cited conversation
  → Analytics/reporting
```

## Data Model Additions for Week 22

### `users`

Stores username, full name, password hash, role, active status, and timestamps.

### `auth_sessions`

Stores token digest, user link, expiration time, and revocation time.

### `audit_events`

Stores user-management and authentication activity for operational traceability.

## Deployment Architecture

Docker Compose runs one FastAPI service with two persistent named volumes:

- `document_data` for the SQLite register.
- `compliance_data` for generated compliance reports.

The container runs as a non-root user and includes an HTTP health check.

## Security Boundaries

- Secrets and administrator credentials are injected through environment variables.
- `.env` is excluded from Git.
- Passwords and raw tokens are never stored.
- Authentication can remain optional for local coursework compatibility and is enabled in Docker.
- Administrator routes require the `admin` role.

## Architecture Diagram

See `docs/architecture_week22.svg`.
