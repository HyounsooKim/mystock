"""Create holdings table

Revision ID: 004
Revises: 003
Create Date: 2024-01-20 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create holdings table with foreign key to portfolios."""
    op.create_table(
        'holdings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='Holding ID (primary key)'),
        sa.Column('portfolio_id', sa.BigInteger(), nullable=False, comment='Portfolio ID (foreign key)'),
        sa.Column('symbol', sa.String(length=20), nullable=False, comment='Stock ticker symbol'),
        sa.Column('quantity', sa.DECIMAL(precision=15, scale=4), nullable=False, comment='Number of shares (supports fractional)'),
        sa.Column('avg_price', sa.DECIMAL(precision=15, scale=4), nullable=False, comment='Average purchase price per share'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When holding was created'),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False, comment='Last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE', name='fk_holdings_portfolio_id'),
        sa.UniqueConstraint('portfolio_id', 'symbol', name='uk_holdings_portfolio_symbol'),
        sa.CheckConstraint('quantity > 0', name='ck_holdings_quantity_positive'),
        sa.CheckConstraint('avg_price > 0', name='ck_holdings_avg_price_positive'),
        comment='Portfolio holdings with purchase information',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    """Drop holdings table."""
    op.drop_table('holdings')
