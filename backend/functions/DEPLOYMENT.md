# Azure Functions 배포 가이드

Azure Functions (Top Movers Updater)를 Azure 클라우드에 배포하는 가이드입니다.

> **🔒 보안 참고**: 이 Function App은 키리스 보안 구성이 적용되어 있습니다:
> - FTP/SCM 기본 인증 비활성화
> - 시스템 할당 관리형 ID 활성화
> - Cosmos DB RBAC 기반 접근 제어
> 
> 자세한 내용은 [`docs/SECURITY_KEYLESS_AUTHENTICATION.md`](../../docs/SECURITY_KEYLESS_AUTHENTICATION.md) 참조

## 📋 목차

- [아키텍처 개요](#아키텍처-개요)
- [사전 요구사항](#사전-요구사항)
- [인프라 배포](#인프라-배포)
- [Functions 배포](#functions-배포)
- [배포 확인](#배포-확인)
- [모니터링](#모니터링)
- [트러블슈팅](#트러블슈팅)

---

## 아키텍처 개요

### 구성 요소

```
┌─────────────────────┐
│ Azure Functions     │ (Timer: 매시간)
│ (Consumption Plan)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Alpha Vantage API   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Cosmos DB           │
│ (top_movers 컨테이너)│
└─────────────────────┘
```

### 리소스

| 리소스 | 용도 | SKU/Tier |
|--------|------|----------|
| Function App | Timer-triggered 함수 실행 | Consumption Y1 |
| Storage Account | Functions 런타임 저장소 | Standard_LRS |
| App Service Plan | Functions 호스팅 | Consumption (Dynamic) |
| Cosmos DB | 데이터 저장소 | Serverless (기존) |
| Log Analytics | 로그 및 메트릭 | PerGB2018 (기존) |
| Application Insights | 애플리케이션 모니터링 | 기존 |

### 예상 비용

- **Function App (Consumption)**: ~$0.20/월
  - 실행: 720회/월 (매시간)
  - 실행 시간: ~5초/회
  - 메모리: 256MB
  - 월 100만 실행 무료 → 비용 거의 없음

- **Storage Account**: ~$0.10/월
  - Functions 런타임 저장소
  - 10GB 미만 사용

- **총 예상 비용**: ~$0.30/월

---

## 사전 요구사항

### 1. Azure CLI 설치

```powershell
# Azure CLI 설치
winget install Microsoft.AzureCLI

# 버전 확인
az --version
```

### 2. Azure Functions Core Tools 설치

```powershell
# Functions Core Tools 설치
winget install Microsoft.Azure.FunctionsCoreTools

# 버전 확인
func --version  # 4.x.x
```

### 3. Azure 로그인

```powershell
# Azure 로그인
az login

# 구독 설정
az account set --subscription "your-subscription-id"

# 현재 구독 확인
az account show
```

### 4. 기존 인프라 확인

```powershell
# Resource Group 확인
az group show --name rg-mystock-dev

# Cosmos DB 확인
az cosmosdb show --name cosmos-mystock-dev --resource-group rg-mystock-dev

# Log Analytics 확인
az monitor log-analytics workspace show --resource-group rg-mystock-dev --workspace-name log-mystock-dev
```

---

## 인프라 배포

### 옵션 1: Bicep 템플릿으로 전체 배포

기존 인프라를 업데이트하여 Functions 추가:

```powershell
cd C:\Work\Azure\mystock\infra

# 배포 실행
az deployment sub create `
  --location koreacentral `
  --template-file main.bicep `
  --parameters `
    environmentName=dev `
    appName=mystock `
    githubRepoUrl="HyounsooKim/mystock" `
    githubBranch=main `
    alphaVantageApiKey="YOUR_API_KEY" `
    jwtSecretKey="YOUR_JWT_SECRET"
```

**참고:** 기존 리소스는 변경되지 않고, Functions 리소스만 추가됩니다.

### 옵션 2: Functions 모듈만 배포

```powershell
cd C:\Work\Azure\mystock\infra

# Resource Group ID 가져오기
$rgId = az group show --name rg-mystock-dev --query id -o tsv

# Functions 모듈만 배포
az deployment group create `
  --resource-group rg-mystock-dev `
  --template-file modules/functions.bicep `
  --parameters `
    location=koreacentral `
    appName=mystock `
    environmentName=dev `
    tags='{"Environment":"dev","Application":"mystock"}' `
    logAnalyticsWorkspaceId="/subscriptions/.../workspaces/log-mystock-dev" `
    appInsightsConnectionString="InstrumentationKey=..." `
    cosmosDbEndpoint="https://cosmos-mystock-dev.documents.azure.com:443/" `
    cosmosDbKey="YOUR_COSMOS_KEY" `
    cosmosDbDatabaseName="mystockdb" `
    alphaVantageApiKey="YOUR_API_KEY"
```

---

## Functions 배포

### 방법 1: PowerShell 스크립트 사용 (권장)

```powershell
cd C:\Work\Azure\mystock\infra

# 배포 스크립트 실행
.\deploy-functions.ps1 -EnvironmentName dev
```

**스크립트가 수행하는 작업:**
1. Azure 로그인 확인
2. Function App 존재 확인
3. Python 의존성 설치
4. Azure Functions에 배포
5. 배포 결과 출력

### 방법 2: Azure Functions Core Tools 직접 사용

```powershell
cd C:\Work\Azure\mystock\backend\functions

# 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# Azure Functions에 배포
func azure functionapp publish func-mystock-topmovers-dev --python
```

### 방법 3: GitHub Actions 자동 배포 (권장)

**⚠️ 보안 강화**: 기본 인증이 비활성화되어 있으므로, publish profile 대신 Azure 서비스 프린시플을 사용합니다.

#### Step 1: Azure 서비스 프린시플 생성

```powershell
# 서비스 프린시플 생성 및 역할 할당
az ad sp create-for-rbac `
  --name "github-actions-mystock-functions" `
  --role "Contributor" `
  --scopes "/subscriptions/<subscription-id>/resourceGroups/rg-mystock-dev" `
  --sdk-auth

# 출력 예시 (JSON 저장)
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "...",
  "resourceManagerEndpointUrl": "..."
}
```

#### Step 2: GitHub Secrets 설정

1. GitHub 리포지토리 → Settings → Secrets and variables → Actions
2. New repository secret 클릭
3. 다음 Secret 추가:
   - Name: `AZURE_CREDENTIALS`
   - Value: (Step 1에서 생성된 JSON 전체 복사)

#### Step 3: 워크플로우 트리거

```powershell
# backend/functions/ 디렉토리 변경 후 commit & push
git add backend/functions/
git commit -m "Update Azure Functions"
git push origin main
```

GitHub Actions가 자동으로 RBAC 기반 배포를 시작합니다.

---

## 배포 확인

### 1. Function App 상태 확인

```powershell
# Function App 정보
az functionapp show `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --query "{name:name, state:state, defaultHostName:defaultHostName}" `
  --output table
```

### 2. Functions 목록 확인

```powershell
# 배포된 함수 목록
az functionapp function show `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --function-name top_movers_updater
```

### 3. 수동 실행 테스트

#### 방법 A: Azure Portal

1. Azure Portal 접속
2. Function App → Functions → top_movers_updater
3. "Code + Test" 탭 → "Test/Run" 클릭
4. "Run" 버튼 클릭

#### 방법 B: Azure CLI

```powershell
# 함수 수동 트리거
az functionapp function invoke `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --function-name top_movers_updater
```

#### 방법 C: HTTP 요청 (Admin Key 필요)

```powershell
# Function Key 가져오기
$masterKey = az functionapp keys list `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --query masterKey -o tsv

# 함수 실행
curl.exe -X POST "https://func-mystock-topmovers-dev.azurewebsites.net/admin/functions/top_movers_updater?code=$masterKey"
```

### 4. Cosmos DB 데이터 확인

```powershell
# Cosmos DB에서 최신 데이터 확인
az cosmosdb sql container query `
  --account-name cosmos-mystock-dev `
  --database-name mystockdb `
  --name top_movers `
  --query-text "SELECT TOP 1 * FROM c ORDER BY c.timestamp DESC"
```

또는 Azure Portal Data Explorer에서 확인:
1. Cosmos DB → Data Explorer
2. mystockdb → top_movers
3. Items → 최신 문서 확인

---

## 모니터링

### 1. 실시간 로그 스트리밍

```powershell
# 실시간 로그 확인
func azure functionapp logstream func-mystock-topmovers-dev
```

또는 Azure CLI:

```powershell
az webapp log tail `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev
```

### 2. Application Insights

**Azure Portal:**
1. Function App → Application Insights
2. Logs 탭에서 다음 쿼리 실행:

```kql
traces
| where cloud_RoleName == "func-mystock-topmovers-dev"
| where operation_Name == "top_movers_updater"
| order by timestamp desc
| take 50
```

**실행 성공/실패 통계:**

```kql
requests
| where cloud_RoleName == "func-mystock-topmovers-dev"
| summarize 
    SuccessCount = countif(success == true),
    FailureCount = countif(success == false),
    AvgDuration = avg(duration)
  by bin(timestamp, 1h)
| order by timestamp desc
```

### 3. Log Analytics

```powershell
# 최근 10건의 함수 실행 로그
az monitor log-analytics query `
  --workspace log-mystock-dev `
  --analytics-query "FunctionAppLogs | where FunctionName == 'top_movers_updater' | take 10"
```

### 4. Azure Portal 대시보드

**Function App Metrics:**
- Function Execution Count
- Function Execution Units
- Http Server Errors
- Average Memory Working Set

**설정 위치:** Function App → Monitoring → Metrics

---

## 트러블슈팅

### 1. 배포 실패: "Could not find function.json"

**원인:** Python v2 모델에서는 `function.json`이 필요 없지만, v1 모델 파일이 남아있을 수 있습니다.

**해결:**
```powershell
# TopMoversUpdater 폴더 삭제 (v2 모델에서는 불필요)
cd C:\Work\Azure\mystock\backend\functions
Remove-Item -Recurse -Force .\TopMoversUpdater -ErrorAction SilentlyContinue

# 재배포
func azure functionapp publish func-mystock-topmovers-dev --python
```

---

### 2. 함수 실행 실패: Cosmos DB 연결 오류

**증상:**
```
Unable to connect to Cosmos DB
```

**해결:**
```powershell
# Function App 설정 확인
az functionapp config appsettings list `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --query "[?name=='COSMOS_ENDPOINT' || name=='COSMOS_KEY']"

# 설정 업데이트
az functionapp config appsettings set `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --settings `
    COSMOS_ENDPOINT="https://cosmos-mystock-dev.documents.azure.com:443/" `
    COSMOS_KEY="YOUR_COSMOS_KEY"
```

---

### 3. Alpha Vantage API 제한

**증상:**
```
API note: Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute
```

**해결:**

Timer 스케줄을 6시간마다로 변경:

```python
# function_app.py
@app.timer_trigger(schedule="0 0 */6 * * *", ...)  # 6시간마다
```

재배포 필요.

---

### 4. 함수가 실행되지 않음

**확인 사항:**

```powershell
# Function App 상태
az functionapp show `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --query state

# Timer 트리거 상태 확인
az functionapp function show `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --function-name top_movers_updater `
  --query config.bindings
```

**재시작:**
```powershell
az functionapp restart `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev
```

---

### 5. 로그에 아무것도 표시되지 않음

**해결:**
```powershell
# Application Insights 연결 확인
az functionapp config appsettings list `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --query "[?name=='APPLICATIONINSIGHTS_CONNECTION_STRING']"

# 진단 설정 확인
az monitor diagnostic-settings show `
  --resource /subscriptions/.../resourceGroups/rg-mystock-dev/providers/Microsoft.Web/sites/func-mystock-topmovers-dev `
  --name functionapp-diagnostics
```

---

## 배포 체크리스트

### 배포 전

- [ ] Azure CLI 설치 및 로그인
- [ ] Functions Core Tools 설치
- [ ] 기존 인프라 배포 확인 (Cosmos DB, Log Analytics)
- [ ] Alpha Vantage API 키 준비
- [ ] `.env` 파일에서 환경 변수 확인

### 인프라 배포

- [ ] Bicep 템플릿으로 Functions 리소스 생성
- [ ] Function App 생성 확인
- [ ] Storage Account 생성 확인
- [ ] App Service Plan 생성 확인

### Functions 배포

- [ ] Python 의존성 설치
- [ ] Functions 코드 배포
- [ ] 배포 성공 확인

### 배포 후

- [ ] 함수 수동 실행 테스트
- [ ] Cosmos DB에 데이터 저장 확인
- [ ] Application Insights 로그 확인
- [ ] Timer 트리거 동작 확인 (1시간 대기 후)
- [ ] Backend API에서 데이터 조회 확인

---

## 참고 자료

- [Azure Functions Python Developer Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)
- [Azure Functions Consumption Plan](https://docs.microsoft.com/azure/azure-functions/consumption-plan)
- [Timer Trigger for Azure Functions](https://docs.microsoft.com/azure/azure-functions/functions-bindings-timer)
- [Azure Cosmos DB Python SDK](https://docs.microsoft.com/azure/cosmos-db/sql/sdk-python)

---

**마지막 업데이트:** 2025-10-26
