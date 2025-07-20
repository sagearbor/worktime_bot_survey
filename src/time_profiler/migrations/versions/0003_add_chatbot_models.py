"""Add chatbot and temporal data models

Revision ID: 0003
Revises: 0002
Create Date: 2025-07-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None

def upgrade():
    # Create user_submission_history table
    op.create_table('user_submission_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('submission_type', sa.String(), nullable=False),
    sa.Column('submission_data', sa.JSON(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False, default=1),
    sa.Column('is_current', sa.Boolean(), nullable=False, default=True),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('archived_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create chatbot_feedback table
    op.create_table('chatbot_feedback',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('message_text', sa.Text(), nullable=False),
    sa.Column('message_type', sa.String(), nullable=False),
    sa.Column('processed', sa.Boolean(), nullable=False, default=False),
    sa.Column('archived', sa.Boolean(), nullable=False, default=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create problem_identification table
    op.create_table('problem_identification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('category', sa.String(), nullable=True),
    sa.Column('frequency_count', sa.Integer(), nullable=False, default=1),
    sa.Column('first_reported', sa.DateTime(), nullable=False),
    sa.Column('last_reported', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(), nullable=False, default='identified'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create solution_suggestions table
    op.create_table('solution_suggestions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('problem_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('estimated_effort', sa.String(), nullable=True),
    sa.Column('estimated_savings', sa.Float(), nullable=True),
    sa.Column('roi_score', sa.Float(), nullable=True),
    sa.Column('status', sa.String(), nullable=False, default='suggested'),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['problem_id'], ['problem_identification.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create jira_ticket_lifecycle table
    op.create_table('jira_ticket_lifecycle',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('problem_id', sa.Integer(), nullable=False),
    sa.Column('solution_id', sa.Integer(), nullable=True),
    sa.Column('ticket_key', sa.String(), nullable=False),
    sa.Column('ticket_url', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('priority', sa.String(), nullable=True),
    sa.Column('created_date', sa.DateTime(), nullable=False),
    sa.Column('last_updated', sa.DateTime(), nullable=False),
    sa.Column('escalation_count', sa.Integer(), nullable=False, default=0),
    sa.ForeignKeyConstraint(['problem_id'], ['problem_identification.id'], ),
    sa.ForeignKeyConstraint(['solution_id'], ['solution_suggestions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('jira_ticket_lifecycle')
    op.drop_table('solution_suggestions')
    op.drop_table('problem_identification')
    op.drop_table('chatbot_feedback')
    op.drop_table('user_submission_history')