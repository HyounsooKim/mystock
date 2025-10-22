# Research: Personalized Stock Portfolio App

**Feature**: 001-personalized-stock-portfolio  
**Date**: 2025-10-21  
**Phase**: 0 (Outline & Research)

## Overview

This document captures technology decisions, best practices, and architectural patterns researched for the Personalized Stock Portfolio application.

---

## Technology Stack Decisions

### Backend Framework: FastAPI

**Decision**: Use FastAPI as the backend web framework

**Rationale**:
- Modern async Python framework with automatic OpenAPI documentation
- Native async/await support for concurrent yfinance API calls
- Minimal dependencies align with Constitution Principle IV (Performance Optimization)
- Built-in data validation with Pydantic reduces boilerplate
- Excellent Azure Container Apps compatibility

**Alternatives Considered**:
- Django: Too heavy for simple REST API, includes ORM/admin we don't need
- Flask: Lacks native async support, requires more middleware setup
- Node.js/Express: Would require separate language from data processing

**Best Practices**:
- Use dependency injection for database sessions and services
- Implement API versioning from the start (`/api/v1/`)
- Apply rate limiting middleware for external API calls
- Use background tasks for non-blocking cache updates

---

### Frontend Framework: Vue 3 + Tabler + ECharts

**Decision**: Use Vue 3 (Composition API) with Tabler Dashboard theme and ECharts for charting

**Rationale**:
- Vue 3 Composition API provides excellent TypeScript support
- Tabler offers ready-made dashboard components reducing custom CSS
- ECharts handles complex financial charts (candlestick) with high performance
- Smaller bundle size than React+Material-UI alternatives (Principle IV)
- Native lazy loading for charts aligns with performance goals

**Alternatives Considered**:
- React: Larger ecosystem but heavier bundle, more dependencies
- Svelte: Great performance but smaller community, fewer dashboard templates
- Angular: Too complex for this scale, violates simplicity principle

**Best Practices**:
- Use Vite for build tooling (faster than Webpack)
- Implement route-based code splitting
- Lazy-load ECharts only on stock detail view
- Use Pinia for state management (Vue 3 recommended over Vuex)
- Implement skeleton screens for loading states (UX Principle III)

---

### Database: Azure MySQL 8.0

**Decision**: Azure MySQL Flexible Server 8.0 (Standard_B2s for production)

**Rationale**:
- Managed service reduces operational overhead
- Standard_B2s provides 2 vCPU, 4 GiB RAM suitable for 100 concurrent users
- Built-in automated backups and point-in-time restore
- Azure integration with Key Vault, Virtual Network, Application Insights
- MySQL 8.0 JSON column support for flexible schema (e.g., chart cache)

**Alternatives Considered**:
- PostgreSQL: More features but no clear advantage for this use case
- Azure SQL Database: More expensive, T-SQL vs MySQL syntax
- CosmosDB: Overkill for relational data, higher cost

**Best Practices**:
- Use connection pooling (SQLAlchemy with PyMySQL)
- Index on user_id, symbol, created_at for query performance
- Implement soft deletes for portfolios and watchlists
- Use read replicas if read load exceeds 80% capacity
- Enable slow query log in Application Insights

---

### Stock Data API: yfinance

**Decision**: Use yfinance library to access Yahoo Finance data

**Rationale**:
- Supports both Korean (.KS, .KQ suffix) and US markets
- Free tier sufficient for MVP (100 users * 50 watchlist items = ~5k tickers)
- Returns OHLCV data compatible with ECharts candlestick format
- Simple Python API with built-in caching options
- Active community maintenance

**Alternatives Considered**:
- Alpha Vantage: 5 API calls/min free tier too restrictive
- IEX Cloud: US-only, no Korean market support
- Polygon.io: Paid tier required for real-time data

