"""Phase 6 Migration: Worker state tracking and approval enhancements

Revision ID: 1875b06d6a88
Revises: 1875b06d6a87
Create Date: 2026-09-06 22:00:00.000000

Phase 6 — Final Migration & Handover
- Add worker_state table for active worker control
- Enhance approval_requests with action metadata
- Add worker_controls table for pause/resume/retire tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1875b06d6a88'
down_revision = '1875b06d6a87'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Worker state tracking
    op.create_table(
        'worker_states',
        sa.Column('worker_id', sa.String(length=255), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='idle'),
        sa.Column('current_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('worker_id')
    )
    op.create_index('ix_worker_states_status', 'worker_states', ['status'])
    
    # Worker control actions log
    op.create_table(
        'worker_controls',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('worker_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['worker_states.worker_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_worker_controls_worker_id', 'worker_controls', ['worker_id'])
    op.create_index('ix_worker_controls_status', 'worker_controls', ['status'])


def downgrade() -> None:
    op.drop_index('ix_worker_controls_status', table_name='worker_controls')
    op.drop_index('ix_worker_controls_worker_id', table_name='worker_controls')
    op.drop_table('worker_controls')
    op.drop_index('ix_worker_states_status', table_name='worker_states')
    op.drop_table('worker_states')
