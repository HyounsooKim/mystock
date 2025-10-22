# Data Model: Personalized Stock Portfolio App

**Feature**: 001-personalized-stock-portfolio  
**Date**: 2025-10-21  
**Phase**: 1 (Design & Contracts)

## Overview

This document defines the complete database schema for the Personalized Stock Portfolio application using Azure MySQL 8.0. The schema supports user authentication, watchlists, portfolios with holdings, and cached stock quote data from yfinance.

---

## Entity Relationship Diagram

```
┌─────────────────┐
│     users       │
│─────────────────│
│ id (PK)         │
│ email (UNIQUE)  │
│ password_hash   │
│ created_at      │
│ last_login_at   │
└─────────────────┘
         │
         │ 1:N
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌──────────────────┐
│   watchlists    │       │   portfolios     │
│─────────────────│       │──────────────────│
│ id (PK)         │       │ id (PK)          │
│ user_id (FK)    │       │ user_id (FK)     │
│ symbol          │       │ name             │
│ display_order   │       │ created_at       │
│ notes (TEXT)    │       │ updated_at       │
│ created_at      │       └──────────────────┘
└─────────────────┘                │
                                   │ 1:N
                                   ▼
                          ┌──────────────────┐
                          │     holdings     │
                          │──────────────────│
                          │ id (PK)          │
                          │ portfolio_id (FK)│
                          │ symbol           │
                          │ quantity         │
                          │ avg_price        │
                          │ created_at       │
                          │ updated_at       │
                          └──────────────────┘

┌─────────────────────────────┐
│       stock_quotes          │
│─────────────────────────────│
│ id (PK)                     │
│ symbol (UNIQUE)             │
│ current_price               │
│ daily_change_pct            │
│ volume                      │
│ market_status               │
│ market (KR/US)              │
│ updated_at                  │
│ cache_data (JSON)           │
└─────────────────────────────┘

┌─────────────────────────────┐
│    candlestick_data         │
│─────────────────────────────│
│ id (PK)                     │
│ symbol                      │
│ period (30m/1h/1d/1wk/1mo)  │
│ date                        │
│ open                        │
│ high                        │
│ low                         │
│ close                       │
│ adj_close                   │
│ volume                      │
│ created_at                  │
└─────────────────────────────┘
```

---

## Table Definitions

### 1. users

**Purpose**: Store user account information with email/password authentication

```sql
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt hash with cost factor 12',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Soft delete flag',
    
    INDEX idx_email (email),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='User accounts with email/password authentication';
```

**Fields**:
- `id`: Primary key, auto-increment
- `email`: User email address, unique constraint for login
- `password_hash`: bcrypt hashed password (never store plaintext)
- `created_at`: Account creation timestamp
- `last_login_at`: Last successful login (for analytics)
- `is_active`: Soft delete flag (FALSE when user requests account deletion)

**Constraints**:
- Email must be valid format (enforced in application layer)
- Password hash must be bcrypt with cost factor 12
- Email unique index for fast login lookups

**Sample Data**:
```sql
INSERT INTO users (email, password_hash) VALUES
('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztP7IqZpKYXW');
```

---

### 2. watchlists

**Purpose**: Store user's favorite stock symbols with custom ordering

```sql
CREATE TABLE watchlists (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL COMMENT 'Stock ticker (e.g., AAPL, 005930.KS)',
    display_order INT DEFAULT 0 COMMENT 'User-defined sort order',
    notes TEXT NULL COMMENT 'Optional user notes for this stock',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_symbol (user_id, symbol) COMMENT 'Prevent duplicate watchlist entries',
    INDEX idx_user_order (user_id, display_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='User watchlists with up to 50 items per user';
```

**Fields**:
- `id`: Primary key
- `user_id`: Foreign key to users table
- `symbol`: Stock ticker symbol (AAPL, 005930.KS, etc.)
- `display_order`: Integer for drag-and-drop ordering (0-49)
- `notes`: Optional text field for user's private notes
- `created_at`: When symbol was added to watchlist

**Constraints**:
- `user_id` + `symbol` unique constraint (no duplicates per user)
- Max 50 items per user (enforced in application layer)
- Cascade delete when user account is deleted

