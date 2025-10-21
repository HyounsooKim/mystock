"""Create portfolios table

Revision ID: 003
Revises: 002
Create Date: 2024-01-20 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create portfolios table with foreign key to users."""
    op.create_table(
        'portfolios',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='Portfolio ID (primary key)'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='User ID (foreign key)'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Portfolio name (장기투자, 단타, 정찰병)'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Portfolio creation timestamp'),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False, comment='Last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_portfolios_user_id'),
        sa.UniqueConstraint('user_id', 'name', name='uk_portfolios_user_name'),
        comment='User portfolios for organizing holdings',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    """Drop portfolios table."""
    op.drop_table('portfolios')
