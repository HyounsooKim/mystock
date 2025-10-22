# MyStock - Personalized Stock Portfolio App

개인화된 주식 포트폴리오 관리 애플리케이션으로, 한국(KOSPI/KOSDAQ)과 미국(NYSE/NASDAQ) 주식 시장을 지원합니다.  

## Features

- **워치리스트 관리**: 관심 주식 종목 추가/삭제 및 실시간 시세 확인
- **주식 상세 정보**: 현재가, 변동률, 거래량, 캔들스틱 차트 (5가지 기간 옵션)
![주식 관심 종목](./images/01_stock_watchlist.png)  
- **뉴스 피드**: 관련 뉴스 및 공시 정보 제공
![뉴스 피드](./images/02_stock_news.png) 
- **포트폴리오 관리**: 3개의 포트폴리오("장기투자", "단타", "정찰병")에서 보유 종목 관리
- **손익 분석**: 실시간 평가액, 손익률, 수익률 계산
![주식 포트폴리오](./images/03_stock_portfolio.png)  

## ⚠️ 주의사항  
> 아래 가이드 문서는 프로젝트를 로컬 환경에서 설정하고 실행하는 방법을 단계별로 안내합니다.  
Azure(클라우드) 배포시 yfinance API는 동작되지 않을 수 있습니다.  
Container Apps 환경과 NAT 설정을 하더라도 429(too many request) 에러가 발생할 수 있습니다.

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
- **Cloud**: Azure (MySQL Flexible Server, Container Apps, Azure Static Web Apps 배포), shell scripts
- **CI/CD**: GitHub Actions (workflows for backend and frontend)

## Quick Start Guide

이 가이드는 프로젝트를 처음 다운로드하고 로컬 환경에서 실행하는 전체 과정을 단계별로 안내합니다.

### Prerequisites

설치가 필요한 도구들:
- **Python 3.11+** - 백엔드 실행
- **Node.js 20.x LTS** - 프론트엔드 빌드 및 실행
- **MySQL 8.0+** - 데이터베이스 (Docker 또는 직접 설치)
- **Git** - 코드 클론

### Step 1: 프로젝트 클론

```bash
git clone https://github.com/HyounsooKim/mystock.git
cd my_stock
```

### Step 2: MySQL 데이터베이스 설치 및 구동

#### Option A: Docker 사용 (권장)

```bash
# Docker Compose로 MySQL 시작
docker-compose up -d

# MySQL 컨테이너가 정상 실행되는지 확인
docker ps | grep mystock-mysql

# MySQL 로그 확인
docker logs mystock-mysql
```

#### Option B: 로컬 MySQL 직접 사용

```bash
# MySQL 설치 (macOS)
brew install mysql
brew services start mysql

# 데이터베이스 생성
mysql -u root -p
CREATE DATABASE mystockdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mystockuser'@'localhost' IDENTIFIED BY 'mystockpass123';
GRANT ALL PRIVILEGES ON mystockdb.* TO 'mystockuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 3: 백엔드 배포

```bash
cd backend

# 1. Python 가상환경 생성
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
a
# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 DATABASE_URL을 확인/수정:
# DATABASE_URL=mysql+pymysql://mystockuser:mystockpass123@localhost:3306/mystockdb

# 4. 데이터베이스 스키마 생성 (Alembic 마이그레이션)
alembic upgrade head

# 5. MySQL 접속 테스트
# 백엔드에서 DB 연결 확인
python -c "from src.core.database import engine; engine.connect(); print('✅ MySQL 연결 성공')"

# 6. 테스트 데이터 생성 (선택사항)
# python -m db.seed

# 7. 백엔드 서버 시작
cd ..  # backend 디렉토리로 돌아가기
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**백엔드 확인:**
- 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 헬스체크: http://localhost:8000/api/v1/health/health
- DB 헬스체크: http://localhost:8000/api/v1/health/db

터미널을 하나 더 열어서 다음 단계를 진행하세요.

### Step 4: 프론트엔드 배포

새 터미널을 열고:

```bash
cd frontend

# 1. Node 패키지 설치
npm install

# 2. 환경변수 설정
cp .env.example .env.local
# .env.local 파일에서 백엔드 URL 확인:
# VITE_API_BASE_URL=http://localhost:8000/api/v1

# 3. 프론트엔드 개발 서버 시작
npm run dev
```

**프론트엔드 확인:**
- 애플리케이션: http://localhost:5173

### Step 5: 접속 및 사용

1. 브라우저에서 http://localhost:5173 열기
2. **회원가입**: 우측 상단 "Sign up" 클릭하여 계정 생성
3. **로그인**: 생성한 계정으로 로그인
4. **주식 검색**: 상단 검색창에서 종목 검색 (예: "AAPL", "삼성전자")
5. **워치리스트**: 관심 종목을 워치리스트에 추가
6. **포트폴리오**: 보유 종목 관리 및 손익 확인

### Step 6: Playwright 테스트 실행 (선택사항)

E2E 테스트를 통해 전체 기능을 자동으로 검증할 수 있습니다.

```bash
cd frontend

# Playwright 설치 (최초 1회만)
npx playwright install

# 테스트 실행 (백엔드와 프론트엔드가 실행 중이어야 함)
npx playwright test

# UI 모드로 테스트 실행 (브라우저에서 시각적으로 확인)
npx playwright test --ui

# 특정 테스트만 실행
npx playwright test tests/auth.spec.ts

# 테스트 리포트 보기
npx playwright show-report
```

**Playwright 테스트 항목:**
- 회원가입 및 로그인 플로우
- 워치리스트 추가/삭제
- 주식 상세 정보 조회
- 포트폴리오 관리
- 차트 렌더링 검증

## Development

### 일반적인 개발 워크플로우

```bash
# 1. MySQL 시작
docker-compose up -d

# 2. 백엔드 시작 (터미널 1)
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 3. 프론트엔드 시작 (터미널 2)
cd frontend
npm run dev

# 4. 브라우저에서 개발
# http://localhost:5173 접속
```

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

# Run E2E tests (Playwright)
npx playwright test

# Run Playwright tests in UI mode
npx playwright test --ui

# Show Playwright test report
npx playwright show-report
```

## Troubleshooting

### 백엔드가 시작되지 않을 때

**증상**: `uvicorn src.main:app` 실행 시 에러 발생

```bash
# 1. MySQL 연결 확인
docker ps | grep mystock-mysql

# MySQL이 실행 중이 아니면
docker-compose up -d

# 2. 데이터베이스 연결 테스트
cd backend/src
python -c "from db.session import engine; engine.connect(); print('✅ DB 연결 성공')"

# 3. 환경변수 확인
cat backend/.env | grep DATABASE_URL

# 4. 마이그레이션 상태 확인
cd backend/src
alembic current
alembic upgrade head
```

### 프론트엔드가 백엔드에 연결되지 않을 때

**증상**: 로그인 시 네트워크 에러

```bash
# 1. 백엔드 실행 확인
curl http://localhost:8000/api/v1/health

# 2. 환경변수 확인
cat frontend/.env.local | grep VITE_API_BASE_URL

# 올바른 값: VITE_API_BASE_URL=http://localhost:8000/api/v1

# 3. CORS 설정 확인
cat backend/.env | grep CORS_ORIGINS

# http://localhost:5173이 포함되어 있어야 함
```

### Playwright 테스트 실패 시

**증상**: E2E 테스트가 타임아웃 또는 실패

```bash
# 1. 백엔드/프론트엔드 실행 확인
curl http://localhost:8000/api/v1/health
curl http://localhost:5173

# 2. 테스트 데이터베이스 초기화
cd backend/src
alembic downgrade base
alembic upgrade head

# 3. Playwright 브라우저 재설치
cd frontend
npx playwright install --force

# 4. 헤드풀 모드로 디버깅
npx playwright test --headed --debug
```

### MySQL 포트 충돌

**증상**: `docker-compose up` 시 포트 3306 사용 중 에러

```bash
# 1. 3306 포트 사용 프로세스 확인
lsof -i :3306

# 2. 로컬 MySQL 중지 (macOS)
brew services stop mysql