**Sample Data**:
```sql
INSERT INTO watchlists (user_id, symbol, display_order, notes) VALUES
(1, 'AAPL', 0, '애플 장기 보유'),
(1, '005930.KS', 1, '삼성전자 매수 검토'),
(1, 'TSLA', 2, NULL);
```

---

### 3. portfolios

**Purpose**: Three predefined portfolio types per user ("장기투자", "단기투자", "정찰병")

```sql
CREATE TABLE portfolios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(50) NOT NULL COMMENT 'Portfolio name (장기투자, 단기투자, 정찰병)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_name (user_id, name) COMMENT 'Each user has exactly 3 portfolios',
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Three predefined portfolios per user';
```

**Fields**:
- `id`: Primary key
- `user_id`: Foreign key to users table
- `name`: Portfolio name (must be one of: "장기투자", "단기투자", "정찰병")
- `created_at`: Portfolio creation timestamp
- `updated_at`: Last modification timestamp

**Constraints**:
- `user_id` + `name` unique constraint
- Exactly 3 portfolios per user (enforced in application layer)
- Allowed names: "장기투자", "단기투자", "정찰병" (enum validation in application)

**Initialization**:
```sql
-- Trigger to auto-create 3 portfolios when user registers
DELIMITER $$
CREATE TRIGGER after_user_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO portfolios (user_id, name) VALUES
    (NEW.id, '장기투자'),
    (NEW.id, '단기투자'),
    (NEW.id, '정찰병');
END$$
DELIMITER ;
```

**Sample Data**:
```sql
INSERT INTO portfolios (user_id, name) VALUES
(1, '장기투자'),
(1, '단기투자'),
(1, '정찰병');
```

---

### 4. holdings

**Purpose**: Store stock holdings (symbol, quantity, average price) within portfolios

```sql
CREATE TABLE holdings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL COMMENT 'Stock ticker',
    quantity DECIMAL(15, 4) NOT NULL COMMENT 'Number of shares (supports fractional shares)',
    avg_price DECIMAL(15, 4) NOT NULL COMMENT 'Average purchase price per share',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    UNIQUE KEY uk_portfolio_symbol (portfolio_id, symbol) COMMENT 'One entry per symbol per portfolio',
    INDEX idx_portfolio_id (portfolio_id),
    CHECK (quantity > 0),
    CHECK (avg_price > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Stock holdings within portfolios (max 100 per portfolio)';
```

**Fields**:
- `id`: Primary key
- `portfolio_id`: Foreign key to portfolios table
- `symbol`: Stock ticker symbol
- `quantity`: Number of shares (DECIMAL to support fractional shares)
- `avg_price`: Average purchase price per share
- `created_at`: When holding was added
- `updated_at`: Last modification timestamp

**Constraints**:
- `portfolio_id` + `symbol` unique constraint (combine quantities if duplicate)
- Max 100 holdings per portfolio (enforced in application layer)
- `quantity` and `avg_price` must be positive (CHECK constraints)

**Calculated Fields** (in application layer):
```python
current_value = quantity * current_price  # From stock_quotes
cost_basis = quantity * avg_price
profit_loss = current_value - cost_basis
return_rate = (profit_loss / cost_basis) * 100
```

**Sample Data**:
```sql
INSERT INTO holdings (portfolio_id, symbol, quantity, avg_price) VALUES
(1, 'AAPL', 10.0000, 150.2500),
(1, '005930.KS', 5.0000, 72000.0000),
(2, 'TSLA', 2.5000, 245.7500);
```

---

### 5. stock_quotes

**Purpose**: Cache stock quote data from yfinance API (5-minute TTL)

```sql
CREATE TABLE stock_quotes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE COMMENT 'Stock ticker',
    current_price DECIMAL(15, 4) NULL COMMENT 'Latest trading price',
    daily_change_pct DECIMAL(8, 4) NULL COMMENT 'Daily percentage change',
    volume BIGINT NULL COMMENT 'Trading volume',
    market_status ENUM('open', 'closed') DEFAULT 'closed',
    market ENUM('KR', 'US') NOT NULL COMMENT 'Korean or US market',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    cache_data JSON NULL COMMENT 'Full yfinance response for extensibility',
    
    INDEX idx_symbol_updated (symbol, updated_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Cached stock quotes with 5-minute TTL';
```

