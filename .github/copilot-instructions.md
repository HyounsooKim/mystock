# MyStock Development Guidelines

Auto-generated from project analysis. Last updated: 2025-10-25

## Project Overview
**MyStock**: Personalized Stock Portfolio Management Application supporting US markets (NYSE/NASDAQ).
- **Demo**: https://stock.hemtory.com/
- **Repository**: HyounsooKim/mystock
- **Status**: Production (deployed on Azure)

## Active Technologies

### Backend
- **Runtime**: Python 3.11
- **Framework**: FastAPI 0.104.1 with Uvicorn 0.24.0
- **Database**: Azure Cosmos DB (NoSQL)
- **Authentication**: JWT with python-jose, passlib/bcrypt
- **Stock Data API**: Alpha Vantage
- **Deployment**: Azure Container Apps (Korea Central)

### Frontend
- **Runtime**: Node.js 20+
- **Framework**: Vue 3.3.8 with Composition API
- **State Management**: Pinia 2.1.7
- **Routing**: Vue Router 4.2.5
- **UI Library**: Tabler Core 1.0.0-beta20
- **Charts**: ECharts 5.4.3
- **HTTP Client**: Axios 1.6.0
- **Build Tool**: Vite 5.0.0
- **Deployment**: Azure Static Web Apps (East Asia)

### Infrastructure
- **IaC**: Azure Bicep
- **CI/CD**: GitHub Actions
- **Monitoring**: Azure Log Analytics + Application Insights

## Project Structure
```
mystock/
├── backend/
│   ├── src/
│   │   ├── api/              # API endpoints (auth, portfolios, stocks, watchlist, health)
│   │   ├── core/             # Config, database, middleware, security
│   │   ├── models/           # Pydantic models (User)
│   │   ├── schemas/          # Request/Response schemas
│   │   ├── services/         # Business logic (Alpha Vantage, stock data)
│   │   ├── db/               # Database utilities (seed)
│   │   ├── alembic/          # Database migrations
│   │   └── main.py           # FastAPI application entry point
│   ├── tests/                # Unit & integration tests
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Container image
├── frontend/
│   ├── src/
│   │   ├── api/              # HTTP client configuration
│   │   ├── components/       # Vue components
│   │   │   ├── layout/       # AppLayout
│   │   │   ├── portfolio/    # PortfolioTreemap
│   │   │   └── stocks/       # TopMoversList
│   │   ├── stores/           # Pinia stores (auth, portfolio, watchlist, topMovers)
│   │   ├── views/            # Page views (Login, Register, Watchlist, Portfolio, StockDetail, TopMovers)
│   │   ├── router/           # Vue Router configuration
│   │   ├── App.vue           # Root component
│   │   └── main.js           # Application entry point
│   ├── public/               # Static assets
│   │   └── staticwebapp.config.json  # Azure SWA configuration
│   ├── tests/                # Vitest unit tests & Playwright e2e tests
│   ├── package.json          # npm dependencies
│   └── vite.config.js        # Vite build configuration
├── infra/
│   ├── main.bicep            # Main infrastructure template
│   └── modules/              # Bicep modules (containerapps, cosmosdb, staticwebapp, monitoring)
├── specs/
│   └── 001-personalized-stock-portfolio/  # Feature specifications
├── .github/
│   └── workflows/            # CI/CD pipelines
└── README.md

```

## Core Features

### 1. User Authentication (P1)
- Email/password registration and login
- JWT-based authentication
- User profile management
- Account deletion

### 2. Watchlist Management (P1)
- Add/remove stocks (max 50 items)
- Drag-and-drop reordering
- Real-time price updates
- Stock search by symbol
- Notes per stock item
- Sparkline charts

### 3. Stock Details (P1)
- Real-time quote (current price, change %, volume)
- Candlestick charts with 5 timeframes:
  - 30min-2days (intraday 30m)
  - 1hour-1week (intraday 1h)
  - 1day-6months (daily)
  - 1week-2years (weekly)
  - 1month-7years (monthly)
- Market status (open/closed)
- Company information

### 4. Portfolio Management (P2)
- 3 predefined portfolios: "장기투자", "단기투자", "정찰병"
- Add/edit/delete holdings (symbol, quantity, avg price required)
- Real-time portfolio valuation
- Profit/loss calculation
- Return rate percentage
- Treemap visualization

### 5. Top Movers (P2)
- Top gainers
- Top losers
- Most actively traded stocks

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `GET /me` - Get current user profile
- `DELETE /me` - Delete account

### Watchlist (`/api/v1/watchlist`)
- `GET /` - Get user's watchlist
- `POST /` - Add stock to watchlist
- `PUT /{symbol}` - Update watchlist item notes
- `DELETE /{symbol}` - Remove from watchlist
- `PUT /reorder` - Reorder watchlist items

