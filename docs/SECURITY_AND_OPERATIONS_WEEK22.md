# Week 22 Security and Operations

## Authentication

- PBKDF2-SHA256 password hashing with random per-user salt
- Expiring opaque access tokens
- HMAC token digests stored instead of raw tokens
- Session revocation during logout or user deactivation
- Administrator and standard-user roles

## Environment Variables

All deployment-specific settings are read from environment variables. Sensitive values belong in `.env` and must not be committed.

## Required Production Changes

Before production deployment:

1. Set a unique `APP_SECRET_KEY`.
2. Set a strong `DEFAULT_ADMIN_PASSWORD`.
3. Keep `AUTH_REQUIRED=true`.
4. Use HTTPS through a reverse proxy.
5. Restrict database and report-volume access.

## Health and Readiness

- `/health` is suitable for container health checks.
- `/production/readiness` checks the database, writable folders, Docker files, technical documentation, authentication mode, and security settings.

## Audit Events

The application records:

- User registrations
- Successful logins
- Failed logins
- Logouts
- User activation/deactivation

Administrators can inspect events through `GET /auth/audit`.

## Backup

Back up the SQLite database and compliance-report volume. With Docker Compose, these are stored in named volumes.

## Recovery

1. Stop the application.
2. Restore the database file or Docker volume.
3. Restart the service.
4. Verify `/production/readiness` and `/health`.
