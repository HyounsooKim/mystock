# MyStock Azure 배포 가이드

## 현재 상태
✅ MySQL Flexible Server 생성 완료
⏳ App Service 생성 필요
⏳ Static Web App 생성 필요
⏳ 코드 배포 필요

---

## 1단계: 나머지 Azure 리소스 생성

### App Service 생성
```bash
# App Service Plan 생성
az appservice plan create \
    --resource-group mystock-mvp-rg \
    --name mystock-mvp-plan \
    --location koreacentral \
    --is-linux \
    --sku B1

# Web App 생성
az webapp create \
    --resource-group mystock-mvp-rg \
    --plan mystock-mvp-plan \
    --name mystock-mvp-api \
    --runtime "PYTHON:3.11"

# Always On 활성화
az webapp config set \
    --resource-group mystock-mvp-rg \
    --name mystock-mvp-api \
    --always-on true \
    --http20-enabled true \
    --min-tls-version 1.2
```

### 환경 변수 설정
```bash
# azure-credentials.txt에서 비밀번호 가져오기
MYSQL_PASSWORD=$(grep "MySQL Admin Password:" azure-credentials.txt | awk '{print $4}')

# 환경 변수 설정
az webapp config appsettings set \
    --resource-group mystock-mvp-rg \
    --name mystock-mvp-api \
    --settings \
        DATABASE_URL="mysql+pymysql://mystockadmin:${MYSQL_PASSWORD}@mystock-mvp-mysql.mysql.database.azure.com:3306/mystockdb?ssl_ca=/etc/ssl/certs/ca-certificates.crt" \
        JWT_SECRET="$(openssl rand -base64 32)" \
        JWT_ALGORITHM="HS256" \
        ACCESS_TOKEN_EXPIRE_MINUTES="1440" \
        DEBUG="False" \
        ENVIRONMENT="production" \
        ALLOWED_ORIGINS="http://localhost:5173,https://*.azurestaticapps.net"
```

---

## 2단계: Backend 배포

### 방법 A: ZIP 배포 (빠른 테스트)

```bash
cd backend

# 배포용 패키지 생성
zip -r ../backend-deploy.zip . \
    -x "*.pyc" \
    -x "__pycache__/*" \
    -x "venv/*" \
    -x "tests/*" \
    -x ".pytest_cache/*" \
    -x "*.db"

cd ..

# Azure에 배포
az webapp deploy \
    --resource-group mystock-mvp-rg \
    --name mystock-mvp-api \
    --src-path backend-deploy.zip \
    --type zip
```

### 방법 B: GitHub Actions (권장)

1. **Dockerfile 생성** (backend/Dockerfile)
2. **GitHub Secrets 설정**
3. **GitHub Actions Workflow 생성**

---

## 3단계: Database 마이그레이션

```bash
# Azure MySQL에 연결
mysql -h mystock-mvp-mysql.mysql.database.azure.com \
      -u mystockadmin \
      -p \
      mystockdb

# 또는 Alembic으로 마이그레이션
cd backend
export DATABASE_URL="mysql+pymysql://mystockadmin:PASSWORD@mystock-mvp-mysql.mysql.database.azure.com:3306/mystockdb?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
alembic upgrade head
```

---

## 4단계: Frontend 배포

### Static Web App 생성
```bash
# GitHub 저장소 URL 필요
az staticwebapp create \
    --resource-group mystock-mvp-rg \
    --name mystock-mvp-frontend \
    --location eastasia \
    --source https://github.com/YOUR_USERNAME/my_stock \
    --branch main \
    --app-location "/frontend" \
    --output-location "dist" \
    --login-with-github
```

### Frontend 환경 변수 설정

**frontend/.env.production** 파일 생성:
```env
VITE_API_BASE_URL=https://mystock-mvp-api.azurewebsites.net
```

---

## 5단계: CORS 설정

```bash
# Static Web App URL 가져오기
STATIC_URL=$(az staticwebapp show \
    --resource-group mystock-mvp-rg \
    --name mystock-mvp-frontend \
    --query defaultHostname -o tsv)

# App Service CORS 업데이트
az webapp config appsettings set \
    --resource-group mystock-mvp-rg \
    --name mystock-mvp-api \
    --settings ALLOWED_ORIGINS="https://${STATIC_URL},http://localhost:5173"
```

---

## 6단계: 배포 확인

### Health Check
```bash
curl https://mystock-mvp-api.azurewebsites.net/health
```

### 로그 확인
```bash
az webapp log tail \
    --resource-group mystock-mvp-rg \
    --name mystock-mvp-api
```

### Frontend 접속
```
https://YOUR_STATIC_APP.azurestaticapps.net
```

---

## 트러블슈팅

### 1. App Service 시작 실패
```bash
# 로그 확인
az webapp log tail --resource-group mystock-mvp-rg --name mystock-mvp-api

# SSH 접속
az webapp ssh --resource-group mystock-mvp-rg --name mystock-mvp-api
```

### 2. Database 연결 실패
- MySQL 방화벽 규칙 확인
- 연결 문자열 확인
- SSL 인증서 경로 확인

### 3. CORS 에러
```bash
# CORS 설정 확인
az webapp config appsettings list \
    --resource-group mystock-mvp-rg \
    --name mystock-mvp-api \
    --query "[?name=='ALLOWED_ORIGINS'].value" -o tsv
```

---

## 비용 모니터링

```bash
# 리소스 그룹 비용 확인
az consumption usage list \
    --start-date $(date -u -d '30 days ago' '+%Y-%m-%d') \
    --end-date $(date -u '+%Y-%m-%d') \
    --query "[?contains(instanceName, 'mystock-mvp')]"
```

---

## 리소스 삭제 (필요시)

```bash
# 전체 리소스 그룹 삭제
az group delete --name mystock-mvp-rg --yes --no-wait
```

---

## 다음 단계

1. ✅ MySQL 서버 생성 완료
2. ⏳ App Service 생성 및 배포
3. ⏳ Database 마이그레이션
4. ⏳ Static Web App 생성 및 배포
5. ⏳ GitHub Actions CI/CD 설정
6. ⏳ 모니터링 및 알람 설정