### Portfolios (`/api/v1/portfolios`)
- `GET /` - List user's portfolios
- `GET /{portfolio_id}` - Get portfolio details
- `GET /{portfolio_id}/summary` - Get portfolio summary (total value, P&L)
- `POST /{portfolio_id}/holdings` - Add holding
- `PUT /{portfolio_id}/holdings/{holding_id}` - Update holding
- `DELETE /{portfolio_id}/holdings/{holding_id}` - Delete holding

### Stocks (`/api/v1/stocks`)
- `GET /top-movers` - Get top gainers/losers/active
- `GET /{symbol}` - Get stock quote
- `GET /{symbol}/chart` - Get candlestick chart data
- `GET /{symbol}/news` - Get stock news (placeholder)

### Health (`/api/v1/health`)
- `GET /` - API health check
- `GET /db` - Database health check

## Development Commands

### Backend (from `backend/` directory)
```bash
# Setup
python -m venv .venv
.\.venv\Scripts\activate          # Windows
source .venv/bin/activate         # Linux/Mac
pip install -r requirements.txt

# Development
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Testing
pytest                            # Run all tests
pytest tests/integration/         # Integration tests only
pytest --cov=src tests/           # With coverage

# Code Quality
ruff check .                      # Lint
black .                           # Format
mypy src/                         # Type check
```

### Frontend (from `frontend/` directory)
```bash
# Setup
npm install

# Development
npm run dev                       # Dev server (localhost:5173)
npm run build                     # Production build
npm run preview                   # Preview production build

# Testing
npm run test                      # Vitest unit tests
npm run test:coverage             # With coverage
npm run test:e2e                  # Playwright e2e tests
npm run test:e2e:ui               # Playwright UI mode

# Code Quality
npm run lint                      # ESLint
npm run format                    # Prettier
```

### Infrastructure (from `infra/` directory)
```bash
# Deploy to Azure
az deployment group create \
  --resource-group rg-mystock-dev \
  --template-file main.bicep \
  --parameters appName=mystock environmentName=dev

# Validate Bicep
az bicep build --file main.bicep
```

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8 conventions
- Use type hints for all function signatures
- Use Pydantic models for data validation
- Use async/await for I/O operations
- Docstrings: Google style for modules/classes/functions
- Error handling: Raise HTTPException with appropriate status codes
- Logging: Use logger with INFO/WARNING/ERROR levels

### JavaScript/Vue (Frontend)
- Use Vue 3 Composition API (`<script setup>`)
- Use Pinia for state management
- Use async/await for API calls
- Use template refs for DOM access
- Component naming: PascalCase for files, kebab-case in templates
- Props: Define with TypeScript-style type annotations
- Events: Use `defineEmits` for custom events

### Bicep (Infrastructure)
- Use parameters for configurable values
- Add comments for resource purposes
- Use outputs for cross-module references
- Follow Azure naming conventions

## Environment Variables

### Backend (.env)
```bash
# Cosmos DB
COSMOS_ENDPOINT=https://xxx.documents.azure.com:443/
COSMOS_KEY=<primary-key>
COSMOS_DATABASE_NAME=mystock
COSMOS_CONTAINER_NAME=users

# Alpha Vantage
ALPHA_VANTAGE_API_KEY=<your-api-key>
ALPHA_VANTAGE_USE_DELAYED=true

# JWT
JWT_SECRET_KEY=<random-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Testing Strategy

### Backend
- **Unit Tests**: Business logic in services
- **Integration Tests**: API endpoints with test database
- **Test Coverage Target**: 70%+
- **Tools**: pytest, pytest-asyncio, pytest-cov

### Frontend
- **Unit Tests**: Component logic and stores
- **E2E Tests**: User flows (auth, watchlist, portfolio)
- **Tools**: Vitest, Playwright
- **E2E Scenarios**: Login → Add to watchlist → View chart → Logout

## Deployment

### Backend
- **Platform**: Azure Container Apps (Consumption plan)
- **Region**: Korea Central
- **Auto-scaling**: 0-2 replicas
- **CI/CD**: GitHub Actions → Azure Container Registry → Container Apps

### Frontend
- **Platform**: Azure Static Web Apps (Free tier)
- **Region**: East Asia
- **CI/CD**: GitHub Actions → Static Web Apps
- **CDN**: Built-in with SWA

## Recent Changes
- 2025-10-25: Fixed candlestick chart tooltip data indexing (commit a72e362)
- 2025-10-24: Added Top Movers feature with gainers/losers/most active stocks
- 2025-10-24: Removed debug logging from production code
- 2025-10-24: Fixed candlestick chart tooltip data mapping (ECharts index offset issue)
- 2025-10-23: Deployed to Azure with Container Apps + Static Web Apps

## Known Issues & TODOs
- [ ] Market cap data not cached (reduce API calls)
- [ ] News endpoint returns placeholder data
- [ ] Support Korean stock markets (KOSPI/KOSDAQ)
- [ ] Add stock search autocomplete
- [ ] Implement data caching strategy

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
