"""Fix candlestick_data table schema.

This script drops and recreates the candlestick_data table to fix the period column.
Run this from the backend directory:
    python fix_candlestick_table.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.database import engine, Base
from src.models.candlestick_data import CandlestickData
import sqlalchemy as sa

def fix_table():
    """Drop and recreate candlestick_data table."""
    try:
        with engine.connect() as conn:
            # Drop existing table
            conn.execute(sa.text('DROP TABLE IF EXISTS candlestick_data'))
            conn.commit()
            print('✓ Dropped candlestick_data table')
        
        # Recreate table with correct schema
        Base.metadata.create_all(bind=engine, tables=[CandlestickData.__table__])
        print('✓ Recreated candlestick_data table with VARCHAR(10) for period column')
        print('\nTable schema updated successfully!')
        print('The period column now accepts: 5m, 1h, 1d, 1wk, 1mo')
        
    except Exception as e:
        print(f'✗ Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    print('Fixing candlestick_data table schema...\n')
    fix_table()
