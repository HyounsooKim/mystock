# Azure 배포 가이드

MyStock 애플리케이션을 Azure에 배포하는 전체 과정을 설명합니다.

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [아키텍처 개요](#아키텍처-개요)
3. [비용 예측](#비용-예측)
4. [초기 인프라 배포](#초기-인프라-배포)
5. [GitHub Actions 설정](#github-actions-설정)
6. [배포 확인](#배포-확인)
7. [모니터링 및 로그](#모니터링-및-로그)
8. [트러블슈팅](#트러블슈팅)

---

## 사전 요구사항

### 필수 도구
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) (v2.50+)
- [Git](https://git-scm.com/)
- Azure 구독 (Owner 또는 Contributor 권한)
- [PowerShell](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell) (Windows) 또는 Bash (Linux/Mac)

### API 키 준비
- **Alpha Vantage API Key**: [무료 발급](https://www.alphavantage.co/support/#api-key)
  - 월 25 API calls/day (Free tier)
  - Premium tier 사용 시 더 많은 요청 가능
- **JWT Secret Key**: 자동 생성됨 (또는 직접 설정 가능)

---

## 아키텍처 개요

```
┌────────────────────────────────────────────────────────┐
│ GitHub Repository                                      │
│ ├─ frontend/ → GitHub Actions → Static Web App         │
│ └─ backend/  → GitHub Actions → Container Apps         │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ Azure Resources                                        │
│                                                        │
│ ┌─────────────────┐  ┌──────────────────┐              │
│ │ Static Web App  │→ │ Container Apps   │              │
│ │ (East Asia)     │  │ (Korea Central)  │              │
│ │ Free SKU        │  │ Consumption      │              │
│ └─────────────────┘  └──────────────────┘              │
│          ↓                    ↓                        │
│ ┌──────────────────────────────────────┐               │
│ │ Cosmos DB (Korea Central)            │               │
│ │ Serverless NoSQL API                 │               │
│ └──────────────────────────────────────┘               │
│                                                        │
│ ┌──────────────────────────────────────┐               │
│ │ Container Registry (Korea Central)   │               │
│ │ Docker 이미지 저장소                 │               │
│ └──────────────────────────────────────┘               │
│                                                        │
│ ┌──────────────────────────────────────┐               │
│ │ Log Analytics + App Insights         │               │
│ │ (Korea Central)                      │               │
│ └──────────────────────────────────────┘               │
└────────────────────────────────────────────────────────┘
```

### 주요 리소스

| 리소스 | SKU/Tier | 리전 | 용도 | 예상 비용 |
|--------|----------|------|------|-----------|
| **Static Web App** | Free | East Asia | 프론트엔드 호스팅 (Vue.js) | $0 |
| **Container Apps** | Consumption | Korea Central | 백엔드 API (FastAPI) | ~$5-10/월 |
| **Cosmos DB** | Serverless | Korea Central | NoSQL 데이터베이스 | ~$1-5/월 |
| **Container Registry** | Basic | Korea Central | Docker 이미지 저장 | ~$5/월 |
| **Log Analytics** | Pay-per-GB | Korea Central | 로그 수집 및 분석 | ~$2-5/월 |
| **Total** | - | - | - | **~$13-30/월** |

> **참고**: Static Web App은 Korea Central을 지원하지 않아 East Asia로 배포됩니다.

---

## 비용 예측

### 예상 월간 비용 (개발 환경 기준)

**Static Web App (Free tier)**
- 100 GB 대역폭/월
- 커스텀 도메인 지원 (무료 SSL 포함)
- **비용: $0**

**Container Apps (Consumption)**
- 0.25 vCPU, 512 MB 메모리
- Min replicas: 1, Max replicas: 2
- 월 10,000 요청 가정
- **비용: ~$5-10/월**

**Cosmos DB (Serverless)**
- 1 GB 스토리지
- 월 50,000 RU (Request Units)
- **비용: ~$1-5/월**

**Container Registry (Basic)**
- 10 GB 스토리지
- **비용: ~$5/월**

**Log Analytics Workspace**
- 1 GB 데이터 수집/월
- 31일 보관
- **비용: ~$2-5/월**

**총 예상 비용: $13-30/월**

> 💡 **비용 절감 팁**: 
> - Container Apps의 min replicas를 0으로 설정하면 비용 절감 가능 (단, 콜드 스타트 발생)
> - Cosmos DB는 사용한 RU만큼만 과금 (Serverless)
> - 개발 환경에서는 Log Analytics 보관 기간을 7일로 축소 가능

---

## 초기 인프라 배포

### 1. Azure CLI 로그인

```powershell
# PowerShell
az login

# 구독 선택 (여러 개인 경우)
az account list --output table
az account set --subscription "<your-subscription-id>"
```

### 2. 환경 변수 설정

```powershell
# PowerShell
$env:ALPHA_VANTAGE_API_KEY = "your-alpha-vantage-api-key"
```

```bash
# Bash
export ALPHA_VANTAGE_API_KEY="your-alpha-vantage-api-key"
```

### 3. Bicep 템플릿으로 인프라 배포

```powershell
# PowerShell
cd infra
.\deploy.ps1
```

```bash
# Bash
cd infra
./deploy.sh
```

배포 스크립트는 다음 리소스를 자동으로 생성합니다:

1. **Resource Group**: `rg-mystock-dev`
2. **Log Analytics Workspace**: 모니터링 및 로그 수집
3. **Cosmos DB Account**: NoSQL 데이터베이스 (Serverless)
   - Database: `mystockdb`
   - Container: `users` (partition key: `/id`)
4. **Container Apps Environment**: 백엔드 런타임 환경
5. **Container Registry**: Docker 이미지 저장소
6. **Container App**: 백엔드 API 서버
7. **Static Web App**: 프론트엔드 호스팅

### 4. 배포 완료 확인

배포가 완료되면 다음 정보가 출력됩니다:

```
Deployment completed successfully!

Resource Group: rg-mystock-dev
Backend URL: https://ca-mystock-backend-dev.whitemeadow-xxxxx.koreacentral.azurecontainerapps.io
Frontend URL: https://gray-beach-xxxxx.3.azurestaticapps.net
Cosmos DB Endpoint: https://cosmos-mystock-dev-koreacentral.documents.azure.com:443/
Container Registry: crmystockdev.azurecr.io
```

---

## GitHub Actions 설정

### 1. GitHub Secrets 구성

GitHub 저장소 → Settings → Secrets and variables → Actions에서 다음 secrets를 추가합니다:

#### 필수 Secrets

| Secret 이름 | 설명 | 예시 값 |
|------------|------|---------|
| `AZURE_CREDENTIALS` | Azure Service Principal JSON | `{"clientId":"...","clientSecret":"...","subscriptionId":"...","tenantId":"..."}` |
| `AZURE_CONTAINER_REGISTRY_NAME` | ACR 이름 | `crmystockdev` |
| `AZURE_CONTAINER_REGISTRY_USERNAME` | ACR 사용자명 | (Azure Portal에서 확인) |
| `AZURE_CONTAINER_REGISTRY_PASSWORD` | ACR 비밀번호 | (Azure Portal에서 확인) |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | SWA API 토큰 | (Azure Portal에서 확인) |
| `VITE_API_BASE_URL` | 백엔드 API URL | `https://ca-mystock-backend-dev.whitemeadow-xxxxx.koreacentral.azurecontainerapps.io/api/v1` |

#### Service Principal 생성

```powershell
# Azure CLI로 Service Principal 생성
az ad sp create-for-rbac --name "mystock-github-actions" --role contributor `
    --scopes /subscriptions/<subscription-id>/resourceGroups/rg-mystock-dev `
    --sdk-auth

# 출력된 JSON을 AZURE_CREDENTIALS에 저장
```

#### ACR 자격 증명 확인

```powershell
# ACR 관리자 활성화 (이미 활성화됨)
az acr update --name crmystockdev --admin-enabled true

# 자격 증명 조회
az acr credential show --name crmystockdev
```

#### Static Web App API 토큰 확인

```powershell
# Azure Portal에서 확인
# Static Web Apps → 설정 → 구성 → Deployment token 복사
# 또는 CLI로 조회
az staticwebapp secrets list --name swa-mystock-dev --resource-group rg-mystock-dev
```

### 2. GitHub Actions 워크플로우

워크플로우는 이미 `.github/workflows/` 디렉토리에 구성되어 있습니다:

- **`backend-deploy.yml`**: 백엔드 Docker 이미지 빌드 및 Container Apps 배포
- **`frontend-deploy.yml`**: 프론트엔드 Vite 빌드 및 Static Web Apps 배포

### 3. 자동 배포 트리거

코드를 `AlphaVantage_v1` 또는 `main` 브랜치에 푸시하면 자동으로 배포됩니다:

```powershell
git add .
git commit -m "Deploy to Azure"
git push origin AlphaVantage_v1
```

GitHub Actions 탭에서 배포 진행 상황을 확인할 수 있습니다.

---

## 배포 확인

### 1. 프론트엔드 확인

브라우저에서 접속:
- **커스텀 도메인**: `https://stock.yourdomain.com`
- **기본 도메인**: `https://gray-beach-xxxxx.3.azurestaticapps.net`

### 2. 백엔드 API 확인

```powershell
# Health check
curl https://ca-mystock-backend-dev.whitemeadow-xxxxx.koreacentral.azurecontainerapps.io/api/v1/health

# Swagger 문서
# 브라우저에서 열기
start https://ca-mystock-backend-dev.whitemeadow-xxxxx.koreacentral.azurecontainerapps.io/docs
```

### 3. Cosmos DB 데이터 확인

```powershell
# Azure Portal에서 Data Explorer 사용
# 또는 CLI로 조회
az cosmosdb sql database show --account-name cosmos-mystock-dev-koreacentral `
    --resource-group rg-mystock-dev --name mystockdb
```

---

## 모니터링 및 로그

### 1. Container Apps 로그 조회

```powershell
# 실시간 로그 스트리밍
az containerapp logs show --name ca-mystock-backend-dev `
    --resource-group rg-mystock-dev --follow

# 최근 100줄 로그
az containerapp logs show --name ca-mystock-backend-dev `
    --resource-group rg-mystock-dev --tail 100
```

### 2. Log Analytics 쿼리

```powershell
# Log Analytics Workspace ID 확인
az monitor log-analytics workspace show `
    --resource-group rg-mystock-dev `
    --workspace-name law-mystock-dev `
    --query customerId -o tsv

# 쿼리 예시: 최근 에러 로그
$workspaceId = "workspace-id"
az monitor log-analytics query --workspace $workspaceId `
    --analytics-query "ContainerAppConsoleLogs_CL | where Log_s contains 'ERROR' | order by TimeGenerated desc | take 50"
```

### 3. 일반적인 Log Analytics 쿼리

**에러 로그 조회:**
```kusto
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == 'ca-mystock-backend-dev'
| where Log_s contains 'ERROR' or Log_s contains 'Exception'
| project TimeGenerated, Log_s
| order by TimeGenerated desc
| take 50
```

**특정 API 엔드포인트 호출 로그:**
```kusto
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == 'ca-mystock-backend-dev'
| where Log_s contains 'POST /api/v1/auth/register'
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

**성능 모니터링:**
```kusto
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == 'ca-mystock-backend-dev'
| where Log_s contains 'HTTP/1.1'
| project TimeGenerated, Log_s
| order by TimeGenerated desc
| take 100
```

---

## 트러블슈팅


### 1. 프론트엔드에서 API 호출시 404 에러날 경우,

**증상**: 프론트엔드에서 API 호출 시 404 Not Found

**원인**: `VITE_API_BASE_URL` 환경변수가 `/api/v1` 경로를 포함하지 않음

**해결**:
GitHub Secrets의 `VITE_API_BASE_URL`을 다음과 같이 설정:
```
https://ca-mystock-backend-dev.whitemeadow-xxxxx.koreacentral.azurecontainerapps.io/api/v1
```

---

## 유용한 명령어 모음

### 리소스 상태 확인
```powershell
# 전체 리소스 그룹 조회
az group show --name rg-mystock-dev

# Container App 상태
az containerapp show --name ca-mystock-backend-dev --resource-group rg-mystock-dev

# Static Web App 상태  
az staticwebapp show --name swa-mystock-dev --resource-group rg-mystock-dev

# Cosmos DB 상태
az cosmosdb show --name cosmos-mystock-dev-koreacentral --resource-group rg-mystock-dev
```

### 리소스 재시작
```powershell
# Container App 재시작
az containerapp revision restart --name ca-mystock-backend-dev `
    --resource-group rg-mystock-dev `
    --revision <revision-name>
```

### 비용 확인
```powershell
# 리소스 그룹 비용 조회 (Azure Portal에서 더 자세히 확인 가능)
az consumption usage list --resource-group rg-mystock-dev
```

### 리소스 삭제
```powershell
# 전체 리소스 그룹 삭제 (주의!)
az group delete --name rg-mystock-dev --yes --no-wait
```

---

## 참고 자료

- [Azure Container Apps 문서](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Static Web Apps 문서](https://learn.microsoft.com/en-us/azure/static-web-apps/)
- [Azure Cosmos DB 문서](https://learn.microsoft.com/en-us/azure/cosmos-db/)
- [Bicep 문서](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [GitHub Actions 문서](https://docs.github.com/en/actions)

---

**작성일**: 2025년 10월 22일  
**버전**: 1.0.0  
**환경**: Azure Korea Central, Container Apps (Consumption), Cosmos DB (Serverless)
