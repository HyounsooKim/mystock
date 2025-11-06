# Azure Function App 보안 설정 가이드

## 개요

Azure Function App `func-mystock-topmovers-dev`에 대한 키리스 보안 설정 구현 문서입니다.
이 문서는 로컬 인증(키/기본 인증) 비활성화 및 Azure AD 기반 인증 전환을 다룹니다.

## 변경 사항 요약

### 1. 기본 인증 비활성화

#### FTP 기본 인증
- **상태**: ✅ 비활성화됨
- **설정**: `ftpsState: 'Disabled'`
- **영향**: FTP를 통한 파일 전송 불가

#### SCM (Kudu) 기본 인증
- **상태**: ✅ 비활성화됨
- **설정**: `basicPublishingCredentialsPolicies/scm` = `false`
- **영향**: 기본 인증으로 Kudu/SCM 접근 불가

### 2. 관리형 ID (Managed Identity) 활성화

#### 시스템 할당 관리형 ID
- **타입**: System-Assigned Managed Identity
- **용도**: Azure 리소스 간 인증 (Cosmos DB, Key Vault 등)
- **장점**:
  - 자격증명 관리 불필요
  - 자동 생명주기 관리
  - 키 유출 위험 제거

### 3. Cosmos DB RBAC 접근 제어

#### 역할 할당
- **역할**: Cosmos DB Built-in Data Contributor
- **역할 ID**: `00000000-0000-0000-0000-000000000002`
- **범위**: Cosmos DB 계정 전체
- **주체**: Function App의 시스템 할당 관리형 ID

#### 권한
- 데이터 읽기/쓰기
- 컨테이너 생성
- 저장 프로시저 실행

## 인프라 코드 변경 사항

### 1. functions.bicep

```bicep
// 시스템 할당 관리형 ID 추가
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  identity: {
    type: 'SystemAssigned'
  }
  // ...
}

// FTP 기본 인증 비활성화
resource functionAppFtpBasicAuth 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-01-01' = {
  name: 'ftp'
  parent: functionApp
  properties: {
    allow: false
  }
}

// SCM 기본 인증 비활성화
resource functionAppScmBasicAuth 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-01-01' = {
  name: 'scm'
  parent: functionApp
  properties: {
    allow: false
  }
}
```

### 2. cosmosdb-role-assignment.bicep (신규)

```bicep
// Cosmos DB SQL Role Assignment
resource roleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-04-15' = {
  name: guid(cosmosAccount.id, principalId, roleDefinitionId)
  parent: cosmosAccount
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/${roleDefinitionId}'
    principalId: principalId
    scope: cosmosAccount.id
  }
}
```

### 3. main.bicep

```bicep
// Cosmos DB 역할 할당 모듈 추가
module cosmosRoleAssignment 'modules/cosmosdb-role-assignment.bicep' = {
  name: 'cosmosdb-role-assignment'
  scope: rg
  params: {
    cosmosAccountName: cosmosDb.outputs.accountName
    roleDefinitionId: '00000000-0000-0000-0000-000000000002'
    principalId: functions.outputs.functionAppPrincipalId
  }
}
```

### 4. Function App 코드 변경

#### function_app.py

```python
# 관리형 ID를 위한 라이브러리 추가
from azure.identity import DefaultAzureCredential

def save_to_cosmos(data: dict):
    """Save top movers data to Cosmos DB using Managed Identity."""
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    database_name = os.environ.get("COSMOS_DATABASE_NAME")
    
    # DefaultAzureCredential 사용 (관리형 ID 자동 인식)
    credential = DefaultAzureCredential()
    
    # 로컬 개발 시에는 COSMOS_KEY 환경변수 사용 가능
    if "localhost" in endpoint:
        key = os.environ.get("COSMOS_KEY")
        if key:
            credential = key
    
    client = CosmosClient(
        url=endpoint,
        credential=credential,
        connection_verify=True
    )
```