**Best Practices**:
- Implement 5-minute cache in MySQL (StockQuote table) to minimize API calls
- Use yfinance `download()` method for bulk chart data
- Set timeout=10s on all yfinance calls to prevent hanging
- Mock yfinance in tests (Principle II: Testing Discipline)
- Log all API failures to Application Insights for rate limit monitoring

**API Call Strategy**:
```python
# Cache check before API call
if cache_age < 5 minutes:
    return cached_data
else:
    data = yf.Ticker(symbol).info
    update_cache(symbol, data, ttl=300)  # 5 min TTL
    return data
```

---

### Authentication: Email/Password

**Decision**: Custom email/password authentication with bcrypt hashing

**Rationale**:
- Spec explicitly requires email/password only (no social login)
- Simple to implement with FastAPI security utilities
- Aligns with Principle IV (minimal dependencies)
- Azure Key Vault stores JWT secret key

**Alternatives Considered**:
- Azure AD B2C: Overkill for MVP, adds complexity
- Supabase Auth: External dependency, potential vendor lock-in
- OAuth2 social providers: Not required per spec clarification

**Best Practices**:
- Use bcrypt with cost factor 12 for password hashing
- Implement JWT tokens with 24-hour expiration
- Store refresh tokens in HTTPOnly cookies
- Rate limit login attempts (5 per 15 min per IP)
- Log authentication failures to Application Insights

---

### Azure Infrastructure: Container Apps + Blob Storage

**Decision**: Deploy backend to Azure Container Apps, frontend to Blob Storage static website

**Rationale**:
- Container Apps auto-scales 0-10 instances based on HTTP traffic
- Blob Storage static website is cost-effective (~$0.02/GB/month)
- Azure CDN can be added later for frontend performance
- Simplified deployment with Docker containers (Principle V)
- Integrated Application Insights for monitoring

**Alternatives Considered**:
- App Service: More expensive than Container Apps for intermittent traffic
- Azure Functions: Not ideal for FastAPI, cold start issues
- VM-based deployment: More operational overhead

**Best Practices**:
- Use Bicep for infrastructure as code
- Implement blue-green deployment slots
- Configure auto-scaling rules: 1-5 instances, CPU threshold 70%
- Use Azure Key Vault for secrets (DB password, JWT secret)
- Enable Application Insights distributed tracing

---

### Caching Strategy: In-Database with TTL

**Decision**: Store stock quotes in MySQL with 5-minute TTL instead of Redis

**Rationale**:
- Simplifies architecture (one less service to manage)
- MySQL indexed queries fast enough for cache lookups (<10ms)
- Aligns with Principle IV (minimal dependencies)
- TTL managed via `updated_at` timestamp comparison

**Alternatives Considered**:
- Redis: Adds operational complexity, cost, and deployment overhead
- In-memory (FastAPI app): Lost on container restart, no shared cache across instances
- Azure Cache for Redis: $55/month minimum, overkill for MVP

**Implementation**:
```sql
-- StockQuote table with TTL check
SELECT * FROM stock_quotes
WHERE symbol = ? AND updated_at > NOW() - INTERVAL 5 MINUTE;
```

---

### Testing Strategy

**Decision**: pytest for backend, Vitest for frontend, Docker Compose for integration tests

**Rationale**:
- pytest: Industry standard for Python, excellent FastAPI support
- Vitest: Fast, native ESM support, Vue 3 recommended
- Docker Compose: Runs local MySQL 8.0 container for integration tests
- Aligns with Principle II (Testing Discipline)

**Best Practices**:
- Mock yfinance in unit tests (pytest-mock)
- Single live API call in integration test to verify connectivity
- Use factory pattern for test data (factory_boy)
- Run tests in GitHub Actions on every PR
- Measure test coverage, maintain >80%

---

### Deployment Pipeline

**Decision**: GitHub Actions with separate workflows for backend, frontend, infrastructure

**Rationale**:
- Separate workflows allow independent deployment
- Backend: Docker build → push to Azure Container Registry → deploy to Container Apps
- Frontend: Vite build → upload to Blob Storage
- Infrastructure: Bicep validation → deploy to Azure

