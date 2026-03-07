"""add_users_table

Revision ID: 047b08c525ae
Revises: f4002c730af9
Create Date: [timestamp]

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '047b08c525ae'
down_revision = 'f4002c730af9'  # ← CHANGED THIS!
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table"""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('picture', sa.String(), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='student'),
        sa.Column('provider', sa.String(length=50), nullable=True, server_default='local'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)


def downgrade() -> None:
    """Drop users table"""
    
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')