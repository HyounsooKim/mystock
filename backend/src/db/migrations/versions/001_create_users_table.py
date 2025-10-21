"""Create users table

Revision ID: 001
Revises: 
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table with authentication fields."""
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='User ID (primary key)'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='User email (unique, login ID)'),
        sa.Column('password_hash', sa.String(length=255), nullable=False, comment='Hashed password (bcrypt)'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Account creation timestamp'),
        sa.Column('last_login_at', sa.TIMESTAMP(), nullable=True, comment='Last login timestamp'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False, comment='Account active status (soft delete)'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uk_users_email'),
        comment='User authentication and account information',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)


def downgrade() -> None:
    """Drop users table."""
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
