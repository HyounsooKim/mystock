<template>
  <app-layout :page-title="`${symbol} - ${companyName}`" page-subtitle="주식 정보">
    <div class="row row-deck row-cards">

        <!-- News Section -->
      <div class="col-12">
        <div class="card">
          <div class="card-header">
            <div class="row align-items-center w-100">
              <!-- Stock Stats -->
              <div v-if="stockInfo" class="col">
                <div class="d-flex align-items-center gap-4">
                  <!-- 현재가 -->
                  <div>
                    <div class="text-muted small">현재가</div>
                    <div class="fw-bold fs-3" :class="getPriceChangeClass(stockInfo.change_percent)">
                      {{ formatPrice(stockInfo.current_price) }}
                    </div>
                  </div>
                  
                  <!-- 전일대비 -->
                  <div>
                    <div class="text-muted small">전일대비</div>
                    <div class="fw-bold fs-4" :class="getPriceChangeClass(stockInfo.change_percent)">
                      {{ formatChangeValue(stockInfo.price_change) }}
                    </div>
                  </div>
                  
                  <!-- 변동률 -->
                  <div>
                    <div class="text-muted small">변동률</div>
                    <div class="fw-bold fs-4" :class="getPriceChangeClass(stockInfo.change_percent)">
                      {{ formatChangePercent(stockInfo.change_percent) }}
                    </div>
                  </div>
                  
                  <!-- Sparkline (변동률 뒤) -->
                  <div class="d-flex align-items-center gap-2">
                    <span class="text-muted small">최근</span>
                    <div 
                      id="stock-sparkline" 
                      class="sparkline-container"
                      style="width: 200px; height: 50px;"
                    ></div>
                  </div>
                  
                  <!-- 거래량 -->
                  <div v-if="stockInfo.volume">
                    <div class="text-muted small">거래량</div>
                    <div class="fw-bold">
                      {{ formatVolume(stockInfo.volume) }}
                    </div>
                  </div>
                </div>
              </div>
              
                <!-- Right: News Count Selector -->
                <div class="col-auto ms-auto">
                <div class="d-flex align-items-center gap-2">
                  <label for="news-limit" class="form-label mb-0">표시 개수:</label>
                  <select 
                  id="news-limit" 
                  v-model.number="newsLimit" 
                  @change="fetchNews" 
                  class="form-select form-select-sm"
                  style="width: auto;"
                  >
                  <option :value="10">10개</option>
                  <option :value="20">20개</option>
                  <option :value="30">30개</option>
                  <option :value="40">40개</option>
                  <option :value="50">50개</option>
                  </select>                  
                </div>
                </div>
            </div>
          </div>
          
          <!-- Loading State -->
          <div v-if="loading" class="card-body text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted mt-2">뉴스를 불러오는 중...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="card-body">
            <div class="alert alert-danger" role="alert">
              <h4 class="alert-title">오류 발생</h4>
              <p>{{ error }}</p>
              <button @click="fetchNews" class="btn btn-danger mt-2">다시 시도</button>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else-if="news.length === 0" class="card-body text-center py-5">
            <div class="empty">
              <div class="empty-icon">
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-news" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                  <path d="M16 6h3a1 1 0 0 1 1 1v11a2 2 0 0 1 -4 0v-13a1 1 0 0 0 -1 -1h-10a1 1 0 0 0 -1 1v12a3 3 0 0 0 3 3h11"></path>
                  <path d="M8 8l4 0"></path>
                  <path d="M8 12l4 0"></path>
                  <path d="M8 16l4 0"></path>
                </svg>
              </div>
              <p class="empty-title">뉴스가 없습니다</p>
              <p class="empty-subtitle text-muted">
                {{ symbol }} 종목에 대한 최근 뉴스가 없습니다.
              </p>
            </div>
          </div>

          <!-- News List -->
          <div v-else class="list-group list-group-flush">
            <div 
              v-for="(item, index) in news" 
              :key="index"
              class="list-group-item"
            >
              <div class="row align-items-start">
                <!-- Content -->
                <div class="col">
                  <!-- Publisher Badge and Date -->
                  <div class="mb-2 d-flex align-items-center justify-content-between">
                    <span class="badge bg-blue text-white">{{ item.publisher }}</span>
                    <small class="news-date" style="font-size: 0.75rem;">
                      {{ formatDate(item.published_at) }}
                      <span class="text-muted ms-1">({{ formatFullDate(item.published_at) }})</span>
                    </small>
                  </div>

                  <!-- Title with Summary Toggle and Link -->
                  <details v-if="item.summary" class="news-details">
                    <summary class="news-summary-container mb-2">
                      <h4 class="news-title-with-toggle mb-0">
                        <svg class="summary-arrow" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                        <a 
                          :href="item.link" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          class="text-decoration-none news-title d-flex align-items-center gap-1"
                          @click.stop
                        >
                          {{ item.title }}
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                          </svg>
                        </a>
                      </h4>
                    </summary>
                    <p class="news-summary-text mt-2 ms-4">
                      {{ item.summary }}
                    </p>
                  </details>

                  <!-- Title without Summary -->
                  <h4 v-else class="mb-2">
                    <a 
                      :href="item.link" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      class="text-decoration-none news-title d-flex align-items-center gap-1"
                    >
                      {{ item.title }}
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                      </svg>
                    </a>
                  </h4>
                </div>

                <!-- Thumbnail (Right aligned) -->
                <div class="col-auto">
                  <div class="news-thumbnail">
                    <img 
                      v-if="item.thumbnail_url" 
                      :src="item.thumbnail_url" 
                      :alt="item.title"
                      @error="(e) => e.target.style.display = 'none'"
                      style="height: 60px; width: auto; object-fit: cover; border-radius: 4px;"
                    />
                    <div 
                      v-else 
                      class="d-flex align-items-center justify-content-center bg-light" 
                      style="height: 60px; width: 90px; border-radius: 4px;"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <circle cx="8.5" cy="8.5" r="1.5"></circle>
                        <polyline points="21 15 16 10 5 21"></polyline>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="news.length > 0" class="card-footer">
            <div class="text-muted">총 {{ news.length }}개의 뉴스</div>
          </div>
        </div>
      </div>
    </div>
  </app-layout>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import apiClient from '@/api/client'
