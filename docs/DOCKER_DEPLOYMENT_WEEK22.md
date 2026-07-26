# Week 22 Docker Deployment

## Prerequisites

- Docker Desktop for macOS
- The project folder open in VS Code

## 1. Create Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` and replace:

```text
APP_SECRET_KEY
DEFAULT_ADMIN_PASSWORD
```

Use a long random secret and a strong password.

## 2. Build and Start

```bash
docker compose up --build
```

Open:

```text
http://127.0.0.1:8000
```

## 3. Verify Deployment

```bash
docker compose ps
```

The service should become `healthy`.

Check readiness:

```text
http://127.0.0.1:8000/production/readiness
```

## 4. View Logs

```bash
docker compose logs -f
```

## 5. Stop

```bash
docker compose down
```

## 6. Stop and Delete Persistent Data

Only use this when a full reset is required:

```bash
docker compose down -v
```

## Persistent Data

Docker named volumes preserve:

- The SQLite document database
- Generated compliance reports

## Production Notes

- Keep `AUTH_REQUIRED=true`.
- Never commit `.env`.
- Change the default administrator password.
- Back up Docker volumes regularly.
- Use HTTPS through a reverse proxy for an internet-facing deployment.
