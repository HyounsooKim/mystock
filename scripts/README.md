# MyStock Deployment Scripts

이 디렉토리는 MyStock 애플리케이션을 Azure에 배포하기 위한 스크립트를 포함합니다.

## 📁 파일 구조

```
scripts/
├── provision-azure-mvp.sh    # Azure 리소스 생성 스크립트
├── deploy-backend.sh          # Backend API 배포 스크립트 (예정)
├── deploy-frontend.sh         # Frontend 배포 스크립트 (예정)
└── README.md                  # 이 파일
```

## 🚀 Quick Start

### 1. Azure 리소스 프로비저닝

```bash
# 스크립트 실행 권한 부여
chmod +x scripts/provision-azure-mvp.sh

# 스크립트 실행
./scripts/provision-azure-mvp.sh
```

### 2. 생성되는 리소스

| 리소스 | SKU | 월 비용 |
|--------|-----|---------|
| Static Web Apps | Free | $0 |
| App Service | B1 | $13.14 |
| MySQL Flexible Server | B1ms | $12.41 |
| **합계** | | **~$25.55** |

### 3. 사전 요구사항

#### Azure CLI 설치
```bash
# macOS
brew install azure-cli

# 버전 확인
az --version

# Azure 로그인
az login
```

#### 필수 정보
- Azure 구독 (활성화된 상태)
- GitHub 리포지토리 URL (Static Web Apps용)

## 📋 프로비저닝 프로세스

### Step 1: 사전 검사
- Azure CLI 설치 확인
- Azure 로그인 상태 확인
- 구독 정보 확인

### Step 2: 사용자 확인
- 생성될 리소스 목록 표시
- 예상 비용 표시
- 사용자 확인 대기

### Step 3: 리소스 생성
1. **Resource Group** 생성
   - Name: `mystock-mvp-rg`
   - Location: Korea Central

2. **MySQL Flexible Server** 생성 (5-10분 소요)
   - SKU: Standard_B1ms (1 vCore, 2GB RAM)
   - Storage: 20GB
   - Database: `mystockdb`
   - 보안 암호 자동 생성

3. **App Service** 생성
   - Plan: B1 (Basic)
   - Runtime: Python 3.11
   - Always On 활성화
   - 환경 변수 자동 설정

4. **Static Web App** 생성 (선택사항)
   - GitHub 연동 필요
   - 자동 CI/CD 설정

### Step 4: 결과 저장
생성된 파일:
- `azure-credentials.txt` - 비밀번호 및 토큰 (⚠️ Git에 커밋 금지!)
- `azure-deployment-info.md` - 배포 정보 문서

## 🔒 보안 관련

### 중요 파일 보호
```bash
# .gitignore에 추가
echo "azure-credentials.txt" >> .gitignore
echo "scripts/*.log" >> .gitignore
```

### 생성된 비밀번호
- MySQL Admin Password (32자 랜덤)
- JWT Secret (32자 랜덤)
- Static Web App Token (Azure 생성)

모든 비밀번호는 `azure-credentials.txt`에 저장됩니다.

## 📊 생성 후 확인

### Azure Portal에서 확인
```bash
# 브라우저에서 Azure Portal 열기
open https://portal.azure.com

# Resource Group 검색: mystock-mvp-rg
```

### CLI로 리소스 확인
```bash
# 모든 리소스 목록
az resource list --resource-group mystock-mvp-rg --output table

# App Service 상태
az webapp show --resource-group mystock-mvp-rg --name mystock-mvp-api --query state

# MySQL 서버 상태
az mysql flexible-server show --resource-group mystock-mvp-rg --name mystock-mvp-mysql --query state
```

### 헬스 체크
```bash
# Backend API Health Check
curl https://mystock-mvp-api.azurewebsites.net/health

# Frontend 확인
curl https://YOUR-STATIC-WEB-APP.azurestaticapps.net
```

## 🛠️ 문제 해결

### 스크립트 실행 오류

#### 1. Azure CLI 인증 만료
```bash
az login
az account show
```

#### 2. 권한 부족
```bash
# 현재 계정의 역할 확인
az role assignment list --assignee $(az account show --query user.name -o tsv)

# Contributor 역할 필요
```

#### 3. 리소스 이름 중복
```bash
# 스크립트에서 PROJECT_NAME 변경
# 또는 기존 리소스 삭제
az group delete --name mystock-mvp-rg --yes
```

### MySQL 연결 실패

#### 방화벽 규칙 확인
```bash
az mysql flexible-server firewall-rule list \
  --resource-group mystock-mvp-rg \
  --name mystock-mvp-mysql \
  --output table
```

#### 로컬에서 연결 테스트
```bash
# 본인 IP 추가
MY_IP=$(curl -s ifconfig.me)
az mysql flexible-server firewall-rule create \
  --resource-group mystock-mvp-rg \
  --name mystock-mvp-mysql \
  --rule-name AllowMyIP \
  --start-ip-address $MY_IP \
  --end-ip-address $MY_IP

# 연결 테스트
mysql -h mystock-mvp-mysql.mysql.database.azure.com \
      -u mystockadmin \
      -p \
      mystockdb
```

### App Service 배포 실패

#### 로그 확인
```bash
# 실시간 로그 스트리밍
az webapp log tail --resource-group mystock-mvp-rg --name mystock-mvp-api

# 로그 다운로드
az webapp log download --resource-group mystock-mvp-rg --name mystock-mvp-api
```

#### 환경 변수 확인
```bash
az webapp config appsettings list \
  --resource-group mystock-mvp-rg \
  --name mystock-mvp-api \
  --output table
```

## 🗑️ 리소스 삭제

### 전체 삭제 (주의!)
```bash
# Resource Group 삭제 (모든 리소스 포함)
az group delete --name mystock-mvp-rg --yes --no-wait

# 삭제 상태 확인
az group exists --name mystock-mvp-rg
```

### 개별 리소스 삭제
```bash
# App Service만 삭제
az webapp delete --resource-group mystock-mvp-rg --name mystock-mvp-api

# MySQL만 삭제
az mysql flexible-server delete --resource-group mystock-mvp-rg --name mystock-mvp-mysql --yes

# Static Web App만 삭제
az staticwebapp delete --resource-group mystock-mvp-rg --name mystock-mvp-frontend --yes
```

## 📚 참고 자료

### Azure 문서
- [Azure App Service](https://docs.microsoft.com/azure/app-service/)
- [Azure Database for MySQL](https://docs.microsoft.com/azure/mysql/)
- [Azure Static Web Apps](https://docs.microsoft.com/azure/static-web-apps/)

### Azure CLI 참조
- [az webapp](https://docs.microsoft.com/cli/azure/webapp)
- [az mysql flexible-server](https://docs.microsoft.com/cli/azure/mysql/flexible-server)
- [az staticwebapp](https://docs.microsoft.com/cli/azure/staticwebapp)

## 🤝 지원

문제가 발생하면 다음을 확인하세요:
1. Azure Portal에서 리소스 상태 확인
2. `az webapp log tail`로 실시간 로그 확인
3. `azure-deployment-info.md` 파일의 관리 명령어 참조

## 📝 다음 단계

리소스 프로비저닝 완료 후:

1. ✅ `azure-credentials.txt`를 `.gitignore`에 추가
2. ⏳ GitHub Actions 설정 (`.github/workflows/`)
3. ⏳ Backend Dockerfile 작성
4. ⏳ Frontend 환경 변수 설정 (.env.production)
5. ⏳ 데이터베이스 마이그레이션 실행
6. ⏳ 첫 배포 수행