**Fields**:
- `id`: Primary key
- `symbol`: Stock ticker symbol (unique)
- `current_price`: Latest trading price
- `daily_change_pct`: Daily percentage change (e.g., +2.5%)
- `volume`: Trading volume
- `market_status`: 'open' (장중) or 'closed' (마감)
- `market`: 'KR' (Korean) or 'US' (American)
- `updated_at`: Timestamp for TTL calculation
- `cache_data`: JSON field storing full yfinance response for future extensibility

**TTL Logic**:
```sql
-- Check if cache is still valid (< 5 minutes old)
SELECT * FROM stock_quotes
WHERE symbol = ?
  AND updated_at > NOW() - INTERVAL 5 MINUTE;
```

**Sample Data**:
```sql
INSERT INTO stock_quotes (symbol, current_price, daily_change_pct, volume, market_status, market, cache_data) VALUES
('AAPL', 175.4300, 1.2500, 54321000, 'closed', 'US', '{"longName": "Apple Inc.", "exchange": "NASDAQ"}'),
('005930.KS', 71500.0000, -0.6900, 12345678, 'open', 'KR', '{"longName": "Samsung Electronics Co., Ltd.", "exchange": "KRX"}');
```

---

### 6. candlestick_data

**Purpose**: Store historical OHLCV data for chart rendering (5 period options)

```sql
CREATE TABLE candlestick_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT 'Stock ticker',
    period ENUM('30m', '1h', '1d', '1wk', '1mo') NOT NULL COMMENT 'Data interval',
    date DATETIME NOT NULL COMMENT 'Candle timestamp',
    open DECIMAL(15, 4) NOT NULL,
    high DECIMAL(15, 4) NOT NULL,
    low DECIMAL(15, 4) NOT NULL,
    close DECIMAL(15, 4) NOT NULL,
    adj_close DECIMAL(15, 4) NULL COMMENT 'Adjusted close price',
    volume BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_symbol_period_date (symbol, period, date),
    INDEX idx_symbol_period (symbol, period),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Historical OHLCV data for candlestick charts';
```

**Fields**:
- `id`: Primary key
- `symbol`: Stock ticker symbol
- `period`: Data interval (30m, 1h, 1d, 1wk, 1mo)
- `date`: Candle timestamp (e.g., 2025-10-21 09:30:00)
- `open`: Opening price
- `high`: Highest price in period
- `low`: Lowest price in period
- `close`: Closing price
- `adj_close`: Adjusted close (for splits/dividends)
- `volume`: Trading volume
- `created_at`: When data was fetched

**Period Mappings** (from spec clarification):
- `30m` interval → 2 day period
- `1h` interval → 1 week period
- `1d` interval → 6 month period
- `1wk` interval → 2 year period
- `1mo` interval → 7 year period

**Sample Data**:
```sql
INSERT INTO candlestick_data (symbol, period, date, open, high, low, close, adj_close, volume) VALUES
('AAPL', '1d', '2025-10-20', 174.5000, 176.2000, 173.8000, 175.4300, 175.4300, 54321000),
('AAPL', '1d', '2025-10-21', 175.5000, 177.0000, 174.9000, 176.1500, 176.1500, 48765000),
('005930.KS', '1d', '2025-10-20', 72000.0000, 72500.0000, 71200.0000, 71500.0000, 71500.0000, 12345678);
```

---

## Indexes and Performance

### Index Strategy

**Primary Indexes**:
- All tables have auto-increment `id` as primary key
- Foreign keys automatically indexed by MySQL InnoDB

**Composite Indexes**:
```sql
-- Watchlist queries by user and order
CREATE INDEX idx_user_order ON watchlists(user_id, display_order);

-- Stock quote cache lookup
CREATE INDEX idx_symbol_updated ON stock_quotes(symbol, updated_at);

-- Candlestick data queries
CREATE INDEX idx_symbol_period ON candlestick_data(symbol, period);

-- Portfolio holdings lookup
CREATE INDEX idx_portfolio_id ON holdings(portfolio_id);
```

### Query Patterns

**Most Frequent Queries**:

