"""add_progress_tracking

Revision ID: f0ea8f80b68c
Revises: df1a51ff1427
Create Date: 2026-03-29 07:30:53.078033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f0ea8f80b68c'
down_revision: Union[str, Sequence[str], None] = 'df1a51ff1427'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create student_interactions table
    op.create_table(
        'student_interactions',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('user_id', sa.String(36), nullable=False),  # ✅ FIXED: String to match users.id
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('topic', sa.String(100)),
        sa.Column('chapter_code', sa.String(50)),
        sa.Column('question_text', sa.Text()),
        sa.Column('user_answer', sa.Text()),
        sa.Column('is_correct', sa.Boolean()),
        sa.Column('time_spent_seconds', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for student_interactions
    op.create_index('idx_user_interactions', 'student_interactions', ['user_id', 'created_at'])
    op.create_index('idx_topic_interactions', 'student_interactions', ['topic'])
    
    # Create topic_mastery table
    op.create_table(
        'topic_mastery',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('user_id', sa.String(36), nullable=False),  # ✅ FIXED: String to match users.id
        sa.Column('topic', sa.String(100), nullable=False),
        sa.Column('chapter_code', sa.String(50)),
        sa.Column('total_questions_attempted', sa.Integer(), default=0),
        sa.Column('correct_answers', sa.Integer(), default=0),
        sa.Column('mastery_percentage', sa.Float(), default=0.0),
        sa.Column('last_practiced_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for topic_mastery
    op.create_index('idx_user_mastery', 'topic_mastery', ['user_id'])
    op.create_index('idx_topic_mastery', 'topic_mastery', ['topic'])
    
    # Create unique constraint: one record per user per topic
    op.create_unique_constraint(
        'uq_user_topic_mastery',
        'topic_mastery',
        ['user_id', 'topic']
    )

def downgrade():
    op.drop_table('topic_mastery')
    op.drop_table('student_interactions')