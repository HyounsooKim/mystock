# MyStock - Personalized Stock Portfolio App

개인화된 주식 포트폴리오 관리 애플리케이션으로, 한국(KOSPI/KOSDAQ)과 미국(NYSE/NASDAQ) 주식 시장을 지원합니다.

## Features

- **워치리스트 관리**: 관심 주식 종목 추가/삭제 및 실시간 시세 확인
- **주식 상세 정보**: 현재가, 변동률, 거래량, 캔들스틱 차트 (5가지 기간 옵션)
- **포트폴리오 관리**: 3개의 포트폴리오("장기투자", "단타", "정찰병")에서 보유 종목 관리
- **손익 분석**: 실시간 평가액, 손익률, 수익률 계산

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: Azure MySQL 8.0 (로컬: MySQL 8.0 in Docker)
- **ORM**: SQLAlchemy with Alembic migrations
- **Stock Data**: yfinance API
- **Authentication**: JWT with bcrypt
- **Testing**: pytest

### Frontend
- **Framework**: Vue 3 (Composition API)
- **UI Library**: Tabler Dashboard
- **Charts**: ECharts
- **Build Tool**: Vite
- **State Management**: Pinia
- **Testing**: Vitest

### Infrastructure
- **Cloud**: Azure (Container Apps, Blob Storage, MySQL Flexible Server)
- **IaC**: Bicep
- **CI/CD**: GitHub Actions

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20.x LTS
- Docker Desktop
- Git

### 1. Clone Repository

```bash
git clone <repository-url>
cd my_stock
```

### 2. Start Database (Docker)

```bash
# Start MySQL container
docker-compose up -d

# Verify container is running
docker ps | grep mystock-mysql
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run database migrations
cd src
alembic upgrade head

# Seed test data (optional)
python -m db.seed

# Start backend server
cd ..
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`  
Health check at `http://localhost:8000/api/v1/health`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Start dev server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Development

### Backend Commands

```bash
cd backend
source venv/bin/activate

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Lint code
ruff check .

# Format code
black .

# Type check
mypy src

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Frontend Commands

```bash
cd frontend

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Generate coverage
npm run test:coverage

# Lint code
npm run lint

# Format code
npm run format
```

### Database Management

```bash
# Connect to MySQL
docker exec -it mystock-mysql mysql -u mystockuser -pmystockpass123 mystockdb

# Backup database
docker exec mystock-mysql mysqldump -u mystockuser -pmystockpass123 mystockdb > backup.sql

# Restore database
docker exec -i mystock-mysql mysql -u mystockuser -pmystockpass123 mystockdb < backup.sql

# View logs
docker logs mystock-mysql

# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Project Structure

```
my_stock/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── db/             # Database migrations
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── frontend/               # Vue 3 frontend
│   ├── src/
│   │   ├── views/          # Page components
│   │   ├── components/     # Reusable components
│   │   ├── stores/         # Pinia stores
│   │   ├── router/         # Vue Router
│   │   └── utils/          # Utilities
│   └── package.json
├── infrastructure/         # Bicep IaC templates
├── database/              # SQL scripts
├── specs/                 # Feature specifications
└── docker-compose.yml     # Local development
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Contract File**: `specs/001-personalized-stock-portfolio/contracts/api.yaml`

### Available Endpoints

#### Health Check
- `GET /api/v1/health` - Application health status
- `GET /api/v1/health/db` - Database health check

#### Authentication
- `POST /api/v1/auth/register` - Register new user account
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user profile (requires auth)
- `DELETE /api/v1/auth/me` - Deactivate account (requires auth)

#### Watchlist
- `GET /api/v1/watchlist` - List user's watchlist (requires auth)
- `POST /api/v1/watchlist` - Add stock to watchlist (requires auth)
- `PUT /api/v1/watchlist/{symbol}` - Update watchlist item notes (requires auth)
- `DELETE /api/v1/watchlist/{symbol}` - Remove from watchlist (requires auth)
- `PUT /api/v1/watchlist/reorder` - Reorder watchlist items (requires auth)

#### Stocks (Coming soon)
- `GET /api/v1/stocks/{symbol}` - Get stock quote
- `GET /api/v1/stocks/{symbol}/chart` - Get chart data

#### Portfolios (Coming soon)
- `GET /api/v1/portfolios` - List user's portfolios
- `POST /api/v1/portfolios/{id}/holdings` - Add holding
- `GET /api/v1/portfolios/{id}/summary` - Portfolio summary

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=src --cov-report=term --cov-report=html

# Run integration tests
pytest tests/integration/
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm run test

# Run with UI
npm run test:ui

# Generate coverage
npm run test:coverage
```

### End-to-End Tests

```bash
# Coming soon: Cypress/Playwright tests
```

## Documentation

- **Feature Spec**: `specs/001-personalized-stock-portfolio/spec.md`
- **Implementation Plan**: `specs/001-personalized-stock-portfolio/plan.md`
- **Data Model**: `specs/001-personalized-stock-portfolio/data-model.md`
- **API Contracts**: `specs/001-personalized-stock-portfolio/contracts/api.yaml`
- **Quickstart Guide**: `specs/001-personalized-stock-portfolio/quickstart.md`
- **Research**: `specs/001-personalized-stock-portfolio/research.md`
- **Tasks**: `specs/001-personalized-stock-portfolio/tasks.md`

## Environment Variables

### Backend (.env)

```bash
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/mystockdb
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
STOCK_CACHE_TTL_SECONDS=300
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (.env.local)

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_ENABLE_MOCK_API=false
```

## Performance Targets

- **Local Operations**: <200ms response time
- **Cached Stock Quotes**: <1s response (95% of requests)
- **Watchlist Load**: <3s for 50 items
- **Portfolio Operations**: <2min end-to-end
- **Cache Hit Ratio**: >80% for repeated ticker queries

## Contributing

1. Create feature branch from `main`
2. Follow code quality guidelines (linting, type hints, docstrings)
3. Write tests (>80% coverage)
4. Update documentation
5. Submit pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please create an issue in the repository.
