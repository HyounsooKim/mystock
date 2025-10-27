#!/bin/bash
set -e

echo "🚀 Setting up MyStock development environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Wait for Cosmos DB Emulator to be ready
print_info "Waiting for Cosmos DB Emulator to be ready..."
timeout=300
counter=0
until curl -k https://cosmos-emulator:8081/_explorer/emulator.pem > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Cosmos DB Emulator failed to start within ${timeout} seconds"
        exit 1
    fi
    sleep 5
    counter=$((counter + 5))
    echo "Waiting... ${counter}s / ${timeout}s"
done
print_step "Cosmos DB Emulator is ready"

# Download and trust Cosmos DB Emulator certificate
print_info "Downloading Cosmos DB Emulator certificate..."
curl -k https://cosmos-emulator:8081/_explorer/emulator.pem > /tmp/emulatorcert.crt
sudo cp /tmp/emulatorcert.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
print_step "Cosmos DB Emulator certificate installed"

# Wait for Azurite to be ready
print_info "Waiting for Azurite (Azure Storage Emulator) to be ready..."
timeout=60
counter=0
until nc -z azurite 10000 > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Azurite failed to start within ${timeout} seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo "Waiting... ${counter}s / ${timeout}s"
done
print_step "Azurite is ready"

# Backend setup
print_info "Setting up Backend (FastAPI)..."
cd /workspace/backend

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_step "Created Python virtual environment"
fi

# Activate virtual environment and install dependencies
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_step "Backend dependencies installed"

# Initialize Cosmos DB if needed
if [ -f "init_cosmos.py" ]; then
    print_info "Initializing Cosmos DB..."
    python init_cosmos.py
    print_step "Cosmos DB initialized"
fi

deactivate

# Azure Functions setup
print_info "Setting up Azure Functions..."
cd /workspace/backend/functions

# Create virtual environment for Functions
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_step "Created Functions virtual environment"
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_step "Azure Functions dependencies installed"
deactivate

# Frontend setup
print_info "Setting up Frontend (Vue 3)..."
cd /workspace/frontend

# Install Node.js dependencies
npm install
print_step "Frontend dependencies installed"

# Install Playwright browsers for E2E testing
if [ -f "playwright.config.ts" ]; then
    npx playwright install chromium --with-deps
    print_step "Playwright browsers installed"
fi

# Create .env files if they don't exist
print_info "Creating environment files..."

# Backend .env
if [ ! -f "/workspace/backend/.env" ]; then
    cat > /workspace/backend/.env << 'EOF'
# Cosmos DB Emulator
COSMOS_ENDPOINT=https://cosmos-emulator:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
COSMOS_DATABASE_NAME=mystock
COSMOS_CONTAINER_NAME=users

# Alpha Vantage API (Replace with your own key)
# Get free key at: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=demo
ALPHA_VANTAGE_USE_DELAYED=true

# JWT Configuration
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080

# CORS Origins
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
EOF
    print_step "Created backend/.env"
fi

# Frontend .env
if [ ! -f "/workspace/frontend/.env" ]; then
    cat > /workspace/frontend/.env << 'EOF'
VITE_API_BASE_URL=http://localhost:8000/api/v1
EOF
    print_step "Created frontend/.env"
fi

# Azure Functions local.settings.json
if [ ! -f "/workspace/backend/functions/local.settings.json" ]; then
    cat > /workspace/backend/functions/local.settings.json << 'EOF'
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "COSMOS_ENDPOINT": "https://cosmos-emulator:8081",
    "COSMOS_KEY": "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
    "COSMOS_DATABASE_NAME": "mystock",
    "ALPHA_VANTAGE_API_KEY": "demo"
  }
}
EOF
    print_step "Created functions/local.settings.json"
fi

# Create README for Codespaces
cat > /workspace/CODESPACES_GUIDE.md << 'EOF'
# 🚀 MyStock Codespaces Development Guide

## Quick Start

