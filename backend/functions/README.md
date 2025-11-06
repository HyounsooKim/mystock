# Top Movers Azure Functions

Azure Functions를 사용하여 Top Movers 데이터를 주기적으로 Cosmos DB에 저장합니다.

## 📋 개요

- **Function**: TopMoversUpdater
- **Trigger**: Timer (매시간 정각)
- **데이터 소스**: Alpha Vantage API
- **저장소**: Azure Cosmos DB (top_movers 컨테이너)

## 🏗️ 아키텍처

```
Azure Functions (Timer)  →  Alpha Vantage API
         ↓
    Cosmos DB (top_movers 컨테이너)
         ↓
    Backend API (최신 데이터 조회)
```

## 📊 Cosmos DB 스키마

### Container: `top_movers`
- **Partition Key**: `/date`
- **Throughput**: 400 RU/s

### Document 구조:
```json
{
  "id": "top-movers-2025-10-25T01:00:00.000000+00:00",
  "date": "2025-10-25",
  "timestamp": "2025-10-25T01:00:00.000000+00:00",
  "data": {
    "top_gainers": [...],
    "top_losers": [...],
    "most_actively_traded": [...]
  },
  "metadata": {
    "last_updated": "2025-10-24",
    "record_count": {
      "gainers": 20,
      "losers": 20,
      "active": 20
    }
  }
}
```

## 🚀 로컬 개발 환경 설정

### 1. 필수 도구 설치

```powershell
# Azure Functions Core Tools 설치 (버전 4)
winget install Microsoft.Azure.FunctionsCoreTools

# 또는 npm으로 설치
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Cosmos DB Emulator 설치 (선택사항)
winget install Microsoft.Azure.CosmosEmulator
```

### 2. Python 가상환경 설정

```powershell
cd backend/functions

# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt
```

### 3. 환경변수 설정

`local.settings.json` 파일을 수정하여 실제 API 키와 Cosmos DB 정보를 입력합니다:

**⚠️ 로컬 개발 전용**: Azure 배포 시에는 관리형 ID를 사용하므로 `COSMOS_KEY`가 필요 없습니다.

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ALPHA_VANTAGE_API_KEY": "YOUR_ACTUAL_API_KEY",
    "COSMOS_ENDPOINT": "https://your-cosmos-account.documents.azure.com:443/",
    "COSMOS_KEY": "YOUR_COSMOS_KEY",  // 로컬 개발용 (Azure 배포 시 자동 제거)
    "COSMOS_DATABASE_NAME": "mystock"
  }
}
```

**Azure 인증 사용 (권장 - 로컬 개발):**
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ALPHA_VANTAGE_API_KEY": "YOUR_ACTUAL_API_KEY",
    "COSMOS_ENDPOINT": "https://your-cosmos-account.documents.azure.com:443/",
    "COSMOS_DATABASE_NAME": "mystock"
    // COSMOS_KEY 없음 - Azure CLI 로그인 후 DefaultAzureCredential 사용
  }
}
```

로컬에서 Azure 인증을 사용하려면:
```bash
az login
# 또는 관리형 ID 시뮬레이션
az account get-access-token --resource https://cosmos.azure.com
```

**로컬 Cosmos DB Emulator 사용 시:**
```json
{
  "COSMOS_ENDPOINT": "https://localhost:8081",
  "COSMOS_KEY": "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
  "COSMOS_DATABASE_NAME": "mystock"
}
```

### 4. Timer 스케줄 조정 (테스트용)

`TopMoversUpdater/function.json` 파일에서 스케줄을 변경하여 빠르게 테스트할 수 있습니다:

```json
{
  "schedule": "0 */5 * * * *"  // 5분마다 실행 (테스트)
}
```

**NCRONTAB 형식:**
- `0 0 * * * *` - 매시간 정각 (프로덕션)
- `0 */5 * * * *` - 5분마다
- `0 */1 * * * *` - 1분마다 (빠른 테스트)

## 🧪 로컬 실행

### 1. Functions 시작

```powershell
cd backend/functions
func start

# 상세 로그 보기
func start --verbose
```

**출력 예시:**
```
Azure Functions Core Tools
Core Tools Version:       4.0.5455
Function Runtime Version: 4.21.3.20698

Functions:

        TopMoversUpdater: timerTrigger

For detailed output, run func with --verbose flag.
[2025-10-25T01:00:00.000Z] Executing 'TopMoversUpdater'
[2025-10-25T01:00:00.123Z] Top Movers Updater function executed at 2025-10-25T01:00:00
[2025-10-25T01:00:01.456Z] Fetching top movers from Alpha Vantage API
[2025-10-25T01:00:02.789Z] Successfully fetched top movers data
[2025-10-25T01:00:03.012Z] Container 'top_movers' ready
[2025-10-25T01:00:03.345Z] Successfully saved top movers data: top-movers-2025-10-25T01:00:00
```