1. Get user's watchlist (sorted):
```sql
SELECT * FROM watchlists
WHERE user_id = ?
ORDER BY display_order;
```

2. Get cached stock quote (with TTL check):
```sql
SELECT * FROM stock_quotes
WHERE symbol = ?
  AND updated_at > NOW() - INTERVAL 5 MINUTE;
```

3. Get portfolio holdings with current value:
```sql
SELECT h.*, sq.current_price, sq.daily_change_pct
FROM holdings h
JOIN stock_quotes sq ON h.symbol = sq.symbol
WHERE h.portfolio_id = ?;
```

4. Get candlestick data for chart:
```sql
SELECT * FROM candlestick_data
WHERE symbol = ? AND period = ?
ORDER BY date DESC
LIMIT 200;  -- Adjust based on period
```

---

## Data Validation Rules

### Application-Layer Validations

**users**:
- Email: Must match regex `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Password: Min 8 chars, at least one uppercase, one lowercase, one digit

**watchlists**:
- Max 50 items per user
- Symbol: Must match yfinance format (uppercase, optional `.KS` or `.KQ` suffix)

**portfolios**:
- Exactly 3 portfolios per user
- Name: Must be one of `["장기투자", "단기투자", "정찰병"]`

**holdings**:
- Max 100 items per portfolio
- Quantity: Positive decimal, max 4 decimal places
- Avg_price: Positive decimal, max 4 decimal places

**stock_quotes**:
- Symbol: Must exist in either watchlists or holdings
- Market: Auto-detected from symbol suffix (`.KS`/`.KQ` → KR, else → US)

---

## Database Migrations

### Migration Tool: Alembic

**Directory Structure**:
```
backend/src/db/migrations/
├── env.py
├── script.py.mako
└── versions/
    ├── 001_create_users_table.py
    ├── 002_create_watchlists_table.py
    ├── 003_create_portfolios_table.py
    ├── 004_create_holdings_table.py
    ├── 005_create_stock_quotes_table.py
    └── 006_create_candlestick_data_table.py
```

**Sample Migration**:
```python
# 001_create_users_table.py
def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.TIMESTAMP, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='1'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

def downgrade():
    op.drop_table('users')
```

---

## Sample Data for Testing

### Test Users with Portfolios
```sql
-- Create test user
INSERT INTO users (email, password_hash) VALUES
('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztP7IqZpKYXW');
-- Password: TestPass123

-- Portfolios auto-created by trigger

-- Add watchlist items
INSERT INTO watchlists (user_id, symbol, display_order) VALUES
(1, 'AAPL', 0),
(1, 'MSFT', 1),
(1, '005930.KS', 2);

-- Add holdings to "장기투자" portfolio
INSERT INTO holdings (portfolio_id, symbol, quantity, avg_price) VALUES
(1, 'AAPL', 10.0000, 150.0000),
(1, '005930.KS', 5.0000, 70000.0000);

-- Add cached stock quotes
INSERT INTO stock_quotes (symbol, current_price, daily_change_pct, volume, market_status, market) VALUES
('AAPL', 175.43, 1.25, 54321000, 'closed', 'US'),
('MSFT', 380.12, -0.45, 23456000, 'closed', 'US'),
('005930.KS', 71500.00, -0.69, 12345678, 'open', 'KR');
```

---

## Backup and Recovery

### Backup Strategy

**Automated Backups** (Azure MySQL):
- Daily automated backups (retained 7 days)
- Point-in-time restore (within 7-day window)
- Geo-redundant backup storage (optional)

**Manual Backup**:
```bash
# Export entire database
mysqldump -h mystock-mysql.mysql.database.azure.com \
  -u admin -p \
  mystockdb > backup_$(date +%Y%m%d).sql

# Restore from backup
mysql -h mystock-mysql.mysql.database.azure.com \
  -u admin -p \
  mystockdb < backup_20251021.sql
```

---

## Next Steps

1. ✅ Data model complete
2. → Generate API contracts in `contracts/api.yaml`
3. → Create `quickstart.md` for local development
4. → Update agent context with database schema

---

**Data Model Complete**: All tables defined with indexes, constraints, sample data, and migration plan. Schema supports all functional requirements from spec.md.
