"""Create stock_quotes table

Revision ID: 005
Revises: 004
Create Date: 2024-01-20 10:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create stock_quotes table for caching stock data."""
    op.create_table(
        'stock_quotes',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='Stock quote ID (primary key)'),
        sa.Column('symbol', sa.String(length=20), nullable=False, comment='Stock ticker symbol'),
        sa.Column('current_price', sa.DECIMAL(precision=15, scale=4), nullable=False, comment='Current stock price'),
        sa.Column('daily_change_pct', sa.DECIMAL(precision=8, scale=4), nullable=True, comment='Daily change percentage'),
        sa.Column('volume', sa.BigInteger(), nullable=True, comment='Trading volume'),
        sa.Column('market_status', sa.Enum('OPEN', 'CLOSED', name='marketstatus'), nullable=False, comment='Market open/closed status'),
        sa.Column('market', sa.Enum('KR', 'US', name='market'), nullable=False, comment='Market region (KR for Korea, US for USA)'),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False, comment='Last data update time (for TTL)'),
        sa.Column('cache_data', sa.JSON(), nullable=True, comment='Full yfinance response (JSON)'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', name='uk_stock_quotes_symbol'),
        comment='Cached stock quote data (5-minute TTL)',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create indexes
    op.create_index('ix_stock_quotes_symbol', 'stock_quotes', ['symbol'], unique=False)
    op.create_index('ix_stock_quotes_updated_at', 'stock_quotes', ['updated_at'], unique=False)


def downgrade() -> None:
    """Drop stock_quotes table."""
    op.drop_index('ix_stock_quotes_updated_at', table_name='stock_quotes')
    op.drop_index('ix_stock_quotes_symbol', table_name='stock_quotes')
    op.drop_table('stock_quotes')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS marketstatus")
    op.execute("DROP TYPE IF EXISTS market")