import * as echarts from 'echarts'
import { getCompanyNameSync } from '@/utils/symbolLookup'

const route = useRoute()
const symbol = route.params.symbol

// Get company name for the symbol
const companyName = computed(() => getCompanyNameSync(symbol))

const news = ref([])
const loading = ref(false)
const error = ref(null)
const newsLimit = ref(10)
const sparklineChart = ref(null)
const stockInfo = ref(null)

// Fetch stock info from watchlist
const fetchStockInfo = async () => {
  try {
    // Try to get from watchlist first
    const watchlistResponse = await apiClient.get('/watchlist')
    const watchlistItem = watchlistResponse.data.items.find(item => item.symbol === symbol)
    
    if (watchlistItem) {
      // Use watchlist data
      stockInfo.value = {
        current_price: watchlistItem.current_price,
        price_change: watchlistItem.price_change,
        change_percent: watchlistItem.change_percent,
        volume: watchlistItem.volume
      }
    } else {
      // Fallback to stock info endpoint
      const response = await apiClient.get(`/stocks/${symbol}`)
      stockInfo.value = {
        current_price: response.data.current_price,
        price_change: response.data.price_change,
        change_percent: response.data.change_percent,
        volume: response.data.volume
      }
    }
  } catch (err) {
    console.error('Failed to fetch stock info:', err)
  }
}

const fetchNews = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await apiClient.get(`/stocks/${symbol}/news`, {
      params: { limit: newsLimit.value }
    })
    news.value = response.data.news
  } catch (err) {
    console.error('Failed to fetch news:', err)
    error.value = err.response?.data?.detail || '뉴스를 불러오는데 실패했습니다.'
  } finally {
    loading.value = false
  }
}

// Fetch sparkline data (1시간봉)
async function fetchSparklineData() {
  try {
    const response = await apiClient.get(`/stocks/${symbol}/chart`, {
      params: { period: '1h' }  // 1시간봉
    })
    return response.data.candlesticks || []
  } catch (error) {
    console.error(`Failed to fetch sparkline for ${symbol}:`, error)
    return []
  }
}

