# GitHub Actions CI/CD Pipelines

MyStock 프로젝트의 GitHub Actions 워크플로우 문서입니다.

## 📋 워크플로우 목록

### 1. Deploy Azure Functions (`deploy-functions.yml`)

**목적:** Azure Functions (Top Movers Updater)를 자동으로 배포합니다.

**트리거:**
- `backend/functions/**` 경로의 파일 변경 시
- `.github/workflows/deploy-functions.yml` 파일 변경 시
- 수동 실행 (`workflow_dispatch`)

**배포 대상:**
- Function App: `func-mystock-topmovers-dev`
- Runtime: Python 3.11
- Azure Functions v4

**단계:**
1. ✅ **코드 체크아웃**
2. ✅ **Python 3.11 설정**
3. ✅ **프로젝트 구조 검증** (function_app.py, host.json, requirements.txt)
4. ✅ **의존성 설치** (.python_packages/lib/site-packages)
5. ✅ **Azure Functions 배포** (Oryx 빌드 사용)
6. ✅ **배포 요약 출력** (URL, 다음 단계 안내)

---

### 2. Deploy Backend (`backend-deploy.yml`)

**목적:** FastAPI 백엔드를 Azure Container Apps에 배포합니다.

**트리거:**
- `backend/**` 경로의 파일 변경 시
- `main` 브랜치에 push

**배포 대상:**
- Azure Container Apps (Korea Central)

---

### 3. Deploy Frontend (`frontend-deploy.yml`)

**목적:** Vue.js 프론트엔드를 Azure Static Web Apps에 배포합니다.

**트리거:**
- `frontend/**` 경로의 파일 변경 시
- `main` 브랜치에 push

**배포 대상:**
- Azure Static Web Apps (East Asia)

---

## 🔧 초기 설정 (Functions 배포용)

### Step 1: Azure Function App 배포

먼저 Bicep을 통해 Function App을 생성해야 합니다:

```powershell
cd C:\Work\Azure\mystock\infra

# 전체 인프라 배포 (Functions 포함)
az deployment sub create `
  --location koreacentral `
  --template-file main.bicep `
  --parameters @parameters.dev.json
```

### Step 2: Publish Profile 가져오기

```powershell
# Function App의 Publish Profile 다운로드
az functionapp deployment list-publishing-profiles `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --xml
```

출력된 XML 전체를 복사합니다.

### Step 3: GitHub Secret 추가

1. GitHub 리포지토리 → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** 클릭
3. Secret 추가:
   - **Name:** `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
   - **Value:** (Step 2에서 복사한 XML 전체 붙여넣기)
4. **Add secret** 클릭

### Step 4: 워크플로우 권한 확인

1. GitHub 리포지토리 → **Settings** → **Actions** → **General**
2. **Workflow permissions** 섹션:
   - ✅ "Read and write permissions" 선택
   - ✅ "Allow GitHub Actions to create and approve pull requests" 체크
3. **Save** 클릭

---

## 🚀 사용 방법

### 자동 배포 (Push 트리거)

```powershell
# Functions 코드 수정
cd C:\Work\Azure\mystock\backend\functions
# (function_app.py 또는 requirements.txt 수정)

# Git commit & push
git add backend/functions/
git commit -m "Update Azure Functions: <변경 내용>"
git push origin main
```

**GitHub Actions가 자동으로:**
1. 코드 체크아웃
2. Python 환경 설정
3. 의존성 설치
4. Azure Functions에 배포
5. 배포 결과 출력

### 수동 배포 (Manual Trigger)

1. GitHub 리포지토리 → **Actions** 탭
2. **Deploy Azure Functions** 워크플로우 선택
3. **Run workflow** 버튼 클릭
4. Branch 선택 (기본: main)
5. **Run workflow** 확인

---

## 📊 배포 모니터링

### GitHub Actions 로그

1. GitHub 리포지토리 → **Actions** 탭
2. 실행 중인 워크플로우 클릭
3. 각 단계별 로그 확인

**주요 확인 포인트:**
- ✅ "Validate Function App Structure": 필수 파일 검증
- ✅ "Resolve Project Dependencies": pip 설치 로그
- ✅ "Run Azure Functions Action": 배포 진행 상황
- ✅ "Deployment Summary": 배포 완료 URL 및 다음 단계

### Azure Portal 확인

```powershell
# Function App 상태 확인
az functionapp show `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --query "{name:name, state:state, hostNames:hostNames}" `
  --output table
