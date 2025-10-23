# Feature: 급등락 종목 페이지 추가

## 📋 기능 개요
미국 주식시장의 급등/급락 종목 및 활발히 거래되는 종목을 한눈에 볼 수 있는 페이지를 추가합니다.

## 🎯 목표
- Alpha Vantage의 `TOP_GAINERS_LOSERS` API를 활용하여 실시간 시장 동향 파악
- 급등 상위 20개, 급락 상위 20개, 거래량 상위 20개 종목을 세로 리스트로 표시
- 사용자가 시장의 흐름을 빠르게 파악할 수 있도록 직관적인 UI 제공

## 📊 API 사양

### Endpoint
```
GET https://www.alphavantage.co/query
```

### Parameters
- `function`: `TOP_GAINERS_LOSERS`
- `apikey`: Alpha Vantage API Key

### Response Structure
```json
{
  "metadata": "Top gainers, losers, and most actively traded US tickers",
  "last_updated": "2025-10-21 16:16:00 US/Eastern",
  "top_gainers": [ /* 20 items */ ],
  "top_losers": [ /* 20 items */ ],
  "most_actively_traded": [ /* 20 items */ ]
}
```

### 각 종목 데이터 구조
```json
{
  "ticker": "BYND",
  "price": "3.62",
  "change_amount": "2.15",
  "change_percentage": "146.2585%",
  "volume": "1812070328"
}
```

## 🎨 UI/UX 설계

### 페이지 레이아웃
```
┌─────────────────────────────────────────────────────────┐
│ 급등락 종목                                               │
├─────────────────────────────────────────────────────────┤
│ 마지막 업데이트: 2025-10-21 16:16:00 US/Eastern         │
├─────────────┬─────────────┬─────────────────────────────┤
│ 급등 TOP 20 │ 급락 TOP 20 │ 거래량 TOP 20                │
├─────────────┼─────────────┼─────────────────────────────┤
│ BYND        │ RGTU        │ BYND                         │
│ +146.26%    │ -71.72%     │ 1.8B                         │
│ $3.62       │ $72.89      │ +146.26%                     │
├─────────────┼─────────────┼─────────────────────────────┤
│ SVREW       │ QBTX        │ YDKG                         │
│ +141.55%    │ -70.71%     │ 808M                         │
│ $0.05       │ $79.00      │ +27.99%                      │
├─────────────┼─────────────┼─────────────────────────────┤
│ ...         │ ...         │ ...                          │
└─────────────┴─────────────┴─────────────────────────────┘
```

### 디자인 요구사항
1. **3단 칼럼 레이아웃**
   - 데스크톱: 3개 칼럼 나란히 배치
   - 태블릿: 1개 칼럼 (스크롤)
   - 모바일: 탭 형식으로 전환 가능

2. **색상 구분**
   - 급등: 녹색/빨간색 (상승)
   - 급락: 파란색/회색 (하락)
   - 거래량: 중립 색상

3. **각 항목 표시 정보**
   - 티커 심볼 (굵게)
   - 등락률 (색상 강조)
   - 현재 가격
   - 거래량 (K/M/B 단위로 축약)

4. **인터랙션**
   - 종목 클릭 시 상세 페이지로 이동
   - 새로고침 버튼 (수동 업데이트)
   - 로딩 스피너

## 🔧 기술 구현 계획

### Backend (FastAPI)

#### 1. API Endpoint 추가
**파일**: `backend/src/api/stocks.py`

```python
@router.get("/market/top-movers", response_model=TopMoversResponse)
async def get_top_movers():
    """Get top gainers, losers, and most actively traded stocks.
    
    Returns:
        Top 20 gainers, losers, and most actively traded stocks from Alpha Vantage
    """
```

#### 2. Service Layer
**파일**: `backend/src/services/stock_data_service.py`

```python
def get_top_movers(self) -> dict:
    """Fetch TOP_GAINERS_LOSERS from Alpha Vantage.
    
    Returns:
        dict: Contains top_gainers, top_losers, most_actively_traded lists
    """
    url = f"{self.base_url}?function=TOP_GAINERS_LOSERS&apikey={self.api_key}"
    response = requests.get(url, timeout=10)
    return response.json()
```

#### 3. Response Schema
**파일**: `backend/src/schemas/stocks.py`

```python
class TopMoverItem(BaseModel):
    ticker: str
    price: Decimal
    change_amount: Decimal
    change_percentage: str
    volume: str

class TopMoversResponse(BaseModel):
    metadata: str
    last_updated: str
    top_gainers: List[TopMoverItem]
    top_losers: List[TopMoverItem]
    most_actively_traded: List[TopMoverItem]
```

### Frontend (Vue.js)

#### 1. 새 페이지 컴포넌트
**파일**: `frontend/src/views/TopMoversView.vue`

