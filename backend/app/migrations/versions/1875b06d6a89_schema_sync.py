"""Schema sync: add missing workspace_path and estimated_tokens

Revision ID: 1875b06d6a89
Revises: 1875b06d6a88
Create Date: 2026-09-13 16:56:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '1875b06d6a89'
down_revision = '1875b06d6a88'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('projects', sa.Column('workspace_path', sa.String(length=500), nullable=True))
    op.add_column('tasks', sa.Column('estimated_tokens', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('tasks', 'estimated_tokens')
    op.drop_column('projects', 'workspace_path')
