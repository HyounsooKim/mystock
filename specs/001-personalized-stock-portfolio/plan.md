# Implementation Plan: Personalized Stock Portfolio App

**Branch**: `001-personalized-stock-portfolio` | **Date**: 2025-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-personalized-stock-portfolio/spec.md`

**Status**: Phase 2 Ready ✅  
**Phase 0 Research**: [research.md](./research.md) ✅  
**Phase 1 Design**: [data-model.md](./data-model.md) | [contracts/api.yaml](./contracts/api.yaml) | [quickstart.md](./quickstart.md) ✅  
**Phase 2 Tasks**: [tasks.md](./tasks.md) ✅ (19 tasks: 2 infra, 5 backend, 5 frontend, 2 testing, 1 deploy, 4 docs)  
**Agent Context**: Updated via `.specify/scripts/bash/update-agent-context.sh copilot` ✅

## Overview

개인화된 주식 포트폴리오 앱으로, 사용자가 한국(KOSPI/KOSDAQ)과 미국(NYSE/NASDAQ) 주식을 워치리스트에 추가하고, 실시간 시세를 조회하며, 3개의 미리 정의된 포트폴리오("장기투자", "단기투자", "정찰병")에서 보유 종목을 관리할 수 있습니다. yfinance API를 통해 시세 데이터를 수집하고 5분간 캐싱하여 API 호출을 최소화합니다. Azure 클라우드 인프라를 100% 활용하며, Vue3 프론트엔드는 Blob Storage에 정적 배포하고, FastAPI 백엔드는 Container Apps에 배포하며, Azure MySQL을 사용합니다.

## Technology Choices

## Technical Context

**Language/Version**: Python 3.11 (backend), Node.js 20+ (frontend build)  
**Primary Dependencies**: 
- Backend: FastAPI, yfinance, SQLAlchemy, PyMySQL, uvicorn
- Frontend: Vue 3, Tabler Dashboard, ECharts, Vite
- Infrastructure: Azure CLI, Bicep/Terraform

**Storage**: Azure MySQL 8.0 (Standard_B2s for production, local MySQL 8.0 for testing)  
**Testing**: pytest (backend), Vitest (frontend), MySQL container for integration tests  
**Target Platform**: Azure Container Apps (backend), Azure Blob Storage (frontend static site)  
**Project Type**: Web application (frontend + backend + infrastructure)  
**Performance Goals**: 
- 95% of quote requests < 1s response time
- Watchlist load < 3s
- Portfolio operations < 2min end-to-end
- Cache hit ratio > 80% for repeated ticker queries

**Constraints**: 
- Local operations < 200ms response time
- yfinance API: max 1 request per 5min per ticker (enforced by cache)
- Azure MySQL connection pooling: max 50 connections
- Frontend bundle size < 2MB (excluding charts)

**Scale/Scope**: 
- Initial target: 100 concurrent users
- Watchlist: 50 items per user
- Portfolio holdings: 100 items per portfolio (3 portfolios per user)
- Chart data: 5 period options (30m-2d, 1h-1wk, 1d-6m, 1wk-2y, 1mo-7y)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Code Quality ✅
- Python backend: Type hints required, docstrings for all public functions
- Vue3 frontend: Composition API with TypeScript, component-level documentation
- Infrastructure: Bicep/Terraform with inline comments for resource purpose
- **Compliance**: All code will follow linting (ruff for Python, ESLint for Vue)

### II. Testing Discipline ✅
- yfinance API calls: Mocked in unit tests, single live call in integration test
- 5-minute cache strategy enforces rate limit compliance
- Integration tests use local MySQL container, not production
- **Compliance**: pytest-mock for API mocking, Docker Compose for test environment

### III. User Experience ✅
- Response time targets defined: <200ms local, <1s API calls, <3s watchlist load
- Loading states for all async operations (Vue Suspense + skeleton screens)
- Error messages user-friendly (not technical stack traces)
- **Compliance**: Performance budgets in CI, Lighthouse scores > 90

### IV. Performance Optimization ✅
- Minimal dependencies: FastAPI (vs Django), Vue3 (vs React+heavy libs)
- Standard library preferred: Python `dataclasses` vs Pydantic where possible
- Frontend: Lazy-load ECharts only on detail view
- **Compliance**: Dependency review in PR checklist, bundle size monitoring

### V. Deployment Strategy ✅
- Azure-first architecture: Container Apps, Blob Storage, MySQL, Key Vault
- Secrets in Azure Key Vault (DB password, API keys if needed)
- Application Insights for logging and monitoring
- **Compliance**: IaC for all resources, staging environment for testing

**Result**: All constitution principles satisfied. No violations to justify.

## Project Structure

### Documentation (this feature)

```
specs/001-personalized-stock-portfolio/
├── plan.md              # This file
├── research.md          # Phase 0 output (technology decisions)
├── data-model.md        # Phase 1 output (database schema)
├── quickstart.md        # Phase 1 output (local dev setup)
├── contracts/           # Phase 1 output (API contracts)
│   └── api.yaml         # OpenAPI 3.0 specification
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```
infrastructure/
├── bicep/
│   ├── main.bicep              # Azure resources orchestration
│   ├── container-app.bicep     # Backend Container Apps
│   ├── storage.bicep           # Blob Storage for frontend
│   ├── mysql.bicep             # Azure MySQL Flexible Server
│   └── key-vault.bicep         # Secrets management
├── scripts/
│   ├── deploy.sh               # Deployment automation
│   └── provision-db.sh         # Database initialization
└── terraform/                  # Alternative IaC (if preferred over Bicep)

backend/
├── src/
│   ├── main.py                 # FastAPI app entry
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── watchlist.py
│   │   ├── portfolio.py
│   │   └── stock_quote.py
│   ├── services/               # Business logic
│   │   ├── auth.py             # Email/password authentication
│   │   ├── stock.py            # yfinance integration + caching
│   │   ├── watchlist.py        # Watchlist CRUD
│   │   └── portfolio.py        # Portfolio CRUD + aggregations
│   ├── api/                    # FastAPI routes
│   │   ├── auth.py
│   │   ├── watchlist.py
│   │   ├── stock.py
│   │   └── portfolio.py
│   ├── db/                     # Database utilities
│   │   ├── connection.py       # MySQL connection pool
│   │   └── migrations/         # Alembic migrations
│   ├── cache/                  # Redis-like simple cache (5min TTL)
│   │   └── stock_cache.py
│   └── config.py               # Azure Key Vault integration
├── tests/
│   ├── unit/                   # Mocked unit tests
│   ├── integration/            # With MySQL container
│   └── conftest.py             # Pytest fixtures
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── Dockerfile                  # Container image for Azure Container Apps
└── docker-compose.yml          # Local development environment

frontend/
├── src/
│   ├── main.ts                 # Vue3 app entry
│   ├── components/             # Reusable UI components
│   │   ├── WatchlistCard.vue   # Stock card display
│   │   ├── ChartTabs.vue       # Period selection tabs
│   │   ├── PortfolioSummary.vue # Aggregated portfolio view
│   │   └── StockChart.vue      # ECharts candlestick chart
│   ├── views/                  # Page-level components
│   │   ├── LoginView.vue
│   │   ├── WatchlistView.vue
│   │   ├── StockDetailView.vue
│   │   └── PortfolioView.vue
│   ├── services/               # API client
│   │   ├── api.ts              # Axios instance with auth
│   │   ├── auth.service.ts
│   │   ├── watchlist.service.ts
│   │   ├── stock.service.ts
│   │   └── portfolio.service.ts
│   ├── router/                 # Vue Router
│   │   └── index.ts
│   ├── stores/                 # Pinia state management
│   │   ├── auth.ts
│   │   ├── watchlist.ts
│   │   └── portfolio.ts
│   └── assets/                 # Tabler theme customization
├── tests/
│   └── unit/                   # Vitest component tests
├── public/                     # Static assets
├── package.json
├── vite.config.ts              # Vite build configuration
├── tsconfig.json
└── .env.example                # Environment variables template

database/
├── schema/
│   ├── 001_users.sql           # User table
│   ├── 002_watchlists.sql      # Watchlist tables
│   ├── 003_portfolios.sql      # Portfolio + holdings tables
│   └── 004_stock_cache.sql     # Cached stock quotes
└── seeds/
    └── initial_portfolios.sql  # Pre-populate 3 portfolio types per user

.github/
└── workflows/
    ├── backend-ci.yml          # Backend tests + Docker build
    ├── frontend-ci.yml         # Frontend tests + build
    └── deploy-azure.yml        # Deploy to Azure (staging + prod)

.venv/                          # Python virtual environment (gitignored)
node_modules/                   # NPM packages (gitignored)
```

**Structure Decision**: Web application structure (Option 2) with separate `infrastructure/`, `backend/`, `frontend/`, and `database/` directories. This separation aligns with Azure deployment model (Container Apps for backend, Blob Storage for frontend, managed MySQL for database) and supports independent CI/CD pipelines. The `infrastructure/` directory contains IaC (Bicep preferred, Terraform as alternative) for reproducible Azure resource provisioning.

## Complexity Tracking

*No violations detected. All constitution principles are satisfied by the chosen architecture.*

