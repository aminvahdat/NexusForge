"""NexusForge Security Architecture Documentation.

This document outlines the security design, authentication, authorization,
secret handling, and known limitations of NexusForge.
"""

# Security Architecture

## Overview
NexusForge is designed with a security-first approach. Authentication and
authorization are implemented before any agent execution capabilities are
activated.

## Authentication

### Token Strategy
- JWT (JSON Web Tokens) with HS256 signing algorithm
- Access tokens: 30-minute expiration
- Refresh tokens: 7-day expiration (rotate on use)
- Tokens stored server-side (Redis with TTL)

### Password Security
- Bcrypt hashing (cost factor 12) for all user passwords
- Passwords validated: minimum 8 characters, complexity requirements
- Password reset: time-limited tokens (15 minutes), single-use
- Email verification: required before first login

## Authorization

### Role-Based Access Control (RBAC)
Two primary roles:
- **Admin**: Full access to all resources
- **User**: Access only to own resources (ownership enforced)

### Resource Ownership
Every protected resource must enforce ownership:
- Project: owned by `owner_id` (UUID FK to users)
- Task: belongs to project, inherited ownership
- Artifact: author_id, project_id, task_id (multi-tenant)
- User API Keys: user_id, encrypted at rest
- Notifications: user_id
- Approval Requests: requested_by_user_id

## Secret Handling

### What is a Secret
- JWT secret key
- Database credentials
- Redis password
- AI provider API keys
- Telegram bot tokens
- Encryption keys

### Storage Rules
- **Environment variables only**: never in source code
- **Server-side only**: never sent to frontend
- **Never logged**: structured logging strips secrets
- **Never in version control**: `.env` is git-ignored
- **Encrypted at rest**: API keys use Fernet symmetric encryption

## API Security

### Request Validation
- Pydantic schema validation for all request bodies
- Type checking and length limits enforced
- Enum validation for status, role, priority fields

### Rate Limiting
- Login attempts: 5 per 15 minutes per IP
- Registration: 3 per hour per IP
- API calls: 100 per minute per authenticated user

### CORS Configuration
- Whitelist allowed origins via `ALLOWED_ORIGINS` env var
- Credentials allowed only for whitelisted origins
- Wildcard (*) never used in production

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'`

### Error Handling
- Production: generic error messages, no stack traces
- Development: detailed errors with stack traces
- All errors logged with correlation IDs

## Database Security

### SQL Injection Prevention
- SQLAlchemy ORM with parameterized queries
- No raw SQL strings with user input
- Input validation at Pydantic schema level

### Connection Security
- PostgreSQL uses asyncpg driver
- Connection pool: 5-20 connections
- TLS required for production connections

## Docker Security

### Container Hardening
- Non-root user in backend container (`nexusforge` UID 1000)
- Read-only filesystem where possible
- No privileged containers
- Resource limits: 2GB RAM, 1 CPU per service

### Network Isolation
- Bridge network for service-to-service communication
- Database ports only exposed to backend
- Redis only accessible within network

## Known Limitations (Documented Honestly)

### Current Phase 3 Limitations
1. **No MFA/2FA**: Two-factor authentication not yet implemented
2. **No OAuth/SSO**: Only email/password authentication
3. **No session management UI**: No way to view/revoke active sessions
4. **Basic password reset**: Email sending not yet integrated
5. **No audit log UI**: Audit events are logged but not queryable via API
6. **Encryption key management**: Single key from env (production should use KMS)

### Future Security Enhancements
- Hardware security module (HSM) integration
- OAuth2/OIDC provider support
- SAML SSO for enterprise
- IP whitelisting per user
- Anomaly detection for unusual API usage
- Encrypted audit log storage with chain verification
- Regular security audit and penetration testing