### 1. Start Backend (FastAPI)
```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
**Access**: http://localhost:8000/docs (API Documentation)

### 2. Start Frontend (Vue 3)
```bash
cd frontend
npm run dev
```
**Access**: http://localhost:5173 (Web Application)

### 3. Start Azure Functions (Optional)
```bash
cd backend/functions
source .venv/bin/activate
func start
```
**Access**: http://localhost:7071

## Services

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Cosmos DB Emulator | 8081 | https://localhost:8081 | Database |
| Backend API | 8000 | http://localhost:8000 | FastAPI Server |
| Frontend | 5173 | http://localhost:5173 | Vue 3 App |
| Azure Functions | 7071 | http://localhost:7071 | Timer Functions |

## Environment Setup

### Cosmos DB Emulator
- ✅ **Auto-started** in Docker container
- 🔑 **Endpoint**: `https://cosmos-emulator:8081`
- 🔐 **Key**: Built-in emulator key (see .env)
- 📊 **Database**: `mystock`

### Alpha Vantage API Key
Current setup uses `demo` key with limitations. Get your free key:
1. Visit: https://www.alphavantage.co/support/#api-key
2. Update `ALPHA_VANTAGE_API_KEY` in:
   - `backend/.env`
   - `backend/functions/local.settings.json`

## Development Tasks

### Backend Development
```bash
cd backend
source .venv/bin/activate

# Run tests
pytest

# Run with coverage
pytest --cov=src tests/

# Code quality
ruff check .
black .
mypy src/
```

### Frontend Development
```bash
cd frontend

# Run unit tests
npm run test

# Run E2E tests
npm run test:e2e

# Lint & format
npm run lint
npm run format
```

### Database Operations

#### View Cosmos DB Data
Access Cosmos DB Emulator UI:
- URL: https://localhost:8081/_explorer/index.html
- Click "Advanced" → "Proceed to localhost"

#### Initialize/Reset Database
```bash
cd backend
source .venv/bin/activate
python init_cosmos.py
```

## Troubleshooting

### Cosmos DB Connection Issues
```bash
# Test connection
curl -k https://cosmos-emulator:8081/_explorer/emulator.pem

# Restart emulator (if needed)
docker restart cosmos-emulator
```

### Certificate Issues
```bash
# Re-download certificate
curl -k https://cosmos-emulator:8081/_explorer/emulator.pem > /tmp/emulatorcert.crt
sudo cp /tmp/emulatorcert.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8000  # or :5173, :7071

# Kill process
kill -9 <PID>
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              GitHub Codespaces Environment              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐      ┌──────────────┐                │
│  │  Frontend   │──────▶│   Backend    │                │
│  │  Vue 3      │      │   FastAPI    │                │
│  │  :5173      │      │   :8000      │                │
│  └─────────────┘      └──────┬───────┘                │
│                              │                          │
│  ┌─────────────┐             │                          │
│  │   Azure     │             │                          │
│  │  Functions  │─────────────┤                          │
│  │  :7071      │             │                          │
│  └─────────────┘             ▼                          │
│                     ┌─────────────────┐                 │
│                     │   Cosmos DB     │                 │
│                     │   Emulator      │                 │
│                     │   :8081         │                 │
│                     └─────────────────┘                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Tips

### VS Code Tasks
Use Command Palette (Ctrl+Shift+P):
- "Tasks: Run Task" → Select service to start

### Multiple Terminals
Create split terminals for parallel development:
1. Terminal 1: Backend server
2. Terminal 2: Frontend dev server
3. Terminal 3: Azure Functions (optional)

### Live Reload
- ✅ Backend: Auto-reloads on file changes
- ✅ Frontend: HMR (Hot Module Replacement)
- ✅ Functions: Auto-reloads with `--verbose`

## Resources

- [Project Documentation](./README.md)
- [Local Development Guide](./LOCAL_DEVELOPMENT.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Azure Functions Docs](https://learn.microsoft.com/azure/azure-functions/)
- [Cosmos DB Emulator Docs](https://learn.microsoft.com/azure/cosmos-db/local-emulator)
EOF

print_step "Created Codespaces guide"

# Print success message
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ MyStock development environment is ready!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Start Backend:"
echo "   cd backend && source .venv/bin/activate && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Start Frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "3. (Optional) Start Azure Functions:"
echo "   cd backend/functions && source .venv/bin/activate && func start"
echo ""
echo "📖 See CODESPACES_GUIDE.md for detailed instructions"
echo "═══════════════════════════════════════════════════════════"