### 2. 수동 실행 (Timer 대기 없이)

다른 터미널에서 실행:

```powershell
curl -X POST http://localhost:7071/admin/functions/TopMoversUpdater
```

### 3. 데이터 확인

**Cosmos DB Emulator 사용 시:**
1. 브라우저에서 `https://localhost:8081/_explorer/index.html` 접속
2. `mystock` 데이터베이스 선택
3. `top_movers` 컨테이너 선택
4. 저장된 문서 확인

**Azure Cosmos DB 사용 시:**
- Azure Portal에서 Data Explorer로 확인

## 🐛 디버깅

### VS Code에서 디버깅

1. **F5** 키를 눌러 디버깅 시작
2. `__init__.py`에 브레이크포인트 설정
3. 함수가 실행될 때 중단점에서 멈춤
4. 변수 값 확인 및 스텝 실행 가능

### 로그 레벨 조정

`host.json`에서 로그 레벨 설정:

```json
{
  "logging": {
    "logLevel": {
      "default": "Information",
      "Function": "Information"
    }
  }
}
```

## 📝 트러블슈팅

### 1. Cosmos DB 연결 실패

**증상:**
```
Error: Unable to connect to Cosmos DB
```

**해결:**
- Cosmos DB Emulator가 실행 중인지 확인
- `local.settings.json`의 COSMOS_ENDPOINT와 COSMOS_KEY 확인
- 로컬 Emulator 사용 시 SSL 인증서 신뢰 설정

### 2. Alpha Vantage API 제한

**증상:**
```
API note: Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute
```

**해결:**
- API 키를 프리미엄으로 업그레이드
- 또는 Timer 간격을 더 길게 설정 (예: 6시간마다)

### 3. 함수가 실행되지 않음

**증상:**
Timer가 트리거되지 않음

**해결:**
```powershell
# AzureWebJobsStorage 확인
# local.settings.json에 "UseDevelopmentStorage=true" 설정되어 있는지 확인

# Azurite 설치 및 실행 (로컬 스토리지 에뮬레이터)
npm install -g azurite
azurite --silent --location c:\azurite
```

## 🚢 Azure 배포

### 1. Function App 생성

```bash
az functionapp create \
  --resource-group rg-mystock-prod \
  --consumption-plan-location koreacentral \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name func-mystock-topmovers \
  --storage-account stmystockfunc
```

### 2. 환경변수 설정

```bash
az functionapp config appsettings set \
  --name func-mystock-topmovers \
  --resource-group rg-mystock-prod \
  --settings \
    ALPHA_VANTAGE_API_KEY="your-api-key" \
    COSMOS_ENDPOINT="https://cosmos-mystock.documents.azure.com:443/" \
    COSMOS_KEY="your-cosmos-key" \
    COSMOS_DATABASE_NAME="mystock"
```

### 3. 배포

```bash
cd backend/functions
func azure functionapp publish func-mystock-topmovers
```

## 📊 모니터링

### Azure Portal에서 확인

1. Function App → Functions → TopMoversUpdater
2. Monitor 탭에서 실행 로그 확인
3. Application Insights에서 성능 메트릭 확인

### 비용 최적화

- **Consumption Plan**: 실행 시간만 과금 (매시간 1회 = 월 ~$0.01)
- **Cosmos DB**: 400 RU/s = 월 ~$24
- **총 예상 비용**: ~$24/월

## 🔒 보안

### 인증 및 접근 제어

- **관리형 ID**: 시스템 할당 관리형 ID 활성화
- **FTP**: 기본 인증 비활성화 (`ftpsState: 'Disabled'`)
- **SCM (Kudu)**: 기본 인증 비활성화
- **Cosmos DB**: RBAC 기반 접근 (Built-in Data Contributor 역할)

### 배포 보안

- **GitHub Actions**: Azure AD 인증 사용 (publish profile 미사용)
- **로컬 개발**: Azure CLI 로그인 필요

자세한 내용은 [`docs/SECURITY_KEYLESS_AUTHENTICATION.md`](../../docs/SECURITY_KEYLESS_AUTHENTICATION.md) 참조

## 📚 참고 자료

- [Azure Functions Python Developer Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)
- [Cosmos DB Python SDK](https://docs.microsoft.com/azure/cosmos-db/sql/sdk-python)
- [Alpha Vantage API Documentation](https://www.alphavantage.co/documentation/)
- [Azure Functions 보안](https://docs.microsoft.com/azure/azure-functions/security-concepts)
