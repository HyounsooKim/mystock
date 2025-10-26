# MyStock 로컬 개발 환경 실행 가이드

MyStock 애플리케이션을 로컬 환경에서 실행하기 위한 단계별 가이드입니다.

## 📋 목차

- [사전 요구사항](#사전-요구사항)
- [실행 순서](#실행-순서)
- [트러블슈팅](#트러블슈팅)
- [선택적 구성요소](#선택적-구성요소)

---

## 사전 요구사항

### 필수 소프트웨어

- **Python 3.11** (Backend)
- **Node.js 20+** (Frontend)
- **Azure Cosmos DB Emulator** (로컬 데이터베이스)

### 선택 설치 (Azure Functions 자동화 사용 시)

- **Azure Functions Core Tools v4**
- **Azurite** (로컬 Azure Storage)

### 설치 확인

```powershell
# Python 버전 확인
python --version  # 3.11.x

# Node.js 버전 확인
node --version    # v20.x.x

# Cosmos DB Emulator 설치 확인
Get-Service -Name "Azure Cosmos DB Emulator"

# Azure Functions Core Tools (선택)
func --version    # 4.x.x

# Azurite (선택)
azurite --version
```

---

## 실행 순서

### 1️⃣ Azure Cosmos DB Emulator 실행

**방법 1: GUI 실행**
1. Windows 시작 메뉴 검색: "Azure Cosmos DB Emulator"
2. 클릭하여 실행

**방법 2: 명령줄 실행**
```powershell
& "C:\Program Files\Azure Cosmos DB Emulator\CosmosDB.Emulator.exe"
```

**확인 방법:**
```powershell
# 브라우저에서 Data Explorer 접속
Start-Process "https://localhost:8081/_explorer/index.html"
```

**상태:**
- ✅ 시스템 트레이에 Cosmos DB 아이콘 표시
- ✅ 포트 8081 사용 중
- ✅ Data Explorer 접속 가능

---

### 2️⃣ Backend API 실행

**터미널 1 - PowerShell:**

```powershell
# 1. Backend 디렉토리로 이동
cd C:\Work\Azure\mystock\backend

# 2. Python 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 3. Uvicorn 서버 실행
uvicorn src.main:app --reload --reload-dir src --host 0.0.0.0 --port 8000
```

**실행 로그 예시:**
```
INFO:     Will watch for changes in these directories: ['C:\\Work\\Azure\\mystock\\backend\\src']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**API 테스트:**
```powershell
# 새 터미널에서 실행
curl.exe http://localhost:8000/api/v1/health
curl.exe http://localhost:8000/api/v1/stocks/top-movers
```

**상태:**
- ✅ Backend API: `http://localhost:8000`
- ✅ API 문서: `http://localhost:8000/docs`
- ✅ Health check: `http://localhost:8000/api/v1/health`

---

### 3️⃣ Frontend 실행

**터미널 2 - PowerShell:**

```powershell
# 1. Frontend 디렉토리로 이동
cd C:\Work\Azure\mystock\frontend

# 2. 개발 서버 실행
npm run dev
```

**실행 로그 예시:**
```
VITE v5.0.0  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h to show help
```

**브라우저 접속:**
```powershell
# 자동으로 브라우저 열기
Start-Process "http://localhost:5173"
```

**주요 페이지:**
- 메인: `http://localhost:5173/`
- 로그인: `http://localhost:5173/login`
- 급등락 종목: `http://localhost:5173/top-movers`
- 관심 종목: `http://localhost:5173/watchlist`
- 포트폴리오: `http://localhost:5173/portfolio`

**상태:**
- ✅ Frontend: `http://localhost:5173`
- ✅ HMR (Hot Module Replacement) 활성화
- ✅ Backend API 연결: `http://localhost:8000/api/v1`

---

### 4️⃣ 초기 데이터 입력 (최초 1회)

Cosmos DB에 Top Movers 데이터가 없으면 `/top-movers` 페이지에서 503 에러가 발생합니다.

**방법 1: 수동 스크립트 실행 (권장)**

```powershell
# Backend 디렉토리에서
cd C:\Work\Azure\mystock\backend
.\.venv\Scripts\Activate.ps1
python populate_top_movers.py
```

**실행 결과:**
```
============================================================
Manual Top Movers Data Population
============================================================
Fetching data from Alpha Vantage...
✓ Fetched 20 gainers
✓ Fetched 20 losers
✓ Fetched 20 active

Connecting to Cosmos DB: https://localhost:8081
✓ Container 'top_movers' ready
✓ Saved document: top-movers-2025-10-26T13:00:00.000000+00:00

============================================================
SUCCESS! Data saved to Cosmos DB
============================================================
```

**방법 2: Azure Functions 사용 (자동화)**

아래 [선택적 구성요소](#선택적-구성요소) 섹션 참조

---

## 선택적 구성요소

### Azure Functions (자동 데이터 업데이트)

매시간 자동으로 Top Movers 데이터를 업데이트하려면 Azure Functions를 실행합니다.

#### A. Azurite 실행

**터미널 3 - PowerShell:**

```powershell
azurite --silent --location c:\azurite
```

**상태:**
- ✅ Blob Service: `http://127.0.0.1:10000`
- ✅ Queue Service: `http://127.0.0.1:10001`
- ✅ Table Service: `http://127.0.0.1:10002`

#### B. Azure Functions 실행

**터미널 4 - PowerShell:**

```powershell
# 1. Functions 디렉토리로 이동
cd C:\Work\Azure\mystock\backend\functions

# 2. Python 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 3. Functions 실행
func start
```

**실행 로그 예시:**
```
Azure Functions Core Tools
Core Tools Version:       4.0.5148
Function Runtime Version: 4.17.3.20392

Functions:
        top_movers_updater: timerTrigger

For detailed output, run func with --verbose flag.
[timestamp] Worker process started and initialized.
```

**상태:**
- ✅ Functions Runtime: `http://localhost:7071`
- ✅ Timer Trigger: 매시간 정각 실행 (`0 0 * * * *`)
- ✅ Admin API: `http://localhost:7071/admin/functions/top_movers_updater`

#### C. 수동 트리거 (테스트용)

```powershell
# 새 터미널에서
Invoke-RestMethod -Method POST -Uri "http://localhost:7071/admin/functions/top_movers_updater" -Headers @{"Content-Type"="application/json"} -Body '{}'
```

---

## 전체 실행 요약

### 최소 구성 (필수만)

| 순서 | 서비스 | 포트 | 터미널 | 자동 시작 |
|------|--------|------|--------|-----------|
| 1 | Cosmos DB Emulator | 8081 | GUI | ❌ 수동 |
| 2 | Backend API | 8000 | 터미널 1 | ❌ 수동 |
| 3 | Frontend | 5173 | 터미널 2 | ❌ 수동 |
| - | 초기 데이터 | - | 터미널 3 | ❌ 1회 실행 |

**실행 명령 한눈에 보기:**
```powershell
# 터미널 1 - Backend
cd C:\Work\Azure\mystock\backend
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --reload --reload-dir src --host 0.0.0.0 --port 8000

# 터미널 2 - Frontend
cd C:\Work\Azure\mystock\frontend
npm run dev

# 터미널 3 - 초기 데이터 (최초 1회)
cd C:\Work\Azure\mystock\backend
.\.venv\Scripts\Activate.ps1
python populate_top_movers.py
```

### 전체 구성 (Functions 포함)

| 순서 | 서비스 | 포트 | 터미널 | 자동 시작 |
|------|--------|------|--------|-----------|
| 1 | Cosmos DB Emulator | 8081 | GUI | ❌ 수동 |
| 2 | Azurite | 10000-10002 | 터미널 1 | ❌ 수동 |
| 3 | Azure Functions | 7071 | 터미널 2 | ⏰ 매시간 |
| 4 | Backend API | 8000 | 터미널 3 | ❌ 수동 |
| 5 | Frontend | 5173 | 터미널 4 | ❌ 수동 |

---

## 트러블슈팅

### 1. Cosmos DB 연결 실패

**증상:**
```
ERROR: Unable to connect to Cosmos DB
```

**해결:**
```powershell
# Cosmos DB Emulator 실행 확인
Get-Service -Name "Azure Cosmos DB Emulator"

# 재시작
Restart-Service -Name "Azure Cosmos DB Emulator"

# 또는 GUI에서 재시작
& "C:\Program Files\Azure Cosmos DB Emulator\CosmosDB.Emulator.exe"
```

---

### 2. Backend 무한 리로드

**증상:**
```
WARNING: WatchFiles detected changes in 'functions\.venv\...'
```

**해결:**
```powershell
# --reload-dir 옵션 사용 (functions 폴더 제외)
uvicorn src.main:app --reload --reload-dir src --host 0.0.0.0 --port 8000
```

---

### 3. Azure Functions 시작 실패

**증상:**
```
The listener for function 'Functions.TopMoversUpdater' was unable to start.
대상 컴퓨터에서 연결을 거부했으므로 연결하지 못했습니다. (127.0.0.1:10000)
```

**해결:**
```powershell
# Azurite 실행 확인
azurite --silent --location c:\azurite

# Functions 재시작
cd C:\Work\Azure\mystock\backend\functions
func start
```

---

### 4. Frontend 빌드 오류

**증상:**
```
ERROR: Failed to resolve import
```

**해결:**
```powershell
# 패키지 재설치
cd C:\Work\Azure\mystock\frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install

# 개발 서버 재시작
npm run dev
```

---

### 5. Top Movers 페이지 503 에러

**증상:**
```
503 Service Unavailable
No top movers data found in Cosmos DB
```

**해결:**
```powershell
# 수동 데이터 입력
cd C:\Work\Azure\mystock\backend
.\.venv\Scripts\Activate.ps1
python populate_top_movers.py

# 또는 Functions 수동 트리거
Invoke-RestMethod -Method POST -Uri "http://localhost:7071/admin/functions/top_movers_updater" -Headers @{"Content-Type"="application/json"} -Body '{}'
```

---

### 6. Alpha Vantage API 제한

**증상:**
```
API note: Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute
```

**해결:**
- 무료 플랜: 하루 25회, 분당 5회 제한
- `.env` 파일에서 다른 API 키 사용
- 또는 API 호출 간격 조정 (Functions 스케줄 변경)

---

## 환경 변수 설정

### Backend (`.env`)

```env
# Cosmos DB (로컬 Emulator)
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
COSMOS_DATABASE_NAME=mystockdb
COSMOS_CONTAINER_NAME=users

# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=your_api_key_here
ALPHA_VANTAGE_USE_DELAYED=true

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Functions (`local.settings.json`)

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ALPHA_VANTAGE_API_KEY": "your_api_key_here",
    "COSMOS_ENDPOINT": "https://localhost:8081",
    "COSMOS_KEY": "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
    "COSMOS_DATABASE_NAME": "mystockdb"
  }
}
```

### Frontend (`.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 개발 팁

### 빠른 시작 스크립트

**`start-dev.ps1` (루트 디렉토리에 생성):**

```powershell
# MyStock 로컬 개발 환경 빠른 시작 스크립트

Write-Host "Starting MyStock Development Environment..." -ForegroundColor Green

# Cosmos DB Emulator 확인
$cosmosService = Get-Service -Name "Azure Cosmos DB Emulator" -ErrorAction SilentlyContinue
if ($cosmosService.Status -ne "Running") {
    Write-Host "Starting Cosmos DB Emulator..." -ForegroundColor Yellow
    Start-Service -Name "Azure Cosmos DB Emulator"
    Start-Sleep -Seconds 10
}

# Backend 실행
Write-Host "Starting Backend API..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Work\Azure\mystock\backend; .\.venv\Scripts\Activate.ps1; uvicorn src.main:app --reload --reload-dir src --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 3

# Frontend 실행
Write-Host "Starting Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Work\Azure\mystock\frontend; npm run dev"

Write-Host "`nAll services started!" -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
```

**실행:**
```powershell
.\start-dev.ps1
```

---

### VS Code 통합 터미널 설정

**`.vscode/tasks.json`:**

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Backend",
      "type": "shell",
      "command": "cd backend && .venv/Scripts/Activate.ps1 && uvicorn src.main:app --reload --reload-dir src --host 0.0.0.0 --port 8000",
      "problemMatcher": [],
      "isBackground": true
    },
    {
      "label": "Start Frontend",
      "type": "shell",
      "command": "cd frontend && npm run dev",
      "problemMatcher": [],
      "isBackground": true
    },
    {
      "label": "Populate Top Movers",
      "type": "shell",
      "command": "cd backend && .venv/Scripts/Activate.ps1 && python populate_top_movers.py",
      "problemMatcher": []
    }
  ]
}
```

---

## 참고 자료

- [Azure Cosmos DB Emulator 문서](https://docs.microsoft.com/azure/cosmos-db/local-emulator)
- [Azure Functions Core Tools](https://docs.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite 문서](https://docs.microsoft.com/azure/storage/common/storage-use-azurite)
- [Alpha Vantage API 문서](https://www.alphavantage.co/documentation/)

---

**마지막 업데이트:** 2025-10-26