// Render sparkline chart
async function renderSparkline() {
  await nextTick()
  
  const container = document.getElementById('stock-sparkline')
  if (!container) return
  
  const data = await fetchSparklineData()
  if (!data || data.length === 0) return
  
  // Dispose existing chart if any
  if (sparklineChart.value) {
    sparklineChart.value.dispose()
  }
  
  const chart = echarts.init(container)
  
  const prices = data.map(d => d.close)
  
  // Determine color based on first and last price
  const firstPrice = prices[0]
  const lastPrice = prices[prices.length - 1]
  const lineColor = lastPrice >= firstPrice ? '#2fb344' : '#d63939'
  const areaColor = lastPrice >= firstPrice ? 'rgba(47, 179, 68, 0.1)' : 'rgba(214, 57, 57, 0.1)'
  
  const option = {
    grid: {
      left: 0,
      right: 0,
      top: 5,
      bottom: 5
    },
    xAxis: {
      type: 'category',
      data: data.map((_, i) => i),
      show: false
    },
    yAxis: {
      type: 'value',
      show: false,
      scale: true
    },
    series: [{
      data: prices,
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: {
        color: lineColor,
        width: 2
      },
      areaStyle: {
        color: areaColor
      }
    }]
  }
  
  chart.setOption(option)
  sparklineChart.value = chart
}

// Format functions
const formatPrice = (price) => {
  if (!price) return '-'
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price)
}

const formatChangeValue = (change) => {
  if (change === null || change === undefined) return '-'
  const sign = change >= 0 ? '+' : ''
  return `${sign}$${Math.abs(change).toFixed(2)}`
}

const formatChangePercent = (percent) => {
  if (percent === null || percent === undefined) return '-'
  const sign = percent >= 0 ? '+' : ''
  return `${sign}${percent.toFixed(2)}%`
}

const formatVolume = (volume) => {
  if (!volume) return '-'
  
  if (volume >= 1e9) {
    return `${(volume / 1e9).toFixed(2)}B`
  } else if (volume >= 1e6) {
    return `${(volume / 1e6).toFixed(2)}M`
  } else if (volume >= 1e3) {
    return `${(volume / 1e3).toFixed(2)}K`
  }
  return new Intl.NumberFormat('ko-KR').format(volume)
}

const getPriceChangeClass = (changePercent) => {
  if (changePercent === null || changePercent === undefined) return ''
  return changePercent > 0 ? 'text-success' : changePercent < 0 ? 'text-danger' : ''
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 60) {
    return `${diffMins}분 전`
  } else if (diffHours < 24) {
    return `${diffHours}시간 전`
  } else if (diffDays < 7) {
    return `${diffDays}일 전`
  } else {
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }
}

const formatFullDate = (dateString) => {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  
  // Convert to KST (UTC+9)
  const kstDate = new Date(date.toLocaleString('en-US', { timeZone: 'Asia/Seoul' }))
  
  const year = kstDate.getFullYear()
  const month = String(kstDate.getMonth() + 1).padStart(2, '0')
  const day = String(kstDate.getDate()).padStart(2, '0')
  const hours = kstDate.getHours()
  const minutes = String(kstDate.getMinutes()).padStart(2, '0')
  
  // Convert to 12-hour format
  const period = hours >= 12 ? 'PM' : 'AM'
  const displayHours = hours % 12 || 12
  
  return `${year}-${month}-${day} ${displayHours}:${minutes} ${period}`
}

onMounted(async () => {
  await fetchStockInfo()
  fetchNews()
  await nextTick()
  renderSparkline()
})
</script>

<style scoped>
/* Sparkline container */
.sparkline-container {
  display: inline-block;
  background: transparent;
}

/* News details container */
.news-details {
  margin-bottom: 0.5rem;
}

/* Summary container - remove default marker */
.news-summary-container {
  list-style: none;
  cursor: pointer;
}

.news-summary-container::-webkit-details-marker {
  display: none;
}

/* Title with toggle */
.news-title-with-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Summary arrow - rotate when open */
.summary-arrow {
  flex-shrink: 0;
  transition: transform 0.2s;
  color: var(--tblr-secondary, #6b7280);
}

details[open] .summary-arrow {
  transform: rotate(90deg);
}

/* News title link - adaptive for light/dark theme */
.news-title {
  color: var(--tblr-body-color, #1e293b) !important;
  transition: color 0.2s;
}

.news-title:hover {
  color: #4dabf7 !important;
}

/* Summary text - adaptive for light/dark theme */
.news-summary-text {
  color: var(--tblr-body-color, #6b7280);
  font-size: 0.875rem;
  line-height: 1.5;
  opacity: 0.9;
}

/* Published date - adaptive for light/dark theme */
.news-date {
  color: var(--tblr-secondary, #6b7280);
  font-size: 0.875rem;
}

/* List group item padding */
.list-group-item {
  padding-top: 10px !important;
  padding-bottom: 10px !important;
}

/* Badge enhancement */
.badge.bg-blue {
  background-color: #1971c2 !important;
  color: white !important;
  font-weight: 500;
}
</style>