**Best Practices**:
- Use GitHub Secrets for Azure credentials
- Implement staging environment for testing before production
- Require PR approval for production deployments
- Tag releases with semantic versioning
- Rollback procedure: revert to previous Docker image tag

---

## Architecture Patterns

### Layered Architecture

```
[Vue3 Frontend] → [FastAPI Backend] → [MySQL Database]
                ↓
            [yfinance API]
```

**Layers**:
1. **Presentation (Frontend)**: Vue 3 components, Tabler UI, ECharts
2. **API (Backend)**: FastAPI routes, request validation, authentication
3. **Business Logic (Backend)**: Services for auth, watchlist, portfolio, stock data
4. **Data Access (Backend)**: SQLAlchemy ORM models, database connection pool
5. **External Integration (Backend)**: yfinance client with caching layer
6. **Persistence**: Azure MySQL with indexed queries

**Benefits**:
- Clear separation of concerns
- Easy to test each layer independently
- Aligns with Constitution Principle I (Code Quality)

---

### Repository Pattern (Simplified)

**Decision**: Use lightweight service layer pattern instead of full repository pattern

**Rationale**:
- SQLAlchemy already provides abstraction over database
- Full repository pattern adds unnecessary complexity for CRUD operations
- Service layer handles business logic (e.g., portfolio aggregation)

**Implementation**:
```python
# services/portfolio.py
class PortfolioService:
    def __init__(self, db: Session, stock_service: StockService):
        self.db = db
        self.stock_service = stock_service
    
    def calculate_portfolio_value(self, portfolio_id: int) -> dict:
        """Calculate total value, profit/loss, return rate"""
        holdings = self.db.query(Holding).filter_by(portfolio_id=portfolio_id).all()
        total_value = 0
        total_cost = 0
        
        for holding in holdings:
            current_price = self.stock_service.get_current_price(holding.symbol)
            total_value += current_price * holding.quantity
            total_cost += holding.avg_price * holding.quantity
        
        return {
            "total_value": total_value,
            "profit_loss": total_value - total_cost,
            "return_rate": ((total_value - total_cost) / total_cost) * 100
        }
```

---

### Error Handling Strategy

**Decision**: Use FastAPI exception handlers with user-friendly messages

**Rationale**:
- Aligns with Principle III (User Experience)
- Centralized error handling reduces code duplication
- Application Insights logs technical details for debugging

**Implementation**:
```python
@app.exception_handler(YFinanceError)
async def yfinance_error_handler(request: Request, exc: YFinanceError):
    logger.error(f"yfinance API error: {exc}", extra={"symbol": exc.symbol})
    return JSONResponse(
        status_code=503,
        content={"message": "일시적으로 주식 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요."}
    )
```

---

## Performance Optimization

### Database Query Optimization

**Indexes**:
```sql
CREATE INDEX idx_user_watchlist ON watchlists(user_id);
CREATE INDEX idx_user_portfolio ON portfolios(user_id);
CREATE INDEX idx_portfolio_holdings ON holdings(portfolio_id);
CREATE INDEX idx_stock_cache ON stock_quotes(symbol, updated_at);
```

**Connection Pooling**:
```python
# SQLAlchemy connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600     # Recycle connections every hour
)
```

### Frontend Bundle Optimization

**Code Splitting**:
```typescript
// Lazy-load stock detail view with ECharts
const StockDetailView = () => import('./views/StockDetailView.vue')

const router = createRouter({
  routes: [
    { path: '/stock/:symbol', component: StockDetailView }  // Loaded on demand
  ]
})
```

**Chart Lazy Loading**:
```vue
<script setup lang="ts">
// ECharts loaded only when component mounts
const { ECharts } = await import('echarts')
</script>
```

---

## Security Considerations

### SQL Injection Prevention

