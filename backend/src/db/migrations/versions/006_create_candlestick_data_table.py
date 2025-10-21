"""Create candlestick_data table

Revision ID: 006
Revises: 005
Create Date: 2024-01-20 10:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create candlestick_data table for historical OHLCV data."""
    op.create_table(
        'candlestick_data',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='Candlestick data ID (primary key)'),
        sa.Column('symbol', sa.String(length=20), nullable=False, comment='Stock ticker symbol'),
        sa.Column('period', sa.Enum('30m', '1h', '1d', '1wk', '1mo', name='period'), nullable=False, comment='Data interval (30m/1h/1d/1wk/1mo)'),
        sa.Column('date', sa.DateTime(), nullable=False, comment='Candle timestamp'),
        sa.Column('open', sa.DECIMAL(precision=15, scale=4), nullable=False, comment='Opening price'),
        sa.Column('high', sa.DECIMAL(precision=15, scale=4), nullable=False, comment='Highest price in period'),
        sa.Column('low', sa.DECIMAL(precision=15, scale=4), nullable=False, comment='Lowest price in period'),
        sa.Column('close', sa.DECIMAL(precision=15, scale=4), nullable=False, comment='Closing price'),
        sa.Column('adj_close', sa.DECIMAL(precision=15, scale=4), nullable=True, comment='Adjusted close (for splits/dividends)'),
        sa.Column('volume', sa.BigInteger(), nullable=False, comment='Trading volume'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When data was fetched'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'period', 'date', name='uk_symbol_period_date'),
        comment='Historical OHLCV data for candlestick charts',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create indexes
    op.create_index('ix_candlestick_data_symbol', 'candlestick_data', ['symbol'], unique=False)
    op.create_index('ix_candlestick_data_period', 'candlestick_data', ['period'], unique=False)
    op.create_index('ix_candlestick_data_date', 'candlestick_data', ['date'], unique=False)
    op.create_index('ix_candlestick_data_symbol_period', 'candlestick_data', ['symbol', 'period'], unique=False)


def downgrade() -> None:
    """Drop candlestick_data table."""
    op.drop_index('ix_candlestick_data_symbol_period', table_name='candlestick_data')
    op.drop_index('ix_candlestick_data_date', table_name='candlestick_data')
    op.drop_index('ix_candlestick_data_period', table_name='candlestick_data')
    op.drop_index('ix_candlestick_data_symbol', table_name='candlestick_data')
    op.drop_table('candlestick_data')
    
    # Drop enum
    op.execute("DROP TYPE IF EXISTS period")