# 또는 docker-compose.yml에서 포트 변경
# "3307:3306" 으로 수정 후 DATABASE_URL도 함께 변경
```

### bcrypt 관련 에러

**증상**: 회원가입 시 bcrypt 에러

```bash
# bcrypt 재설치
cd backend
source .venv/bin/activate
pip uninstall bcrypt
pip install bcrypt==4.0.1
```

## Database Management

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
├── .github/                        # GitHub 설정
│   ├── copilot-instructions.md     # Copilot 가이드라인
│   ├── prompts/                    # AI 프롬프트 템플릿
│   └── workflows/                  # GitHub Actions CI/CD
│       ├── azure-container-app-deploy.yml        # 백엔드 배포
│       └── azure-static-web-apps-*.yml           # 프론트엔드 배포
│
├── backend/                        # FastAPI 백엔드
│   ├── src/
│   │   ├── api/                    # API 라우트
│   │   │   ├── v1/                 # API v1 엔드포인트
│   │   │   │   ├── auth.py         # 인증 (회원가입/로그인)
│   │   │   │   ├── health.py       # 헬스체크
│   │   │   │   ├── portfolios.py   # 포트폴리오 관리
│   │   │   │   ├── stocks.py       # 주식 정보
│   │   │   │   └── watchlist.py    # 워치리스트
│   │   ├── core/                   # 핵심 설정
│   │   │   ├── config.py           # 환경변수 설정
│   │   │   ├── security.py         # JWT/bcrypt 보안
│   │   │   └── dependencies.py     # FastAPI 의존성
│   │   ├── db/                     # 데이터베이스
│   │   │   ├── migrations/         # Alembic 마이그레이션
│   │   │   └── session.py          # DB 세션 관리
│   │   ├── models/                 # SQLAlchemy ORM 모델
│   │   │   ├── user.py             # 사용자 모델
│   │   │   ├── watchlist.py        # 워치리스트 모델
│   │   │   ├── portfolio.py        # 포트폴리오 모델
│   │   │   └── holding.py          # 보유 종목 모델
│   │   ├── schemas/                # Pydantic 스키마 (요청/응답)
│   │   │   ├── user.py             # 사용자 DTO
│   │   │   ├── stock.py            # 주식 DTO
│   │   │   ├── watchlist.py        # 워치리스트 DTO
│   │   │   └── portfolio.py        # 포트폴리오 DTO
│   │   ├── services/               # 비즈니스 로직
│   │   │   ├── stock_service.py    # yfinance 주식 데이터
│   │   │   └── news_service.py     # 뉴스 데이터
│   │   └── main.py                 # FastAPI 앱 진입점
│   ├── tests/                      # 백엔드 테스트
│   │   ├── test_auth.py            # 인증 테스트
│   │   ├── test_watchlist.py       # 워치리스트 테스트
│   │   └── integration/            # 통합 테스트
│   ├── .env.example                # 환경변수 템플릿
│   ├── Dockerfile                  # 컨테이너 이미지
│   ├── alembic.ini                 # Alembic 설정
│   ├── requirements.txt            # Python 의존성
│   └── startup.sh                  # 컨테이너 시작 스크립트
│
├── frontend/                       # Vue 3 프론트엔드
│   ├── src/
│   │   ├── api/                    # API 클라이언트
│   │   │   └── client.js           # Axios 인스턴스
│   │   ├── components/             # 재사용 컴포넌트
│   │   │   ├── StockCard.vue       # 주식 카드
│   │   │   ├── ChartComponent.vue  # ECharts 차트
│   │   │   └── NewsCard.vue        # 뉴스 카드
│   │   ├── views/                  # 페이지 컴포넌트
│   │   │   ├── DashboardView.vue   # 대시보드
│   │   │   ├── StockDetailView.vue # 주식 상세
│   │   │   ├── WatchlistView.vue   # 워치리스트
│   │   │   ├── PortfolioView.vue   # 포트폴리오
│   │   │   ├── LoginView.vue       # 로그인
│   │   │   └── SignupView.vue      # 회원가입
│   │   ├── stores/                 # Pinia 상태 관리
│   │   │   ├── auth.js             # 인증 상태
│   │   │   └── portfolio.js        # 포트폴리오 상태
│   │   ├── router/                 # Vue Router
│   │   │   └── index.js            # 라우트 정의
│   │   ├── App.vue                 # 루트 컴포넌트
│   │   └── main.js                 # Vue 앱 진입점
│   ├── tests/                      # E2E 테스트 (Playwright)
│   │   ├── auth.spec.ts            # 인증 테스트
│   │   ├── watchlist.spec.ts       # 워치리스트 테스트
│   │   └── health.spec.ts          # 헬스체크 테스트
│   ├── public/                     # 정적 파일
│   ├── .env.example                # 환경변수 템플릿
│   ├── package.json                # Node 의존성
│   ├── vite.config.js              # Vite 설정
│   └── playwright.config.ts        # Playwright 설정
│
├── specs/                          # 기능 명세서
│   └── 001-personalized-stock-portfolio/
│       ├── spec.md                 # 기능 명세
│       ├── plan.md                 # 구현 계획
│       ├── data-model.md           # 데이터 모델
│       ├── quickstart.md           # 빠른 시작 가이드
│       └── contracts/
│           └── api.yaml            # OpenAPI 스펙
│
├── scripts/                        # 배포 스크립트
│   ├── provision-azure-mvp.sh      # Azure 리소스 프로비저닝
│   └── README.md                   # 스크립트 사용법
│
├── images/                         # README 이미지
│   ├── 01_stock_watchlist.png      # 워치리스트 스크린샷
│   ├── 02_stock_news.png           # 뉴스 피드 스크린샷
│   └── 03_stock_portfolio.png      # 포트폴리오 스크린샷
│
├── docker-compose.yml               # 로컬 MySQL 컨테이너
├── README.md                        # 프로젝트 문서
└── DEPLOYMENT_GUIDE.md              # Azure 배포 가이드
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

#### Stock News
- `GET /api/v1/stocks/{symbol}` - Get stock quote
- `GET /api/v1/stocks/{symbol}/chart` - Get chart data

#### Portfolios
- `GET /api/v1/portfolios` - List user's portfolios
- `POST /api/v1/portfolios/{id}/holdings` - Add holding
- `GET /api/v1/portfolios/{id}/summary` - Portfolio summary

## Testing

### Backend Tests

```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=src --cov-report=term --cov-report=html

