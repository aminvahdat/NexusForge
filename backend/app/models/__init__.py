"""Database models for NexusForge."""

from uuid import uuid4
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from .base import Base
from .enums import TaskStatus, AgentRole, Priority, WorkerStatus, PermissionLevel, RiskLevel
import re

Base = Base


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)

    projects = relationship('Project', back_populates='owner')
    api_keys = relationship('UserAPIKey', back_populates='user')
    memory = relationship('UserMemory', back_populates='user', uselist=False)
    notifications = relationship('Notification', back_populates='user')
    approval_requests = relationship('ApprovalRequest', foreign_keys='ApprovalRequest.requested_by_user_id', back_populates='requested_by_user')

    __table_args__ = (
        Index('ix_users_email_lower', func.lower(email)),
        Index('ix_users_created_at', created_at),
    )

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            raise ValueError('Invalid email format')
        return email.lower()

    @validates('username')
    def validate_username(self, key, username):
        if username and not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return username

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'email': self.email,
            'username': self.username,
            'is_active': self.is_active,
            'is_superuser': self.is_superuser,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'email_verified': self.email_verified,
        }

    def __repr__(self):
        return f'<User {self.email}>'


class Project(Base):
    """Project model for AI development coordination."""

    __tablename__ = 'projects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    status = Column(String(50), default='active', index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    ai_provider = Column(String(100), nullable=True)
    ai_model = Column(String(100), nullable=True)
    preferred_language = Column(String(10), default='en')
    timezone = Column(String(50), default='UTC')
    telegram_notifications_enabled = Column(Boolean, default=False)
    telegram_chat_id = Column(String(100), nullable=True)

    owner = relationship('User', back_populates='projects')
    tasks = relationship('Task', back_populates='project')
    artifacts = relationship('Artifact', back_populates='project')
    memory = relationship('ProjectMemory', back_populates='project', uselist=False)

    __table_args__ = (
        Index('ix_projects_owner_created', owner_id, created_at),
        Index('ix_projects_name_lower', func.lower(name)),
        UniqueConstraint('name', 'owner_id', name='uq_project_name_owner'),
    )

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'owner_id': str(self.owner_id),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'preferred_language': self.preferred_language,
            'timezone': self.timezone,
            'telegram_notifications_enabled': self.telegram_notifications_enabled,
            'telegram_chat_id': self.telegram_chat_id,
        }

    def __repr__(self):
        return f'<Project {self.name}>'


class Task(Base):
    """Task model for agent execution and tracking."""

    __tablename__ = 'tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    role = Column(String(100), nullable=False)
    status = Column(String(50), default='queued', nullable=False, index=True)
    priority = Column(String(20), default='medium')
    required_skills = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    input_artifacts = Column(JSON, default=list)
    output_artifacts = Column(JSON, default=list)
    assigned_worker_id = Column(UUID(as_uuid=True), nullable=True)
    acceptance_criteria = Column(JSON, default=list)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_tokens = Column(Integer, nullable=True)

    project = relationship('Project', back_populates='tasks')

    __table_args__ = (
        Index('ix_tasks_project_status_created', project_id, status, created_at),
        Index('ix_tasks_assigned_worker_status', assigned_worker_id, status),
        Index('ix_tasks_role_status', role, status),
    )

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'project_id': str(self.project_id),
            'title': self.title,
            'description': self.description,
            'role': self.role,
            'status': self.status,
            'priority': self.priority,
            'required_skills': self.required_skills,
            'dependencies': self.dependencies,
            'input_artifacts': self.input_artifacts,
            'output_artifacts': self.output_artifacts,
            'assigned_worker_id': str(self.assigned_worker_id) if self.assigned_worker_id else None,
            'acceptance_criteria': self.acceptance_criteria,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f'<Task {self.title}>'


class Artifact(Base):
    """Artifact model for storing task outputs and project artifacts."""

    __tablename__ = 'artifacts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    version = Column(String(50), default='1.0')
    description = Column(Text, nullable=True)
    path = Column(String(1000), nullable=False)
    size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    checksum = Column(String(64), nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    extra_data = Column(JSON, default=dict)
    is_public = Column(Boolean, default=False)

    project = relationship('Project', back_populates='artifacts')

    __table_args__ = (
        Index('ix_artifacts_project_type', project_id, type),
        Index('ix_artifacts_task_created', task_id, created_at),
        Index('ix_artifacts_author_created', author_id, created_at),
    )

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'project_id': str(self.project_id),
            'task_id': str(self.task_id) if self.task_id else None,
            'name': self.name,
            'type': self.type,
            'version': self.version,
            'description': self.description,
            'path': self.path,
            'size': self.size,
            'mime_type': self.mime_type,
            'checksum': self.checksum,
            'author_id': str(self.author_id) if self.author_id else None,
            'created_at': self.created_at.isoformat(),
            'extra_data': self.extra_data,
            'is_public': self.is_public,
        }

    def __repr__(self):
        return f'<Artifact {self.name}>'


