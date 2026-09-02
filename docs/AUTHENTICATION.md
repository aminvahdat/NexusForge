# NexusForge Authentication

## Overview

NexusForge implements JWT-based authentication with the following flow:

1. User registers or logs in via `/auth/register` or `/auth/login`
2. Server validates credentials and issues an access token (JWT)
3. Client includes token in `Authorization: Bearer <token>` header
4. Protected routes validate the token and extract user identity

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register new user (email, username, password) |
| `/auth/login` | POST | Authenticate and receive JWT access token |
| `/auth/me` | GET | Get current authenticated user info |
| `/auth/logout` | POST | Invalidate session (token blacklist) |
| `/auth/refresh` | POST | Rotate refresh token, issue new access token |

## Token Details

- **Algorithm**: HS256
- **Access token expiry**: 30 minutes
- **Refresh token expiry**: 7 days
- **Claims**:
  - `sub`: user ID (UUID)
  - `iat`: issued at timestamp
  - `exp`: expiry timestamp
  - `role`: user role(s)

## Password Policy

- Minimum length: 8 characters
- Cannot contain common passwords (checked against breach list)
- Bcrypt hash with cost factor 12

## Error Responses

### Authentication Errors (401)

```json
{
  "detail": "Could not validate credentials"
}
```

### Registration Errors (400/422)

```json
{
  "detail": "Email already registered"
}
```

## Rate Limiting

- Login: 5 attempts per 15 minutes per IP
- Registration: 3 attempts per hour per IP
- Violating IPs blocked with exponential backoff

## Implementation Notes

- Passwords hashed with bcrypt (`passlib.hash.bcrypt`)
- Tokens stored in Redis with TTL matching expiry
- Token revocation: add to Redis blacklist on logout
- Future: MFA/2FA support planned

## Security Audit

See `docs/SECURITY_ARCHITECTURE.md` for full security design and known limitations.