```vue
<template>
  <div class="top-movers-view">
    <h1>급등락 종목</h1>
    <p class="last-updated">{{ lastUpdated }}</p>
    
    <div class="movers-grid">
      <TopMoversList 
        title="급등 TOP 20" 
        :items="topGainers" 
        type="gainers" 
      />
      <TopMoversList 
        title="급락 TOP 20" 
        :items="topLosers" 
        type="losers" 
      />
      <TopMoversList 
        title="거래량 TOP 20" 
        :items="mostActively" 
        type="volume" 
      />
    </div>
  </div>
</template>
```

#### 2. 리스트 컴포넌트
**파일**: `frontend/src/components/movers/TopMoversList.vue`

```vue
<template>
  <div class="movers-list">
    <h2>{{ title }}</h2>
    <div class="list-container">
      <TopMoverCard 
        v-for="item in items" 
        :key="item.ticker"
        :item="item"
        :type="type"
      />
    </div>
  </div>
</template>
```

#### 3. 카드 컴포넌트
**파일**: `frontend/src/components/movers/TopMoverCard.vue`

```vue
<template>
  <div class="mover-card" @click="goToDetail">
    <div class="ticker">{{ item.ticker }}</div>
    <div class="change" :class="changeClass">
      {{ item.change_percentage }}
    </div>
    <div class="price">${{ item.price }}</div>
    <div class="volume">{{ formattedVolume }}</div>
  </div>
</template>
```

#### 4. API Client
**파일**: `frontend/src/api/client.js`

```javascript
export const stocksApi = {
  async getTopMovers() {
    const response = await apiClient.get('/stocks/market/top-movers')
    return response.data
  }
}
```

#### 5. Router 설정
**파일**: `frontend/src/router/index.js`

```javascript
{
  path: '/top-movers',
  name: 'TopMovers',
  component: () => import('@/views/TopMoversView.vue'),
  meta: { requiresAuth: true }
}
```

#### 6. Navigation 메뉴 추가
**파일**: `frontend/src/components/layout/AppLayout.vue`

메뉴 항목 추가:
- 관심종목
- 포트폴리오
- **급등락 종목** ← NEW

## ✅ 체크리스트

### Backend Tasks
- [ ] `stocks.py`에 `/market/top-movers` 엔드포인트 추가
- [ ] `stock_data_service.py`에 `get_top_movers()` 메서드 구현
- [ ] `schemas/stocks.py`에 `TopMoverItem`, `TopMoversResponse` 스키마 정의
- [ ] Alpha Vantage API 호출 및 에러 핸들링
- [ ] 캐싱 전략 구현 (선택사항, API 호출 제한 고려)
- [ ] API 테스트 작성

### Frontend Tasks
- [ ] `TopMoversView.vue` 페이지 컴포넌트 생성
- [ ] `TopMoversList.vue` 리스트 컴포넌트 생성
- [ ] `TopMoverCard.vue` 카드 컴포넌트 생성
- [ ] API client에 `getTopMovers()` 함수 추가
- [ ] Router에 `/top-movers` 경로 추가
- [ ] Navigation 메뉴에 "급등락 종목" 추가
- [ ] 반응형 디자인 적용 (모바일/태블릿/데스크톱)
- [ ] 로딩 상태 처리
- [ ] 에러 처리 (API 실패 시)
- [ ] 새로고침 기능 구현
- [ ] 컴포넌트 테스트 작성 (선택사항)

### 추가 고려사항
- [ ] 캐싱: Alpha Vantage API는 실시간이 아니므로 5-10분 캐싱 적용
- [ ] 에러 핸들링: API 호출 실패 시 사용자 친화적 메시지 표시
- [ ] 성능 최적화: 거래량 숫자 포맷팅 (1,812,070,328 → 1.8B)
- [ ] 접근성: 키보드 네비게이션, 스크린 리더 지원
- [ ] 다크 모드: 급등/급락 색상 대비 확인

## 📝 참고 자료
- [Alpha Vantage TOP_GAINERS_LOSERS API](https://www.alphavantage.co/documentation/#top-gainers-losers)
- Sample Response: `sample_data/alphavantage_TOP_GAINERS_LOSERS.json`

## 🎯 완료 조건
1. 사용자가 "급등락 종목" 메뉴를 클릭하면 페이지로 이동
2. 3개의 리스트가 세로로 표시됨 (급등/급락/거래량 상위 20)
3. 각 종목 카드에 티커, 등락률, 가격, 거래량이 표시됨
4. 종목 클릭 시 상세 페이지로 이동
5. 로딩 및 에러 상태가 적절히 처리됨
6. 모바일/태블릿에서도 정상 동작

## 🚀 우선순위
**Priority**: Medium  
**Effort**: 3-5 days  
**Sprint**: Next

## 📌 Labels
- `feature`
- `frontend`
- `backend`
- `enhancement`