**Decision**: Use SQLAlchemy ORM with parameterized queries

**Implementation**:
```python
# Safe: SQLAlchemy automatically parameterizes
watchlist = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()

# Unsafe (never use):
# db.execute(f"SELECT * FROM watchlists WHERE user_id = {user_id}")
```

### CORS Configuration

**Decision**: Restrict CORS to Azure Blob Storage frontend domain

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mystockapp.z13.web.core.windows.net",  # Azure Blob Storage
        "http://localhost:5173"  # Local development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Secrets Management

**Decision**: Azure Key Vault for all secrets

**Secrets**:
- `mysql-password`: Database connection password
- `jwt-secret-key`: JWT token signing key
- `azure-storage-connection-string`: For file uploads if needed

**Access**:
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://mystock-kv.vault.azure.net/", credential=credential)
db_password = client.get_secret("mysql-password").value
```

---

## Monitoring and Observability

### Application Insights Integration

**Metrics to Track**:
- API response times (p50, p95, p99)
- yfinance API call success rate
- Cache hit ratio
- Authentication failure rate
- Database connection pool saturation

**Custom Events**:
```python
from applicationinsights import TelemetryClient

tc = TelemetryClient('<instrumentation-key>')
tc.track_event('stock_quote_cached', {'symbol': symbol, 'cache_age_seconds': cache_age})
tc.flush()
```

### Logging Strategy

**Levels**:
- ERROR: Failed API calls, database errors, authentication failures
- WARN: Cache misses, slow queries (>100ms), rate limit approaching
- INFO: User registration, portfolio creation, successful deployments
- DEBUG: Detailed request/response (development only)

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()
logger.info("portfolio_calculated", user_id=user_id, portfolio_id=portfolio_id, total_value=total_value)
```

---

## Cost Estimation (Azure)

**Monthly Cost Breakdown** (100 concurrent users):

| Resource | SKU | Cost |
|----------|-----|------|
| Container Apps | 1-5 instances (CPU: 0.5, RAM: 1GB) | ~$30 |
| Blob Storage | 10 GB + 100k requests | ~$2 |
| MySQL Flexible Server | Standard_B2s (2 vCPU, 4 GiB) | ~$50 |
| Key Vault | Standard tier | ~$0.30 |
| Application Insights | First 5 GB free | ~$0 |
| **Total** | | **~$82/month** |

**Cost Optimization**:
- Container Apps scales to 0 during idle periods
- Use Azure Reservations for MySQL (up to 63% discount)
- Blob Storage lifecycle policy to archive old data after 90 days

---

## Risks and Mitigations

### Risk 1: yfinance API Rate Limiting

**Mitigation**:
- 5-minute cache reduces API calls by ~80% (estimated)
- Monitor API call frequency in Application Insights
- Fallback to cached data if API fails (SC-007: 80% success rate)

### Risk 2: Database Connection Exhaustion

**Mitigation**:
- SQLAlchemy connection pool (max 30 connections)
- Connection timeout 30s, automatic recycling every hour
- Monitor connection pool saturation metric

### Risk 3: Frontend Bundle Size Exceeds 2MB

**Mitigation**:
- Lazy-load ECharts (saves ~500KB)
- Use Vite tree-shaking and code splitting
- Monitor bundle size in CI pipeline (fail if >2MB)

### Risk 4: Azure MySQL Cold Start Latency

**Mitigation**:
- Enable connection pooling with `pool_pre_ping=True`
- Use read replicas for scaling (if needed)
- Implement query result caching for aggregations

---

## Next Steps (Phase 1)

1. Generate `data-model.md` with complete MySQL schema
2. Create `contracts/api.yaml` OpenAPI specification
3. Generate `quickstart.md` for local development setup
4. Update agent context with technology decisions

---

**Research Complete**: All technical decisions documented with rationale, best practices, and alternatives considered. Ready to proceed to Phase 1 (Design & Contracts).