#### requirements.txt

```txt
azure-functions
azure-cosmos>=4.5.0
azure-identity>=1.15.0  # 관리형 ID 지원
aiohttp>=3.9.0
python-dotenv>=1.0.0
```

**주요 변경점:**
- ✅ `COSMOS_KEY` 환경변수 제거 (Azure 배포 시)
- ✅ `DefaultAzureCredential` 사용으로 자동 인증
- ✅ 로컬 개발 시 key-based auth 폴백 지원

## 배포 방법

### 옵션 1: Bicep 템플릿으로 전체 배포 (권장)

```bash
az deployment sub create \
  --location koreacentral \
  --template-file infra/main.bicep \
  --parameters \
    environmentName=dev \
    appName=mystock \
    githubRepoUrl="HyounsooKim/mystock" \
    githubBranch=main \
    alphaVantageApiKey="<your-api-key>" \
    jwtSecretKey="<your-jwt-secret>"
```

### 옵션 2: Functions 모듈만 재배포

```bash
az deployment group create \
  --resource-group rg-mystock-dev \
  --template-file infra/modules/functions.bicep \
  --parameters @infra/params.dev.json
```

### 옵션 3: GitHub Actions 자동 배포

1. 코드 변경 커밋
2. `main` 브랜치에 푸시
3. GitHub Actions가 자동으로 배포 실행

## 배포 후 확인 사항

### 1. 관리형 ID 확인

```bash
# Function App의 Principal ID 확인
az functionapp identity show \
  --name func-mystock-topmovers-dev \
  --resource-group rg-mystock-dev \
  --query principalId -o tsv
```

### 2. 기본 인증 비활성화 확인

```bash
# FTP 기본 인증 상태
az functionapp config show \
  --name func-mystock-topmovers-dev \
  --resource-group rg-mystock-dev \
  --query ftpsState

# SCM 기본 인증 상태
az resource show \
  --ids "/subscriptions/<subscription-id>/resourceGroups/rg-mystock-dev/providers/Microsoft.Web/sites/func-mystock-topmovers-dev/basicPublishingCredentialsPolicies/scm" \
  --query properties.allow
```

### 3. Cosmos DB 역할 할당 확인

```bash
# SQL Role Assignments 목록
az cosmosdb sql role assignment list \
  --account-name cosmos-mystock-dev \
  --resource-group rg-mystock-dev
```

### 4. Function 실행 테스트

```bash
# 함수 수동 트리거
az functionapp function invoke \
  --name func-mystock-topmovers-dev \
  --resource-group rg-mystock-dev \
  --function-name top_movers_updater
```

## 보안 개선 효과

### 이전 (키 기반 인증)

```
❌ 위험 요소:
- Function Keys 유출 시 무제한 접근 가능
- 기본 인증 자격증명 노출 위험
- SCM/Kudu 접근 시 키 필요
- 키 회전 수동 관리
- 접근 감사 추적 어려움
```

### 이후 (RBAC 기반 인증)

```
✅ 보안 향상:
- Azure AD 기반 인증 (조건부 접근, MFA)
- 관리형 ID로 키 관리 불필요
- RBAC 권한으로 최소 권한 원칙 적용
- SCM 접근도 Azure AD 인증 필요
- 모든 접근 Azure Activity Log에 기록
```

## 영향 받는 시나리오 및 대안

### 1. ❌ 로컬 개발에서 Kudu/SCM 접근

**이전 방법:**
```bash
# 기본 인증 사용
https://username:password@func-mystock-topmovers-dev.scm.azurewebsites.net
```

**새로운 방법:**
```bash
# Azure CLI로 로그인 후 접근
az login
az webapp browse --name func-mystock-topmovers-dev --resource-group rg-mystock-dev --scm
```

### 2. ❌ Function Keys로 함수 호출

**이전 방법:**
```bash
curl "https://func-mystock-topmovers-dev.azurewebsites.net/api/function?code=<function-key>"
```

