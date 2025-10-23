# MyStock - Personalized Stock Portfolio App

개인화된 주식 포트폴리오 관리 애플리케이션으로 미국(NYSE/NASDAQ) 주식 시장을 지원합니다.  
  
![주식 관심 종목](./images/01_stock_watchlist.png)  

> 이 애플리케이션은 주식 앱의 간단한 기능만 들어가 있으며 개선할 포인트가 존재합니다.  
빠른 배포를 위해 Azure 환경에서 쉽게 배포할 수 있도록 구성되어 있습니다.  
(추후 Codespace로 실습할 수 있는 환경이 업데이트 될 예정입니다.)  

[Demo 접속](https://stock.hemtory.com/)  

## Architecture
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

## Features

- **워치리스트 관리**: 관심 주식 종목 추가/삭제 및 실시간 시세 확인
- **주식 상세 정보**: 현재가, 변동률, 거래량, 캔들스틱 차트 (5가지 기간 옵션)
- **뉴스 피드**: 관련 뉴스 및 공시 정보 제공
![뉴스 피드](./images/02_stock_news.png) 
- **포트폴리오 관리**: 3개의 포트폴리오("장기투자", "단기투자", "정찰병")에서 보유 종목 관리
- **손익 분석**: 실시간 평가액, 손익률, 수익률 계산
![주식 포트폴리오](./images/03_stock_portfolio.png)  
- **급등락 종목**: 실시간 급등/급락 종목 및 거래량 상위 종목 조회 (Alpha Vantage API 활용)  

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: Azure Cosmos DB (로컬: MongoDB in Docker)
- **ORM**: SQLAlchemy with Alembic migrations
- **Stock Data**: Alpha Vantage API
- **Authentication**: JWT with bcrypt
- **Testing**: pytest

### Frontend
- **Framework**: Vue 3 (Composition API)
- **UI Library**: Tabler Dashboard
- **Charts**: ECharts
- **Build Tool**: Vite
- **State Management**: Pinia
- **Testing**: Vitest

### Infrastructure
- **Cloud**: Azure (Cosmos DB NoSQL, Container Apps, Azure Static Web Apps 배포)
- **CI/CD**: GitHub Actions (backend: build/deploy, frontend: build/deploy)

## 배포가이드 문서

이 문서는 MyStock 애플리케이션을 Azure에 배포하는 전체 과정을 설명합니다.  
[DEPLOYMENT_GUIDE](./DEPLOYMENT_GUIDE.md) 파일에서 참고


## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please create an issue in the repository.
