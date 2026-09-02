# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within NexusForge, please follow these guidelines:

### How to Report

1. **Do not** create a public GitHub issue for security vulnerabilities
2. Send a detailed report to **security@nexusforge.org**
3. Include the following information:
   - Type of vulnerability
   - Full paths of source file(s) related to the vulnerability
   - Location of the affected source code
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact assessment of the vulnerability

### Response Timeline

- **Initial Response**: Within 48 hours of report submission
- **Status Update**: Within 7 days with progress updates
- **Resolution**: Target timeline of 30 days for critical issues

### Scope

NexusForge is committed to ensuring the security of our users and their data. The following areas are within our security scope:

### In Scope

- Authentication and authorization mechanisms
- User data isolation and privacy
- API security and rate limiting
- Worker process isolation
- Secret management and storage
- Session management
- Input validation and sanitization
- Dependency security
- Docker container security
- Configuration security

### Out of Scope

- User-provided API keys (user responsibility)
- User infrastructure security (deployment responsibility)
- Social engineering attacks
- Physical security
- Denial of service attacks (mitigation only)
- Security misconfigurations by administrators

## Security Architecture

### Authentication

NexusForge implements secure authentication using:
- bcrypt password hashing with salt
- JWT access and refresh tokens
- Session management with secure cookies
- Rate limiting on authentication endpoints
- Brute-force protection

### Authorization

Role-based access control (RBAC) ensures:
- Users can only access their own resources
- Role-based permissions for different actions
- User isolation at the database level
- Resource scoping by user and project

### Data Protection

- Encryption at rest for sensitive data
- Secure transmission (TLS/SSL)
- Secret handling rules (never in logs, never in frontend after saving)
- Context isolation for AI agent workers

### Worker Security

Workers operate with:
- Process-level isolation
- Tool permission levels (SAFE, LIMITED, PRIVILEGED, DANGEROUS)
- No access to host system outside project workspace
- Explicit human approval for dangerous operations

## Security Best Practices

### For Users

1. **Use strong passwords**: Minimum 8 characters with mixed case, numbers, and special characters
2. **Enable two-factor authentication**: When available (future enhancement)
3. **Keep API keys secure**: Never share or commit to version control
4. **Review permissions**: Regularly review which agents have access to what
5. **Monitor activity**: Review audit logs and project activity
6. **Report issues**: Report security concerns immediately

### For Administrators

1. **Secure deployment**: Follow security hardening guidelines
2. **Regular updates**: Keep NexusForge and dependencies updated
3. **Network security**: Use firewalls and network segmentation
4. **Monitoring**: Set up monitoring and alerting
5. **Backup security**: Encrypt backups and store securely
6. **Access control**: Follow least-privilege principles

### For Developers

1. **Secure coding**: Follow OWASP guidelines
2. **Input validation**: Validate all user input
3. **Output encoding**: Encode output appropriately
4. **Dependency management**: Keep dependencies updated
5. **Security testing**: Include security tests in CI/CD
6. **Code review**: Security-focused code review

## Security Updates

### How to Stay Updated

1. **Watch the repository**: Enable notifications for releases
2. **Security mailing list**: Subscribe to security announcements (future)
3. **GitHub Security Advisories**: Enable GitHub security alerts

### Update Process

When a security update is released:
1. Security advisory published with details
2. Patched version released
3. Upgrade instructions provided
4. Migration guide if needed

## Security Configuration

### Recommended Security Settings

```yaml
# Authentication
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS: 7
ACCOUNT_LOCKOUT_ATTEMPTS: 5
ACCOUNT_LOCKOUT_DURATION: 1800

# Rate Limiting
RATE_LIMIT_PER_MINUTE: 60
RATE_LIMIT_PER_HOUR: 1000

# Worker Security
DEFAULT_WORKER_PERMISSION: SAFE
REQUIRE_APPROVAL_FOR_DANGEROUS: true
```

## Compliance

NexusForge is designed with security compliance in mind:
- **OWASP Top 10**: Addresses common web application vulnerabilities
- **GDPR Ready**: User data protection and deletion capabilities
- **Data Minimization**: Only collects necessary data
- **Privacy by Design**: Security built into the architecture

## Security Acknowledgments

We would like to thank all security researchers and contributors who help keep NexusForge secure.

## Contact

For security-related questions or concerns:
- **Email**: security@nexusforge.org
- **Response Time**: 48 hours for non-critical, 24 hours for critical issues

## Disclosure Policy

We follow a coordinated disclosure process:
1. Researcher reports vulnerability
2. We confirm receipt within 48 hours
3. We investigate and develop fix
4. We coordinate disclosure timeline with researcher
5. Public disclosure with credit to researcher (with permission)

## Security Training

Contributors are encouraged to:
- Review OWASP resources
- Complete secure coding training
- Stay updated on security best practices
- Participate in security code reviews