**새로운 방법:**
Timer trigger 함수는 외부 호출이 필요 없으므로 Function Keys 사용하지 않음.
테스트 시에는 Azure Portal 또는 Azure CLI 사용.

### 3. ✅ GitHub Actions 배포

**이전 방법:**
```yaml
- uses: Azure/functions-action@v1
  with:
    publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

**새로운 방법:**
```yaml
- uses: azure/login@v1
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}

- uses: Azure/functions-action@v1
  with:
    app-name: func-mystock-topmovers-dev
    # publish-profile 없이 Azure 인증 사용
```

## 롤백 절차

보안 설정으로 인해 문제가 발생할 경우, 임시로 기본 인증을 재활성화할 수 있습니다:

### 1. SCM 기본 인증 재활성화

```bash
az resource update \
  --ids "/subscriptions/<subscription-id>/resourceGroups/rg-mystock-dev/providers/Microsoft.Web/sites/func-mystock-topmovers-dev/basicPublishingCredentialsPolicies/scm" \
  --set properties.allow=true
```

### 2. FTP 기본 인증 재활성화

```bash
az functionapp config set \
  --name func-mystock-topmovers-dev \
  --resource-group rg-mystock-dev \
  --ftps-state FtpsOnly
```

**⚠️ 주의**: 롤백은 임시 조치이며, 근본 원인을 해결한 후 다시 비활성화해야 합니다.

## 규정 준수

이 보안 설정은 다음 표준을 준수합니다:

- ✅ **CIS Azure Foundations Benchmark**: 9.10 - Ensure FTP deployments are disabled
- ✅ **Azure Security Baseline**: Use Azure Active Directory for authentication
- ✅ **NIST Cybersecurity Framework**: PR.AC-1 - Identity and credential management
- ✅ **ISO 27001**: A.9.2.1 - User registration and de-registration

## 모니터링 및 경보

### 1. 인증 실패 경보 설정

```bash
az monitor metrics alert create \
  --name "Function-Auth-Failures" \
  --resource-group rg-mystock-dev \
  --scopes "/subscriptions/.../providers/Microsoft.Web/sites/func-mystock-topmovers-dev" \
  --condition "count Http401 > 10" \
  --window-size 5m \
  --evaluation-frequency 1m
```

### 2. Log Analytics 쿼리

```kql
// 인증 실패 추적
AzureDiagnostics
| where ResourceType == "SITES"
| where Category == "FunctionAppLogs"
| where ResultCode == 401 or ResultCode == 403
| summarize count() by bin(TimeGenerated, 1h), ResultCode
| order by TimeGenerated desc
```

## 참고 자료

- [Azure Functions 보안](https://docs.microsoft.com/azure/azure-functions/security-concepts)
- [Cosmos DB RBAC](https://docs.microsoft.com/azure/cosmos-db/role-based-access-control)
- [관리형 ID 개요](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
- [Azure App Service 보안 권장 사항](https://docs.microsoft.com/azure/app-service/security-recommendations)

## 완료 기준 (DoD)

- [x] FTP 기본 인증 비활성화 구성 완료
- [x] SCM 기본 인증 비활성화 구성 완료
- [x] 시스템 할당 관리형 ID 활성화
- [x] Cosmos DB RBAC 역할 할당 구성
- [x] GitHub Actions 워크플로우 RBAC 배포로 전환
- [x] Bicep 템플릿 검증 통과
- [x] 보안 설정 문서화 완료
- [ ] 스테이징 환경에서 배포 테스트
- [ ] 프로덕션 환경에 배포
- [ ] 배포 후 함수 정상 동작 확인
- [ ] 모니터링 경보 설정
- [ ] 운영 문서 업데이트

---

**작성일**: 2025-11-06  
**작성자**: GitHub Copilot  
**추적 이슈**: [보안] Azure Function App 로컬 인증(키/기본 인증) 비활성화 필요
