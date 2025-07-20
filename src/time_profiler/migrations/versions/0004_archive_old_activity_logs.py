"""archive old activity logs

Revision ID: 0004
Revises: 0003
Create Date: 2025-07-22
"""

from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'archived_activity_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('group_id', sa.String(), nullable=False),
        sa.Column('activity', sa.String(), nullable=False),
        sa.Column('sub_activity', sa.String(), nullable=False),
        sa.Column('hours_work', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('archived_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    op.drop_table('archived_activity_logs')

