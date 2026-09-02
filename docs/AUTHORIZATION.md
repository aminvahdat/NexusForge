# NexusForge Authorization

## Overview

NexusForge implements Role-Based Access Control (RBAC) with ownership boundary
enforcement. Every protected resource is owned by a specific user, and access
is denied unless the requesting user is the owner or has an admin role.

## Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **Admin** | Full system access | All actions, all resources |
| **User** | Standard authenticated user | Own resources only |

## Ownership Boundaries

### Resource Ownership Matrix

| Resource | Owner Field | Isolation Rule |
|----------|-------------|----------------|
| Project | `owner_id` (UUID FK → users.id) | User must be owner or admin |
| Task | `user_id` (inherited via project) | User must own project or be admin |
| Artifact | `user_id` (direct) | User must own artifact or be admin |
| API Key | `user_id` (direct) | Only key owner can view/edit |
| Notification | `user_id` (direct) | Only recipient can read |
| Memory | `user_id` (scoped) | Project/user memory scoped by owner |
| Approval Request | `requested_by_user_id` | Only requester/owner can access |

## Authorization Enforcement

### Dependency-Based Auth

Protected routes use `Depends(get_current_user)`:
- Extracts JWT from Authorization header
- Validates token signature and expiry
- Loads user from DB by `sub` claim
- Raises `401 Unauthorized` if invalid

### Ownership Checks

Each resource endpoint enforces ownership:

```python
# Example: getting a task
task = await db.get_task(task_id)
if task.user_id != current_user.id and not current_user.is_superuser:
    raise HTTPException(403, "Not authorized to access this task")
```

### IDOR Protection

All endpoint handlers that accept a resource ID perform an explicit ownership
check before returning data. UUIDs are used for all public-facing resource IDs
to make enumeration infeasible.

## IDOR / Horizontal Privilege Escalation Tests

Verified scenarios:
1. User A cannot access User B's projects (tested)
2. User A cannot access User B's tasks (tested)
3. User A cannot access User B's artifacts (tested)
4. User A cannot access User B's API keys (tested)
5. User A cannot access User B's notifications (tested)
6. User A cannot access User B's approval requests (tested)
7. User A cannot access User B's memory (tested)

All tests pass — ownership is enforced at the handler level.

## Future Extensions

- Team-based access: shared resources within a team
- Role inheritance: hierarchical role model
- Policy engine: OPA integration for fine-grained ABAC
- Audit trail: all authorization decisions logged with correlation ID