# Run integration tests
pytest tests/integration/

# View coverage report
open htmlcov/index.html  # macOS
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

# View coverage report
open coverage/index.html  # macOS
```

### End-to-End Tests (Playwright)

E2E 테스트는 실제 브라우저에서 전체 사용자 시나리오를 검증합니다.

**사전 준비:**
1. 백엔드가 http://localhost:8000 에서 실행 중이어야 함
2. 프론트엔드가 http://localhost:5173 에서 실행 중이어야 함
3. 데이터베이스가 정상 작동 중이어야 함

```bash
cd frontend

# Playwright 브라우저 설치 (최초 1회)
npx playwright install
![Frontend Test](./images/04_test_playwright.png)  

# 모든 E2E 테스트 실행
npx playwright test

# UI 모드로 실행 (디버깅에 유용)
npx playwright test --ui

# 특정 브라우저에서만 실행
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# 특정 테스트 파일만 실행
npx playwright test tests/auth.spec.ts
npx playwright test tests/watchlist.spec.ts

# 헤드풀 모드로 실행 (브라우저 UI 표시)
npx playwright test --headed

# 디버그 모드로 실행
npx playwright test --debug

# 테스트 리포트 보기
npx playwright show-report

# 테스트 트레이스 보기
npx playwright show-trace trace.zip
```

**주요 테스트 시나리오:**
- `auth.spec.ts` - 회원가입, 로그인, 로그아웃
- `watchlist.spec.ts` - 워치리스트 추가/삭제/정렬
- `stock-detail.spec.ts` - 주식 상세 정보 및 차트 렌더링
- `portfolio.spec.ts` - 포트폴리오 생성 및 종목 추가
- `health.spec.ts` - API 헬스체크 및 기본 동작 확인

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