```

**Azure Portal:**
1. Function App → **Functions** → `top_movers_updater`
2. Status가 "Enabled"인지 확인
3. **Monitor** 탭에서 실행 로그 확인

---

## 🔍 트러블슈팅

### 1. 배포 실패: "Publish profile is invalid"

**원인:** `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` 시크릿이 없거나 잘못됨

**해결:**
```powershell
# 1. 새 Publish Profile 가져오기
az functionapp deployment list-publishing-profiles `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --xml

# 2. GitHub Secret 업데이트
# Settings → Secrets → AZURE_FUNCTIONAPP_PUBLISH_PROFILE → Update
```

---

### 2. 배포 실패: "function_app.py not found"

**원인:** 프로젝트 구조 검증 단계 실패

**해결:**
```powershell
# 필수 파일 확인
cd C:\Work\Azure\mystock\backend\functions
ls function_app.py, host.json, requirements.txt

# 파일이 없다면 생성 필요
```

---

### 3. 배포 성공했지만 함수가 실행되지 않음

**원인:** Azure Function App 설정 문제

**해결:**
```powershell
# Function App 환경 변수 확인
az functionapp config appsettings list `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --query "[?name=='COSMOS_ENDPOINT' || name=='ALPHA_VANTAGE_API_KEY']"

# 누락된 설정이 있다면 추가
az functionapp config appsettings set `
  --name func-mystock-topmovers-dev `
  --resource-group rg-mystock-dev `
  --settings `
    COSMOS_ENDPOINT="https://cosmos-mystock-dev.documents.azure.com:443/" `
    COSMOS_KEY="<your-key>" `
    ALPHA_VANTAGE_API_KEY="<your-key>"
```

---

### 4. Python 패키지 설치 오류

**증상:**
```
ERROR: Could not find a version that satisfies the requirement azure-cosmos>=4.5.0
```

**해결:**

`requirements.txt`에서 버전 확인:

```plaintext
azure-functions
azure-cosmos>=4.5.0
aiohttp>=3.9.0
python-dotenv>=1.0.0
```

또는 버전 제약 완화:

```plaintext
azure-functions
azure-cosmos
aiohttp
python-dotenv
```

---

### 5. Oryx 빌드 실패

**증상:**
```
Oryx build failed
```

**해결:**

`deploy-functions.yml`에서 빌드 설정 변경:

```yaml
- name: 'Run Azure Functions Action'
  uses: Azure/functions-action@v1
  with:
    app-name: ${{ env.AZURE_FUNCTIONAPP_NAME }}
    package: ${{ env.AZURE_FUNCTIONAPP_PACKAGE_PATH }}
    publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
    scm-do-build-during-deployment: true  # 변경
    enable-oryx-build: false              # 변경
```

---

## 📋 배포 체크리스트

### 첫 배포 전

- [ ] Azure Function App 생성 (Bicep 배포)
- [ ] Publish Profile 가져오기
- [ ] GitHub Secret 추가 (`AZURE_FUNCTIONAPP_PUBLISH_PROFILE`)
- [ ] Workflow permissions 설정 (Read and write)
- [ ] `.funcignore` 파일 확인

### 배포 후

- [ ] GitHub Actions 로그 확인 (모든 단계 성공)
- [ ] Azure Portal에서 Function App 상태 확인
- [ ] Functions → top_movers_updater 활성화 확인
- [ ] Application Insights 로그 확인
- [ ] 수동 트리거로 함수 실행 테스트
- [ ] Cosmos DB에 데이터 저장 확인

---

## 📚 참고 자료

- [Azure Functions GitHub Actions](https://github.com/Azure/functions-action)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Functions Python Developer Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)

---

**마지막 업데이트:** 2025-10-27
