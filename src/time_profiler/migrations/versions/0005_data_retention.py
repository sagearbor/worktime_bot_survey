"""add submission summary table for data retention

Revision ID: 0005
Revises: 0004
Create Date: 2025-07-26
"""

from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'submission_summary',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('submission_type', sa.String(), nullable=False),
        sa.Column('summary_data', sa.JSON(), nullable=False),
        sa.Column('start_period', sa.DateTime(), nullable=False),
        sa.Column('end_period', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    op.drop_table('submission_summary')

