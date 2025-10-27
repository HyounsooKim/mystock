# 🚀 GitHub Codespaces Quick Start

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/HyounsooKim/mystock)

MyStock 프로젝트를 GitHub Codespaces에서 실행하기 위한 가이드입니다.

## ✨ 특징

- **원클릭 개발 환경**: Codespace 생성 시 모든 것이 자동으로 설정됩니다
- **Cosmos DB Emulator**: Docker 컨테이너로 실행되는 완전한 로컬 데이터베이스
- **Azure Functions**: 로컬에서 Timer Trigger 함수 테스트 가능
- **Hot Reload**: Backend(FastAPI)와 Frontend(Vue 3) 모두 자동 리로드 지원

## 🏗️ 자동 구성 항목

Codespace 생성 시 다음이 자동으로 설정됩니다:

### 1. 개발 환경
- ✅ Python 3.11 + 가상환경
- ✅ Node.js 20 + npm
- ✅ Azure Functions Core Tools v4
- ✅ Azure CLI

### 2. 데이터베이스 & 스토리지
- ✅ Cosmos DB Linux Emulator (Docker)
- ✅ Azurite (Azure Storage Emulator)
- ✅ 자동 인증서 설치
- ✅ 데이터베이스 초기화

### 3. 의존성
- ✅ Backend: FastAPI, Azure SDK, pytest 등
- ✅ Frontend: Vue 3, Vite, ECharts 등
- ✅ Functions: Azure Functions Python 런타임

### 4. 설정 파일
- ✅ `.env` 파일 자동 생성
- ✅ `local.settings.json` 구성
- ✅ CORS 설정 (Codespaces URL 포함)

## 🚦 서비스 시작하기

### 옵션 1: VS Code Tasks 사용 (권장)

1. **Command Palette** 열기: `Ctrl+Shift+P` (또는 `Cmd+Shift+P`)
2. **"Tasks: Run Task"** 선택
3. 원하는 작업 선택:
   - `Start All Services` - Backend + Frontend 동시 시작
   - `Start Backend (FastAPI)` - Backend만 시작
   - `Start Frontend (Vite)` - Frontend만 시작
   - `Start Azure Functions` - Azure Functions만 시작

### 옵션 2: 수동으로 터미널에서 실행

#### Backend 시작
```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend 시작
```bash
cd frontend
npm run dev
```

#### Azure Functions 시작 (선택사항)
```bash
cd backend/functions
source .venv/bin/activate
func start
```

## 🌐 접속 URL

Codespace에서 서비스가 시작되면 다음 포트가 자동으로 포워딩됩니다:

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Frontend | 5173 | Vue 3 웹 애플리케이션 (자동으로 브라우저 열림) |
| Backend API | 8000 | FastAPI 서버 + Swagger UI (/docs) |
| Azure Functions | 7071 | Timer Trigger 함수 |
| Cosmos DB | 8081 | Emulator 데이터 탐색기 |
| Azurite Blob | 10000 | Azure Blob Storage Emulator |
| Azurite Queue | 10001 | Azure Queue Storage Emulator |
| Azurite Table | 10002 | Azure Table Storage Emulator |

**포트 탭**에서 각 URL을 클릭하여 접속할 수 있습니다.

## 🔑 Alpha Vantage API 키 설정

기본적으로 `demo` 키가 사용되지만, 실제 데이터를 위해서는 무료 API 키를 받으세요:

1. https://www.alphavantage.co/support/#api-key 에서 무료 키 발급
2. 다음 파일을 수정:

```bash
# backend/.env
ALPHA_VANTAGE_API_KEY=your_actual_key_here

# backend/functions/local.settings.json
{
  "Values": {
    "ALPHA_VANTAGE_API_KEY": "your_actual_key_here",
    ...
  }
}
```

3. 서비스 재시작

## 🗄️ 데이터베이스 관리

### Cosmos DB Emulator UI 접속

1. 포트 탭에서 `8081` 클릭
2. 브라우저에서 "고급" → "계속" 클릭 (자체 서명 인증서 경고)
3. Data Explorer에서 데이터 확인/수정 가능

### 데이터베이스 초기화/리셋

```bash
cd backend
source .venv/bin/activate
python init_cosmos.py
```

### 샘플 데이터 추가 (급등락 종목)

```bash
cd backend
source .venv/bin/activate
python populate_top_movers.py
```

## 🧪 테스트 실행

### Backend 테스트
```bash
cd backend
source .venv/bin/activate
pytest -v

# 커버리지 포함
pytest --cov=src tests/
```

### Frontend 테스트
```bash
cd frontend
npm run test

