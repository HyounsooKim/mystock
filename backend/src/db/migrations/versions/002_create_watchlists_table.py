"""Create watchlists table

Revision ID: 002
Revises: 001
Create Date: 2024-01-20 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create watchlists table with foreign key to users."""
    op.create_table(
        'watchlists',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='Watchlist ID (primary key)'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='User ID (foreign key)'),
        sa.Column('symbol', sa.String(length=20), nullable=False, comment='Stock ticker symbol'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default=sa.text('0'), comment='Display order (0-49, max 50 items)'),
        sa.Column('notes', sa.Text(), nullable=True, comment='User notes about this stock'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When stock was added'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_watchlists_user_id'),
        sa.UniqueConstraint('user_id', 'symbol', name='uk_watchlists_user_symbol'),
        comment='User watchlist for monitoring stocks',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create indexes
    op.create_index('ix_watchlists_user_id_display_order', 'watchlists', ['user_id', 'display_order'], unique=False)


def downgrade() -> None:
    """Drop watchlists table."""
    op.drop_index('ix_watchlists_user_id_display_order', table_name='watchlists')
    op.drop_table('watchlists')
