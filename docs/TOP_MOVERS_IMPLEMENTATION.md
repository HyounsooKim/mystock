# Top Movers Feature Implementation

This document describes the implementation of the "급등락 종목들" (Top Movers) feature for the MyStock application.

## Overview

The Top Movers feature displays real-time market movers from the US stock market, showing three categorized lists:
- **Top Gainers** (상승 상위): Stocks with the highest percentage gains
- **Top Losers** (하락 상위): Stocks with the highest percentage losses  
- **Most Active** (거래량 상위): Stocks with the highest trading volume

## Implementation Summary

### Backend Changes

#### 1. Schemas (`backend/src/schemas/stocks.py`)
- Added `StockMoverItem` schema for individual stock items
- Added `TopMoversResponse` schema for the API response

#### 2. Services
- **`backend/src/services/alpha_vantage_service.py`**
  - Added `get_top_movers()` method to fetch data from Alpha Vantage API
  - Includes error handling for API failures, timeouts, and rate limits
  
- **`backend/src/services/top_movers_service.py`** (new file)
  - Implements caching layer with 4-hour TTL
  - Handles stale cache fallback on API errors
  - Provides singleton instance for consistent cache across requests

#### 3. API Endpoint (`backend/src/api/stocks.py`)
- Added `GET /api/v1/stocks/top-movers` endpoint
- **Important**: Route defined BEFORE `/{symbol}` to avoid path conflicts
- Returns 503 on API failures, 500 on internal errors
- Includes proper logging and error handling

#### 4. Tests (`backend/tests/test_top_movers.py`)
- Unit tests for successful data retrieval
- Tests for API failure handling
- Mock-based testing using sample data

### Frontend Changes

#### 1. Router (`frontend/src/router/index.js`)
- Added `/top-movers` route
- Configured with authentication requirement
- Set page title to "급등락 종목들"

#### 2. Navigation (`frontend/src/components/layout/AppLayout.vue`)
- Added "급등락 종목들" menu item with trending-up icon
- Positioned after "포트폴리오" as specified
- Added `fullWidth` prop support for full-width layouts

#### 3. Store (`frontend/src/stores/topMovers.js`)
- Pinia store for state management
- Tracks: data, loading state, errors, last update time
- Getters: `hasData`, `isStale`, `topGainers`, `topLosers`, `mostActive`
- Actions: `fetchTopMovers()`, `refreshTopMovers()`, `clearError()`
- 15-minute staleness check

#### 4. Components

**`frontend/src/components/stocks/TopMoversList.vue`**
- Reusable list component for displaying stock data
- Props: `stocks`, `type`, `title`, `maxItems`
- Features:
  - Color-coded headers (red for gainers, blue for losers, gray for active)
  - Formatted numbers (prices, percentages, volumes)
  - Click-to-navigate to stock detail pages
  - Hover effects for better UX
  - Responsive table design

**`frontend/src/views/TopMoversView.vue`**
- Main view component
- Three-column layout on desktop (responsive grid)
- Features:
  - Loading spinner during data fetch
  - Error alert with dismiss button
  - Empty state with retry button
  - Floating refresh button
  - Last updated timestamp display
  - Automatic data refresh on stale data

#### 5. E2E Tests (`frontend/tests/e2e/top-movers.spec.ts`)
- Navigation test
- Three lists display test
- Stock detail navigation test
- Mobile responsive test
- Error handling test
- Loading state test
- Refresh functionality test
- Number formatting test

## File Structure

```
backend/
├── src/
│   ├── api/
│   │   └── stocks.py (modified - added /top-movers endpoint)
│   ├── schemas/
│   │   └── stocks.py (modified - added TopMovers schemas)
│   └── services/
│       ├── alpha_vantage_service.py (modified - added get_top_movers)
│       └── top_movers_service.py (new - caching layer)
└── tests/
    └── test_top_movers.py (new)

frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   └── AppLayout.vue (modified - added menu item)
│   │   └── stocks/
│   │       └── TopMoversList.vue (new)
│   ├── router/
│   │   └── index.js (modified - added route)
│   ├── stores/
│   │   └── topMovers.js (new)
│   └── views/
│       └── TopMoversView.vue (new)
└── tests/
    └── e2e/
        └── top-movers.spec.ts (new)

scripts/
└── test_top_movers.py (new - integration test script)
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/test_top_movers.py -v
```

### Frontend Build
```bash
cd frontend
npm run build
```

### E2E Tests (requires running servers)
```bash
cd frontend
npm run test:e2e
```

### Manual Integration Test
```bash
python scripts/test_top_movers.py
```

## Configuration

### Backend Environment Variables
```env
ALPHA_VANTAGE_API_KEY=your-api-key
STOCK_CACHE_TTL_SECONDS=300
```

## Known Limitations

1. **Alpha Vantage Rate Limits**: Free tier limited to 25 calls/day for this endpoint
2. **Data Freshness**: Data typically updates once per trading day
3. **Cache Duration**: 4-hour cache means data may be slightly stale
4. **Network Dependency**: Requires internet access to fetch data
