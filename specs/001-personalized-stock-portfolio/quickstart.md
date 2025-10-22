# Quickstart Guide: Local Development Setup

**Feature**: 001-personalized-stock-portfolio  
**Date**: 2025-10-21  
**Estimated Setup Time**: 30 minutes

## Overview

This guide will help you set up a complete local development environment for the MyStock Personalized Stock Portfolio application, including:

- **Backend**: FastAPI server with Python 3.11
- **Frontend**: Vue 3 application with Vite dev server
- **Database**: MySQL 8.0 in Docker container
- **Testing**: pytest and Vitest configured

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 20.x LTS | [nodejs.org](https://nodejs.org/) |
| **Docker** | Latest | [docker.com](https://www.docker.com/get-started) |
| **Git** | Latest | Pre-installed on macOS |

### Verification Commands

```bash
# Check Python version
python3 --version  # Should output: Python 3.11.x

# Check Node.js version
node --version     # Should output: v20.x.x

# Check Docker
docker --version   # Should output: Docker version 24.x.x
```

---

## Step 1: Clone Repository and Checkout Feature Branch

```bash
# Clone repository (if not already cloned)
git clone <repository-url>
cd my_stock

# Checkout feature branch
git checkout 001-personalized-stock-portfolio

# Verify you're on correct branch
git branch --show-current
# Output: 001-personalized-stock-portfolio
```

---

## Step 2: Database Setup (MySQL 8.0 with Docker)

### Start MySQL Container

```bash
# Create Docker network for local services
docker network create mystock-network

# Run MySQL 8.0 container
docker run -d \
  --name mystock-mysql \
  --network mystock-network \
  -e MYSQL_ROOT_PASSWORD=rootpass123 \
  -e MYSQL_DATABASE=mystockdb \
  -e MYSQL_USER=mystockuser \
  -e MYSQL_PASSWORD=mystockpass123 \
  -p 3306:3306 \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci

# Wait for MySQL to be ready (takes ~30 seconds)
docker logs -f mystock-mysql
# Look for: "mysqld: ready for connections"
# Press Ctrl+C to exit logs
```

### Verify Database Connection

```bash
# Connect to MySQL using Docker
docker exec -it mystock-mysql mysql -u mystockuser -pmystockpass123 mystockdb

# Inside MySQL shell, run:
SHOW DATABASES;
# You should see: mystockdb

# Exit MySQL shell
exit;
```

---

## Step 3: Backend Setup (FastAPI)

### Create Python Virtual Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# For Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### Install Backend Dependencies

```bash
# Install production dependencies
pip install fastapi uvicorn sqlalchemy pymysql yfinance pydantic-settings

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov httpx alembic

# Freeze dependencies
pip freeze > requirements.txt
```

**Expected `requirements.txt`** (partial):
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pymysql==1.1.0
yfinance==0.2.31
pydantic-settings==2.0.3
pytest==7.4.3
pytest-asyncio==0.21.1
alembic==1.12.1
```

### Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=mysql+pymysql://mystockuser:mystockpass123@localhost:3306/mystockdb

# JWT Authentication
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Stock API Configuration
STOCK_CACHE_TTL_SECONDS=300  # 5 minutes

# Server Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
EOF
```

### Initialize Database Schema

```bash
# Create Alembic migration directory (if not exists)
alembic init src/db/migrations

# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Verify tables were created
docker exec -it mystock-mysql mysql -u mystockuser -pmystockpass123 mystockdb -e "SHOW TABLES;"
# Expected output: users, watchlists, portfolios, holdings, stock_quotes, candlestick_data
```

### Run Backend Server

```bash
# Start FastAPI server with hot reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Server should start on http://localhost:8000
# API docs available at: http://localhost:8000/docs (Swagger UI)
```

**Test Backend Health**:
```bash
# In a new terminal window
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","timestamp":"2025-10-21T12:34:56Z","database":"connected"}
```

---

## Step 4: Frontend Setup (Vue 3 + Vite)

### Install Frontend Dependencies

```bash
# Open new terminal window
cd frontend

# Install Node.js dependencies
npm install

# Install specific packages
npm install vue@3.3.8 vue-router@4.2.5 pinia@2.1.7
npm install @tabler/core@1.0.0-beta20 echarts@5.4.3
npm install axios@1.6.0

# Install dev dependencies
npm install -D vite@5.0.0 @vitejs/plugin-vue@4.5.0
npm install -D vitest@1.0.0 @vue/test-utils@2.4.1
npm install -D tailwindcss@3.3.5 postcss@8.4.31 autoprefixer@10.4.16
```

**Expected `package.json`** (partial):
```json
{
  "name": "mystock-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext .vue,.js,.ts"
  },
  "dependencies": {
    "vue": "^3.3.8",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "@tabler/core": "^1.0.0-beta20",
    "echarts": "^5.4.3",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^4.5.0",
    "vitest": "^1.0.0",
    "@vue/test-utils": "^2.4.1"
  }
}
```

### Configure Environment Variables

Create `.env.local` file in `frontend/` directory:

```bash
cat > .env.local << 'EOF'
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_ENABLE_MOCK_API=false
EOF
```

### Run Frontend Dev Server

```bash
# Start Vite dev server
npm run dev

# Server should start on http://localhost:5173
# Open in browser: http://localhost:5173
```

**Expected Console Output**:
```
VITE v5.0.0  ready in 324 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## Step 5: Verify Complete Setup

### Test Backend API

```bash
# Register a test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'

# Expected response:
# {
#   "id": 1,
#   "email": "test@example.com",
#   "created_at": "2025-10-21T12:34:56Z"
# }

# Login to get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'

# Save the access_token from response
# Export as environment variable:
export TOKEN="<your-access-token>"

# Add stock to watchlist (use token)
curl -X POST http://localhost:8000/api/v1/watchlist \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "symbol": "AAPL",
    "notes": "Apple stock"
  }'

# Get watchlist
curl http://localhost:8000/api/v1/watchlist \
  -H "Authorization: Bearer $TOKEN"
```

### Test Frontend Application

1. Open browser: http://localhost:5173
2. Click "Register" and create account
3. Login with credentials
4. Add stocks to watchlist (AAPL, MSFT, 005930.KS)
5. View stock details with charts
6. Check portfolio page (3 portfolios should be auto-created)

---

## Step 6: Run Tests

### Backend Tests

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
# For Linux: xdg-open htmlcov/index.html
```

**Expected Test Output**:
```
========================= test session starts ==========================
collected 24 items

tests/test_auth.py ......                                        [ 25%]
tests/test_watchlist.py ......                                   [ 50%]
tests/test_stock.py ......                                       [ 75%]
tests/test_portfolio.py ......                                   [100%]

========================== 24 passed in 2.45s ==========================
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm run test

# Run with UI
npm run test -- --ui

# Generate coverage
npm run test -- --coverage
```

---

## Common Issues and Solutions

### Issue 1: MySQL Container Fails to Start

**Symptoms**: `docker ps` doesn't show `mystock-mysql` container

**Solutions**:
```bash
# Check if port 3306 is already in use
lsof -i :3306

# If another MySQL is running, stop it or use different port:
docker run -d \
  --name mystock-mysql \
  -p 3307:3306 \  # Use port 3307 instead
  ...

# Update DATABASE_URL in backend/.env:
DATABASE_URL=mysql+pymysql://mystockuser:mystockpass123@localhost:3307/mystockdb
```

### Issue 2: Backend Can't Connect to Database

**Symptoms**: `sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError)`

**Solutions**:
```bash
# Verify MySQL is running
docker ps | grep mystock-mysql

# Test connection directly
docker exec -it mystock-mysql mysql -u mystockuser -pmystockpass123 -e "SELECT 1;"

# Check DATABASE_URL in backend/.env matches container config
cat backend/.env | grep DATABASE_URL
```

### Issue 3: Frontend Can't Reach Backend API

**Symptoms**: `Network Error` in browser console, CORS errors

**Solutions**:
```bash
# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check CORS_ORIGINS in backend/.env includes frontend URL
cat backend/.env | grep CORS_ORIGINS
# Should include: http://localhost:5173

# Restart backend server after changing .env
```

### Issue 4: yfinance API Rate Limiting

**Symptoms**: `Too many requests` error when fetching stock data

**Solutions**:
```python
# Increase cache TTL in backend/.env
STOCK_CACHE_TTL_SECONDS=600  # 10 minutes instead of 5

# Or use mock data for development:
# In frontend/.env.local:
VITE_ENABLE_MOCK_API=true
```

---

## Development Workflow

### Starting Services

```bash
# Terminal 1: Start MySQL
docker start mystock-mysql

# Terminal 2: Start Backend
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000

# Terminal 3: Start Frontend
cd frontend
npm run dev
```

### Stopping Services

```bash
# Stop frontend (Ctrl+C in Terminal 3)
# Stop backend (Ctrl+C in Terminal 2)

# Stop MySQL container
docker stop mystock-mysql

# Or stop all services:
docker stop mystock-mysql && killall uvicorn && killall node
```

### Database Management

```bash
# View MySQL logs
docker logs mystock-mysql

# Backup database
docker exec mystock-mysql mysqldump -u mystockuser -pmystockpass123 mystockdb > backup.sql

# Restore database
docker exec -i mystock-mysql mysql -u mystockuser -pmystockpass123 mystockdb < backup.sql

# Reset database (careful: deletes all data!)
docker exec mystock-mysql mysql -u mystockuser -pmystockpass123 -e "DROP DATABASE mystockdb; CREATE DATABASE mystockdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
cd backend
alembic upgrade head
```

---

## Next Steps

After completing this setup:

1. **Read the Data Model**: Review `data-model.md` for database schema details
2. **Review API Contracts**: Check `contracts/api.yaml` for endpoint specifications
3. **Explore Codebase**: Familiarize yourself with project structure in `plan.md`
4. **Run Tests**: Ensure all tests pass before making changes
5. **Start Development**: Pick a task from Phase 2 tasks (will be generated separately)

---

## Useful Commands Reference

```bash
# Backend
cd backend
source venv/bin/activate                 # Activate venv
uvicorn src.main:app --reload           # Start server
pytest                                  # Run tests
alembic revision --autogenerate -m "msg" # Create migration
alembic upgrade head                    # Apply migrations

# Frontend
cd frontend
npm run dev                             # Start dev server
npm run build                           # Production build
npm run test                            # Run tests
npm run lint                            # Lint code

# Database
docker exec -it mystock-mysql mysql -u mystockuser -pmystockpass123 mystockdb  # MySQL shell
docker logs mystock-mysql               # View logs
docker restart mystock-mysql            # Restart container

# Docker
docker ps                               # List running containers
docker stop mystock-mysql               # Stop container
docker start mystock-mysql              # Start container
docker rm mystock-mysql                 # Remove container (after stop)
```

---

## Environment Variables Summary

### Backend (`backend/.env`)
```bash
DATABASE_URL=mysql+pymysql://mystockuser:mystockpass123@localhost:3306/mystockdb
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
STOCK_CACHE_TTL_SECONDS=300
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (`frontend/.env.local`)
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_ENABLE_MOCK_API=false
```

---

## Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Vue 3 Documentation**: https://vuejs.org/guide/introduction.html
- **Tabler UI Components**: https://tabler.io/docs
- **ECharts Documentation**: https://echarts.apache.org/en/index.html
- **yfinance Library**: https://github.com/ranaroussi/yfinance
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/

---

**Setup Complete!** You should now have a fully functional local development environment. If you encounter any issues, refer to the "Common Issues and Solutions" section or consult the team.
