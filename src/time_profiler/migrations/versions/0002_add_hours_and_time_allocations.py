"""add hours column and time allocations table

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add hours_work column to activity_logs table
    op.add_column('activity_logs', sa.Column('hours_work', sa.Float(), nullable=True))
    
    # Create time_allocations table
    op.create_table(
        'time_allocations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('group_id', sa.String(), nullable=False),
        sa.Column('activities', sa.JSON(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    # Drop time_allocations table
    op.drop_table('time_allocations')
    
    # Remove hours_work column from activity_logs table  
    op.drop_column('activity_logs', 'hours_work')