# E2E 테스트
npm run test:e2e
```

## 🛠️ 개발 팁

### 1. Multiple Terminals
Split Terminal을 사용하여 동시에 여러 서비스 실행:
- Terminal 1: Backend
- Terminal 2: Frontend  
- Terminal 3: Azure Functions
- Terminal 4: 일반 작업용

### 2. Live Reload
- ✅ Backend: 파일 저장 시 자동 재시작
- ✅ Frontend: HMR (Hot Module Replacement)
- ✅ Functions: `--verbose` 옵션으로 상세 로그 확인

### 3. VS Code 확장
다음 확장이 자동으로 설치됩니다:
- Python (Pylance, Black formatter)
- Vue Language Features (Volar)
- Azure Functions
- Azure Cosmos DB
- GitHub Copilot

### 4. 디버깅
`.vscode/launch.json`이 구성되어 있어 F5로 디버깅 가능:
- FastAPI Backend 디버깅
- Azure Functions 디버깅

## 📊 아키텍처

```
┌──────────────────────────────────────────────────────┐
│         GitHub Codespaces Container                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Frontend (Vue 3)          Backend (FastAPI)        │
│  ┌─────────────┐           ┌──────────────┐        │
│  │   Vite      │──HTTP────▶│   FastAPI    │        │
│  │   :5173     │           │   :8000      │        │
│  └─────────────┘           └──────┬───────┘        │
│                                   │                  │
│  Azure Functions                  │                  │
│  ┌─────────────┐                  │                  │
│  │ Timer Func  │──────────────────┤                  │
│  │   :7071     │                  │                  │
│  └──────┬──────┘                  │                  │
│         │                         ▼                  │
│         │                ┌──────────────────┐        │
│         │                │  Cosmos DB       │        │
│         │                │  Emulator        │        │
│         │                │  (Docker)        │        │
│         │                │  :8081           │        │
│         │                └──────────────────┘        │
│         │                                            │
│         ▼                                            │
│  ┌──────────────────┐                               │
│  │  Azurite         │                               │
│  │  Storage         │                               │
│  │  Emulator        │                               │
│  │  :10000-10002    │                               │
│  └──────────────────┘                               │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## 🐛 트러블슈팅

### Cosmos DB 연결 실패
```bash
# Emulator 상태 확인
docker ps | grep cosmos

# 재시작
docker restart cosmos-emulator

# 인증서 재설치
curl -k https://cosmos-emulator:8081/_explorer/emulator.pem > /tmp/emulatorcert.crt
sudo cp /tmp/emulatorcert.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

### 포트 충돌
```bash
# 사용 중인 프로세스 확인
lsof -i :8000  # 또는 :5173, :7071

# 프로세스 종료
kill -9 <PID>
```

### Azurite 연결 확인
```bash
# Blob service 테스트
curl http://azurite:10000/devstoreaccount1?comp=list

# Azure Storage Explorer 사용 가능
# Connection string: UseDevelopmentStorage=true
```

### Python 가상환경 문제
```bash
# 가상환경 재생성
cd backend
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### npm 의존성 문제
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 추가 문서

- [프로젝트 README](./README.md)
- [로컬 개발 가이드](./LOCAL_DEVELOPMENT.md)
- [Codespaces 상세 가이드](./CODESPACES_GUIDE.md) - setup.sh 실행 후 생성됨

## 💡 주요 기능 사용법

### 1. 사용자 등록 및 로그인
1. Frontend (http://localhost:5173) 접속
2. "회원가입" 클릭하여 계정 생성
3. 로그인 후 관심종목 추가

### 2. 관심종목 관리
- 상단 "관심종목" 메뉴
- "종목 추가" 버튼으로 미국 주식 추가 (예: AAPL, MSFT, TSLA)
- 드래그 앤 드롭으로 순서 변경

### 3. 포트폴리오 관리
- "포트폴리오" 메뉴에서 보유 종목 추가
- 수량, 평균 단가 입력하여 손익 확인

### 4. 급등락 종목
- "급등락" 메뉴에서 실시간 Top Movers 확인
- Azure Functions로 매시간 자동 갱신 (로컬에서는 수동 실행)

## 🎯 다음 단계

1. ✅ Codespace 생성 및 환경 구성 완료
2. 🚀 서비스 시작 및 애플리케이션 탐색
3. 💻 코드 수정 및 실시간 확인
4. 🧪 테스트 작성 및 실행
5. 🔄 GitHub에 Push 및 배포

---

**문제가 있나요?** [Issue](https://github.com/HyounsooKim/mystock/issues)를 열어주세요!