class UserAPIKey(Base):
    """User API key model for external service access."""

    __tablename__ = 'user_api_keys'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    api_key = Column(String(500), nullable=False)
    model = Column(String(100), nullable=True)
    max_tokens = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship('User', back_populates='api_keys')

    __table_args__ = (
        Index('ix_user_api_keys_user_provider', user_id, provider),
    )

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': self.name,
            'provider': self.provider,
            'model': self.model,
            'max_tokens': self.max_tokens,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }

    def __repr__(self):
        return f'<UserAPIKey {self.name}>'


class Worker(Base):
    """Worker model for tracking Hermes instances."""

    __tablename__ = 'workers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    worker_id = Column(String(100), unique=True, nullable=False, index=True)
    hostname = Column(String(255), nullable=True)
    status = Column(String(50), default='idle', nullable=False, index=True)
    current_task_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    role = Column(String(100), nullable=True)
    skills = Column(JSON, default=list)
    memory = Column(JSON, default=dict)
    tools = Column(JSON, default=list)
    toolsets = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    max_concurrent_tasks = Column(Integer, default=1)
    current_task_count = Column(Integer, default=0)
    resource_usage = Column(JSON, default=dict)

    __table_args__ = (
        Index('ix_workers_status_heartbeat', status, last_heartbeat),
        Index('ix_workers_role_status', role, status),
    )

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'worker_id': self.worker_id,
            'hostname': self.hostname,
            'status': self.status,
            'current_task_id': str(self.current_task_id) if self.current_task_id else None,
            'role': self.role,
            'skills': self.skills,
            'memory': self.memory,
            'tools': self.tools,
            'toolsets': self.toolsets,
            'created_at': self.created_at.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'current_task_count': self.current_task_count,
            'resource_usage': self.resource_usage,
        }

    def __repr__(self):
        return f'<Worker {self.worker_id}>'


class ProjectMemory(Base):
    """Project memory for storing project-specific knowledge."""

    __tablename__ = 'project_memory'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, unique=True)
    scope = Column(String(50), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship('Project', back_populates='memory')

    __table_args__ = (
        Index('ix_project_memory_scope_key', scope, key),
        Index('ix_project_memory_project_scope', project_id, scope),
    )

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'project_id': str(self.project_id),
            'scope': self.scope,
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': str(self.created_by) if self.created_by else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }

    def __repr__(self):
        return f'<ProjectMemory {self.scope}.{self.key}>'


class UserMemory(Base):
    """User memory for storing user-specific preferences."""

    __tablename__ = 'user_memory'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    scope = Column(String(50), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship('User', back_populates='memory')

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'scope': self.scope,
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<UserMemory {self.scope}.{self.key}>'


class Notification(Base):
    """Notification model for user notifications."""

    __tablename__ = 'notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, default=dict)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship('User', back_populates='notifications')

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None,
        }

    def __repr__(self):
        return f'<Notification {self.type}>'


class ApprovalRequest(Base):
    """Approval request model for human approval of dangerous operations."""

    __tablename__ = 'approval_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False, index=True)
    requested_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    risk_level = Column(String(50), nullable=False)
    status = Column(String(50), default='pending', nullable=False, index=True)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    outcome = Column(String(255), nullable=True)

    task = relationship('Task')
    requested_by_user = relationship('User', foreign_keys=[requested_by_user_id])
    approved_by_user = relationship('User', foreign_keys=[approved_by_user_id])

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'task_id': str(self.task_id),
            'requested_by_user_id': str(self.requested_by_user_id),
            'action': self.action,
            'reason': self.reason,
            'risk_level': self.risk_level,
            'status': self.status,
            'requested_at': self.requested_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'approved_by_user_id': str(self.approved_by_user_id) if self.approved_by_user_id else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'outcome': self.outcome,
        }

    def __repr__(self):
        return f'<ApprovalRequest {self.action}>'


class SystemMemory(Base):
    """System memory for global reusable knowledge."""

    __tablename__ = 'system_memory'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key = Column(String(255), nullable=False, unique=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String(100), nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
        }

    def __repr__(self):
        return f'<SystemMemory {self.key}>'


class WorkerLog(Base):
    """Worker log model for tracking worker operations."""

    __tablename__ = 'worker_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey('workers.id'), nullable=False, index=True)
    level = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'worker_id': str(self.worker_id),
            'level': self.level,
            'message': self.message,
            'context': self.context,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<WorkerLog {self.level}>'
