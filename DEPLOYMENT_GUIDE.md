# Azure 배포 가이드

이 문서는 MyStock 애플리케이션을 Azure에 배포하는 전체 과정을 설명합니다.

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

### API 키 준비
- **Alpha Vantage API Key**: [무료 발급](https://www.alphavantage.co/support/#api-key)
- **JWT Secret Key**: 자동 생성됨 (또는 직접 설정 가능)

---

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────┐
│ GitHub Repository                                        │
│ ├─ frontend/ → GitHub Actions → Static Web App         │
│ └─ backend/  → GitHub Actions → Container Apps         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Azure Resources (Korea Central)                         │
│                                                          │
│ ┌─────────────────┐  ┌──────────────────┐              │
│ │ Static Web App  │→ │ Container Apps   │              │
│ │ (Free SKU)      │  │ (Consumption)    │              │
│ └─────────────────┘  └──────────────────┘              │
│          ↓                    ↓                         │
│ ┌──────────────────────────────────────┐               │
│ │ Cosmos DB (Serverless NoSQL)         │               │
│ └──────────────────────────────────────┘               │
│                                                          │
│ ┌──────────────────────────────────────┐               │
│ │ Log Analytics + App Insights         │               │
│ └──────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

### 주요 리소스

| 리소스 | SKU/Tier | 용도 | 예상 비용 |
|--------|----------|------|-----------|
| **Static Web App** | Free | 프론트엔드 호스팅 | $0 |
| **Container Apps** | Consumption | 백엔드 API | ~$0-10/월 |
| **Cosmos DB** | Serverless | NoSQL 데이터베이스 | ~$1-5/월 |
| **Container Registry** | Basic | Docker 이미지 저장 | ~$5/월 |
| **Log Analytics** | Pay-per-GB | 로그 수집 | ~$2-5/월 |
| **Total** | - | - | **~$8-25/월** |

---

## 비용 예측

### 예상 월간 비용 (MVP 수준 트래픽 기준)

**Static Web App (Free tier)**
- 100 GB 대역폭/월
- 커스텀 도메인 지원
- **비용: $0**

**Container Apps (Consumption)**
- 0.25 vCPU, 512 MB 메모리
- Scale to Zero (사용하지 않을 때 과금 없음)
- 월 1,000 요청 가정
- **비용: ~$0-10/월**

**Cosmos DB (Serverless)**
- 1 GB 스토리지
- 월 10,000 RU (Request Units)
- **비용: ~$1-5/월**

**Container Registry (Basic)**
- 10 GB 스토리지
- **비용: ~$5/월**

**Log Analytics Workspace**
- 1 GB 데이터 수집/월
- 31일 보관
- **비용: ~$2-5/월**

**총 예상 비용: $8-25/월**

> 💡 **비용 절감 팁**: 개발 환경에서는 Container Apps가 자동으로 scale to zero되어 사용하지 않을 때 과금이 없습니다.

---

## 초기 인프라 배포

### 1. Azure CLI 로그인

```bash
az login
