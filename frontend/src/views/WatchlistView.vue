<template>
  <app-layout page-title="관심종목" page-subtitle="나의 주식">
    <div class="row row-deck row-cards">
      <div class="col-12">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">관심종목 목록</h3>
            <div class="card-actions">
              <button class="btn btn-primary" @click="showAddModal = true">
                <i class="ti ti-plus"></i>
                종목 추가
              </button>
            </div>
          </div>
          
          <div class="card-body">
            <!-- Loading state -->
            <div v-if="watchlistStore.loading" class="text-center py-5">
              <div class="spinner-border text-primary"></div>
            </div>
            
            <!-- Error state -->
            <div v-else-if="watchlistStore.error" class="alert alert-danger">
              {{ watchlistStore.error }}
            </div>
            
            <!-- Empty state -->
            <div v-else-if="!watchlistStore.hasItems" class="empty">
              <div class="empty-icon">
                <i class="ti ti-star"></i>
              </div>
              <p class="empty-title">관심종목이 없습니다</p>
              <p class="empty-subtitle text-muted">
                첫 번째 종목을 추가해보세요
              </p>
              <div class="empty-action">
                <button class="btn btn-primary" @click="showAddModal = true">
                  <i class="ti ti-plus"></i>
                  종목 추가
                </button>
              </div>
            </div>
            
            <!-- Watchlist items -->
            <div v-else class="table-responsive">
              <table class="table table-vcenter card-table">
                <thead>
                  <tr>
                    <th class="w-1"></th>
                    <th>종목코드</th>
                    <th>회사명</th>
                    <th style="width: 150px;">최근 추이</th>
                    <th class="text-end">현재가</th>
                    <th class="text-end">전일대비</th>
                    <th class="text-end">변동률</th>
                    <th class="text-end">시가총액</th>
                    <th>메모</th>
                    <th class="w-1"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="(item, index) in watchlistStore.items" 
                    :key="item.symbol"
                    draggable="true"
                    @dragstart="handleDragStart(index, $event)"
                    @dragover="handleDragOver(index, $event)"
                    @dragenter="handleDragEnter(index, $event)"
                    @dragleave="handleDragLeave($event)"
                    @drop="handleDrop(index, $event)"
                    @dragend="handleDragEnd"
                    :class="{ 'drag-over': dragOverIndex === index, 'dragging': draggingIndex === index }"
                    style="cursor: move;"
                  >
                    <td>
                      <div class="drag-handle" style="cursor: grab;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <line x1="3" y1="12" x2="21" y2="12"></line>
                          <line x1="3" y1="6" x2="21" y2="6"></line>
                          <line x1="3" y1="18" x2="21" y2="18"></line>
                        </svg>
                      </div>
                    </td>
                    <td>
                      <router-link :to="`/stock/${item.symbol}`" class="text-reset fw-bold">
                        {{ item.symbol }}
                      </router-link>
                    </td>
                    <td>
                      <span class="text-muted">
                        {{ getCompanyNameSync(item.symbol) }}
                      </span>
                    </td>
                    <td>
                      <div 
                        class="sparkline-container" 
                        :id="`sparkline-${item.symbol}`" 
                        style="height: 40px; width: 150px; cursor: pointer;"
                        @click="showDetailChart(item.symbol)"
                        :title="`${item.symbol} 상세 차트 보기`"
                      ></div>
                    </td>
                    <td class="text-end">
                      <span v-if="item.current_price" class="fw-bold fs-4" :class="getPriceColor(item)">
                        {{ formatPrice(item.current_price, item.symbol) }}
                      </span>
                      <span v-else class="text-muted">-</span>
                    </td>
                    <td class="text-end">
                      <span v-if="item.price_change" :class="getChangeClass(item.price_change)" class="fw-bold">
                        {{ formatChange(item.price_change, item.symbol) }}
                      </span>
                      <span v-else class="text-muted">-</span>
                    </td>
                    <td class="text-end">
                      <span v-if="item.change_percent" :class="getChangeClass(item.change_percent)" class="fw-bold">
                        {{ formatPercent(item.change_percent) }}
                      </span>
                      <span v-else class="text-muted">-</span>
                    </td>
                    <td class="text-end">
                      <span v-if="item.market_cap" class="text-muted">
                        {{ formatMarketCap(item.market_cap) }}
                      </span>
                      <span v-else class="text-muted">-</span>
                    </td>
                    <td>
                      <div v-if="editingSymbol === item.symbol" class="d-flex gap-2">
                        <input
                          v-model="editingNotes"
                          type="text"
                          class="form-control form-control-sm"
                          @keyup.enter="saveNotes(item.symbol)"
                          @keyup.esc="cancelEdit"
                          ref="notesInput"
                        />
                        <button
                          class="btn btn-sm btn-success"
                          @click="saveNotes(item.symbol)"
                          :disabled="watchlistStore.loading"
                        >
                          <i class="ti ti-check"></i>
                        </button>
                        <button
                          class="btn btn-sm btn-ghost-secondary"
                          @click="cancelEdit"
                        >
                          <i class="ti ti-x"></i>
                        </button>
                      </div>
                      <div v-else class="d-flex align-items-center gap-2">
                        <span class="text-muted flex-grow-1">{{ item.notes || '-' }}</span>
                        <button
                          class="btn btn-sm btn-ghost-secondary"
                          @click="startEdit(item.symbol, item.notes)"
                          title="메모 수정"
                        >
                          <i class="ti ti-edit"></i>
                        </button>
                      </div>
                    </td>
                    <td>
                      <button
                        class="btn btn-sm btn-ghost-danger"
                        @click="handleRemove(item.symbol)"
                        :disabled="watchlistStore.loading"
                      >
                        <i class="ti ti-trash"></i>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <!-- Item count -->
            <div v-if="watchlistStore.hasItems" class="card-footer">
              <div class="text-muted">
                총 {{ watchlistStore.count }}개 종목
                <span v-if="watchlistStore.isAtLimit" class="text-warning ms-2">
                  (최대 50개)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Detail Chart Card -->
      <div v-if="selectedSymbol" class="col-12">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ selectedSymbol }} - 캔들스틱 차트</h3>
            <div class="card-actions">
              <button class="btn btn-sm btn-ghost-secondary" @click="closeDetailChart">
                <i class="ti ti-x"></i>
              </button>
            </div>
          </div>
          
          <!-- Period selection tabs -->
          <div class="card-header">
            <ul class="nav nav-tabs card-header-tabs">
              <li class="nav-item" v-for="option in periodOptions" :key="option.value">
                <a 
                  class="nav-link" 
                  :class="{ active: selectedPeriod === option.value }"
                  href="#"
                  @click.prevent="changePeriod(option.value)"
                >
                  {{ option.label }}
                </a>
              </li>
            </ul>
          </div>
          
          <div class="card-body">
            <div id="detail-candlestick-chart" style="width: 100%; height: 400px;"></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Add stock modal (placeholder) -->
    <div v-if="showAddModal" class="modal modal-blur fade show" style="display: block;">
      <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">종목 추가</h5>
            <button type="button" class="btn-close" @click="showAddModal = false"></button>
          </div>
          <form @submit.prevent="handleAdd">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">종목코드</label>
                <input
                  v-model="newSymbol"
                  type="text"
                  class="form-control"
                  placeholder="예: AAPL, 005930.KS"
                  required
                />
              </div>
              <div class="mb-3">
                <label class="form-label">메모 (선택)</label>
                <textarea
                  v-model="newNotes"
                  class="form-control"
                  rows="2"
                  placeholder="메모를 입력하세요"
                ></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn me-auto" @click="showAddModal = false">취소</button>
              <button type="submit" class="btn btn-primary" :disabled="watchlistStore.loading">
                추가
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </app-layout>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import AppLayout from '@/components/layout/AppLayout.vue'
import * as echarts from 'echarts'
import apiClient from '@/api/client'
import { getCompanyNameSync } from '@/utils/symbolLookup'

const watchlistStore = useWatchlistStore()

// Modal state
const showAddModal = ref(false)
const newSymbol = ref('')
const newNotes = ref('')

// Detail chart state
const selectedSymbol = ref(null)
const detailChart = ref(null)
const selectedPeriod = ref('1d_3mo') // Default: 1일봉 3개월

// Period options
const periodOptions = [
  { label: '5m', value: '5m_1d', interval: '5m', period: '5m' },    // 5분봉 1일
  { label: 'H', value: '1h_1mo', interval: '1h', period: '1h' },    // 1시간봉 1개월
  { label: 'D', value: '1d_3mo', interval: '1d', period: '1d' },    // 1일봉 3개월
  { label: 'W', value: '1wk_2y', interval: '1wk', period: '1wk' },  // 1주봉 2년
  { label: 'M', value: '1mo_5y', interval: '1mo', period: '1mo' }   // 1월봉 5년
]

// Edit state
const editingSymbol = ref(null)
const editingNotes = ref('')
const notesInput = ref(null)

// Drag and drop state
const draggingIndex = ref(null)
const dragOverIndex = ref(null)

// Sparkline charts
const sparklineCharts = ref({})

// Fetch sparkline data for a symbol
async function fetchSparklineData(symbol) {
  try {
    const response = await apiClient.get(`/stocks/${symbol}/chart`, {
      params: { period: '1d' }  // 1일봉 1개월 (sparkline은 고정)
    })
    return response.data.candlesticks || []
  } catch (error) {
    console.error(`Failed to fetch sparkline for ${symbol}:`, error)
    return []
  }
}

// Fetch candlestick data with specified period
async function fetchCandlestickData(symbol, period) {
  try {
    const response = await apiClient.get(`/stocks/${symbol}/chart`, {
      params: { period: period }
    })
    return response.data.candlesticks || []
  } catch (error) {
    console.error(`Failed to fetch candlestick data for ${symbol}:`, error)
    return []
  }
}

// Render sparkline chart
function renderSparkline(symbol, data) {
  const containerId = `sparkline-${symbol}`
  const container = document.getElementById(containerId)
  
  if (!container || data.length === 0) return
  
  // Dispose existing chart if any
  if (sparklineCharts.value[symbol]) {
    sparklineCharts.value[symbol].dispose()
  }
  
  const chart = echarts.init(container)
  
  // Extract close prices
  const closePrices = data.map(item => item.close)
  const firstPrice = closePrices[0]
  const lastPrice = closePrices[closePrices.length - 1]
  const isPositive = lastPrice >= firstPrice
  
  const option = {
    grid: {
      left: 0,
      right: 0,
      top: 0,
      bottom: 0
    },
    xAxis: {
      type: 'category',
      show: false,
      data: data.map((_, index) => index)
    },
    yAxis: {
      type: 'value',
      show: false,
      scale: true
    },
    series: [
      {
        data: closePrices,
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: isPositive ? '#2fb344' : '#d63939',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: isPositive ? 'rgba(47, 179, 68, 0.3)' : 'rgba(214, 57, 57, 0.3)'
              },
              {
                offset: 1,
                color: isPositive ? 'rgba(47, 179, 68, 0.05)' : 'rgba(214, 57, 57, 0.05)'
              }
            ]
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
  sparklineCharts.value[symbol] = chart
  
  // Handle resize
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

// Load all sparklines
async function loadSparklines() {
  await nextTick()
  
  for (const item of watchlistStore.items) {
    const data = await fetchSparklineData(item.symbol)
    renderSparkline(item.symbol, data)
  }
}

// Detail chart functions
async function showDetailChart(symbol) {
  selectedSymbol.value = symbol
  selectedPeriod.value = '1d_3mo' // Reset to default period
  await nextTick()
  
  // Render chart with selected period
  await renderDetailCandlestickChart()
}

function closeDetailChart() {
  if (detailChart.value) {
    detailChart.value.dispose()
    detailChart.value = null
  }
  selectedSymbol.value = null
  selectedPeriod.value = '1d_3mo'
}

async function changePeriod(periodValue) {
  selectedPeriod.value = periodValue
  await renderDetailCandlestickChart()
}

async function renderDetailCandlestickChart() {
  if (!selectedSymbol.value) return
  
  // Get period configuration
  const periodConfig = periodOptions.find(opt => opt.value === selectedPeriod.value)
  if (!periodConfig) return
  
  // Fetch data with selected period
  const data = await fetchCandlestickData(selectedSymbol.value, periodConfig.period)
  if (!data || data.length === 0) {
    console.warn(`No chart data available for ${selectedSymbol.value} with period ${periodConfig.period}`)
    
    // Show error message in chart container
    const container = document.getElementById('detail-candlestick-chart')
    if (container) {
      container.innerHTML = `
        <div style="display: flex; justify-content: center; align-items: center; height: 100%; color: var(--tblr-secondary);">
          <div style="text-align: center;">
            <i class="ti ti-chart-line" style="font-size: 48px; opacity: 0.5;"></i>
            <div style="margin-top: 16px;">차트 데이터를 불러올 수 없습니다</div>
            <div style="font-size: 0.875rem; opacity: 0.7; margin-top: 8px;">다른 기간을 선택해주세요</div>
          </div>
        </div>
      `
    }
    return
  }
  
  // Render chart
  const container = document.getElementById('detail-candlestick-chart')
  if (!container) return
  
  // Clear any error message
  container.innerHTML = ''
  
  // Dispose existing chart
  if (detailChart.value) {
    detailChart.value.dispose()
  }
  
  const chart = echarts.init(container)
  
  // Get period label from already fetched periodConfig
  const periodLabel = periodConfig?.label || 'D'
  
  // Format dates based on period
  const dates = data.map(d => {
    const date = new Date(d.date)
    
    // 5m: 일자 시:분 (10/21 09:30)
    if (periodLabel === '5m') {
      const month = date.getMonth() + 1
      const day = date.getDate()
      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      return `${month}/${day} ${hours}:${minutes}`
    }
    
    // M, W: 연/월/일 (2024/10/21)
    if (periodLabel === 'M' || periodLabel === 'W') {
      const year = date.getFullYear()
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      return `${year}/${month}/${day}`
    }
    
    // 기본 (H, D): 월/일 (10/21)
    return `${date.getMonth() + 1}/${date.getDate()}`
  })
  
  const candleData = data.map(d => [d.open, d.close, d.low, d.high])
  const volumes = data.map(d => d.volume)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function (params) {
        if (!params || params.length === 0) return ''
        
        const candleParam = params.find(p => p.seriesType === 'candlestick')
        const volumeParam = params.find(p => p.seriesType === 'bar')
        
        let tooltip = ''
        
        // Candlestick data
        if (candleParam && candleParam.data && Array.isArray(candleParam.data)) {
          const candleValue = candleParam.data
          tooltip += `<div style="font-weight: bold; margin-bottom: 5px;">${candleParam.name}</div>`
          tooltip += `<div>시가: $${candleValue[1].toFixed(2)}</div>`
          tooltip += `<div>종가: $${candleValue[2].toFixed(2)}</div>`
          tooltip += `<div>최저: $${candleValue[3].toFixed(2)}</div>`
          tooltip += `<div>최고: $${candleValue[4].toFixed(2)}</div>`
        }
        
        // Volume data
        if (volumeParam && volumeParam.data !== undefined) {
          if (!tooltip) {
            tooltip += `<div style="font-weight: bold; margin-bottom: 5px;">${volumeParam.name}</div>`
          }
          tooltip += `<div>거래량: ${volumeParam.data.toLocaleString()}</div>`
        }
        
        return tooltip
      }
    },
    grid: [
      {
        left: '10%',
        right: '10%',
        top: '15%',
        height: '50%'
      },
      {
        left: '10%',
        right: '10%',
        top: '70%',
        height: '15%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        boundaryGap: false,
        axisLine: { 
          onZero: false,
          lineStyle: { color: '#6c757d' }
        },
        splitLine: { show: false },
        axisLabel: {
          color: '#6c757d'  // 중간 회색
        },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        boundaryGap: false,
        axisLine: { 
          onZero: false,
          lineStyle: { color: '#6c757d' }
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      {
        scale: true,
        splitArea: {
          show: true
        },
        axisLine: {
          lineStyle: { color: '#6c757d' }
        },
        axisLabel: {
          color: '#6c757d'  // 중간 회색
        },
        splitLine: {
          lineStyle: { color: '#dee2e6' }  // 연한 회색 그리드
        }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '90%',
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: '캔들',
        type: 'candlestick',
        data: candleData,
        itemStyle: {
          color: '#2fb344',
          color0: '#d63939',
          borderColor: '#2fb344',
          borderColor0: '#d63939'
        }
      },
      {
        name: '거래량',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: function(params) {
            const candleItem = candleData[params.dataIndex]
            return candleItem[1] >= candleItem[0] ? '#2fb344' : '#d63939'
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
  detailChart.value = chart
  
  // Handle resize
  window.addEventListener('resize', () => {
    if (detailChart.value) {
      detailChart.value.resize()
    }
  })
}

// Lifecycle
onMounted(async () => {
  await watchlistStore.fetchWatchlist()
  await loadSparklines()
})

// Methods
async function handleAdd() {
  try {
    await watchlistStore.addStock(newSymbol.value, newNotes.value)
    
    // Reset form and close modal
    newSymbol.value = ''
    newNotes.value = ''
    showAddModal.value = false
    
    // Reload sparklines
    await loadSparklines()
  } catch (error) {
    console.error('Failed to add stock:', error)
  }
}

async function handleRemove(symbol) {
  if (confirm(`${symbol}을(를) 관심종목에서 삭제하시겠습니까?`)) {
    try {
      // Dispose chart before removing
      if (sparklineCharts.value[symbol]) {
        sparklineCharts.value[symbol].dispose()
        delete sparklineCharts.value[symbol]
      }
      
      await watchlistStore.removeStock(symbol)
    } catch (error) {
      console.error('Failed to remove stock:', error)
    }
  }
}

// Edit handlers
function startEdit(symbol, notes) {
  editingSymbol.value = symbol
  editingNotes.value = notes || ''
  // Focus input on next tick
  setTimeout(() => {
    if (notesInput.value) {
      notesInput.value.focus()
    }
  }, 50)
}

async function saveNotes(symbol) {
  try {
    await watchlistStore.updateNotes(symbol, editingNotes.value)
    editingSymbol.value = null
    editingNotes.value = ''
  } catch (error) {
    console.error('Failed to update notes:', error)
  }
}

function cancelEdit() {
  editingSymbol.value = null
  editingNotes.value = ''
}

// Drag and Drop handlers
function handleDragStart(index, event) {
  draggingIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/html', event.target.innerHTML)
  // Add a slight opacity to the dragged element
  event.target.style.opacity = '0.5'
}

function handleDragOver(index, event) {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  return false
}

function handleDragEnter(index, event) {
  if (index !== draggingIndex.value) {
    dragOverIndex.value = index
  }
}

function handleDragLeave(event) {
  // Only clear if we're leaving the row entirely
  const relatedTarget = event.relatedTarget
  if (!relatedTarget || !event.currentTarget.contains(relatedTarget)) {
    dragOverIndex.value = null
  }
}

async function handleDrop(dropIndex) {
  if (draggingIndex.value === null || draggingIndex.value === dropIndex) {
    draggingIndex.value = null
    dragOverIndex.value = null
    return
  }
  
  try {
    const dragIndex = draggingIndex.value
    draggingIndex.value = null
    
    // Reorder locally
    const items = [...watchlistStore.items]
    
    // Remove the dragged item
    const [draggedItem] = items.splice(dragIndex, 1)
    
    // Insert at the new position
    items.splice(dropIndex, 0, draggedItem)
    
    // Create the new symbol order
    const symbolOrder = items.map(item => item.symbol)
    
    // Update on the server
    await watchlistStore.reorderWatchlist(symbolOrder)
    
    // Dispose all existing sparkline charts
    Object.values(sparklineCharts.value).forEach(chart => {
      if (chart) chart.dispose()
    })
    sparklineCharts.value = {}
    
    // Reload sparklines after reordering
    await nextTick()
    await loadSparklines()
  } catch (error) {
    console.error('Failed to reorder watchlist:', error)
    // Optionally show an error message to the user
  }
  
  dragOverIndex.value = null
}

function handleDragEnd(event) {
  // Reset opacity
  event.target.style.opacity = '1'
  draggingIndex.value = null
  dragOverIndex.value = null
}

// Formatting functions
function isUSStock(symbol) {
  return !symbol.includes('.')
}

function formatPrice(price, symbol) {
  if (!price) return '-'
  if (isUSStock(symbol)) {
    return `$${price.toFixed(2)}`
  }
  return `₩${price.toLocaleString('ko-KR')}`
}

function formatChange(change, symbol) {
  if (!change) return '-'
  const prefix = change >= 0 ? '+' : ''
  if (isUSStock(symbol)) {
    return `${prefix}$${change.toFixed(2)}`
  }
  return `${prefix}₩${change.toLocaleString('ko-KR')}`
}

function formatPercent(percent) {
  if (!percent) return '-'
  const prefix = percent >= 0 ? '+' : ''
  return `${prefix}${percent.toFixed(2)}%`
}

function formatMarketCap(marketCap) {
  if (!marketCap) return '-'
  
  if (marketCap >= 1_000_000_000_000) {
    return `${(marketCap / 1_000_000_000_000).toFixed(2)}T`
  } else if (marketCap >= 1_000_000_000) {
    return `${(marketCap / 1_000_000_000).toFixed(2)}B`
  } else if (marketCap >= 1_000_000) {
    return `${(marketCap / 1_000_000).toFixed(2)}M`
  }
  return marketCap.toLocaleString()
}

function getPriceColor(item) {
  if (!item.price_change) return ''
  return item.price_change >= 0 ? 'text-success' : 'text-danger'
}

function getChangeClass(value) {
  if (!value) return ''
  return value >= 0 ? 'text-success' : 'text-danger'
}
</script>

<style scoped>
.modal.show {
  background-color: rgba(0, 0, 0, 0.5);
}

/* Drag and drop styles */
tr.dragging {
  opacity: 0.5;
}

tr.drag-over {
  border-top: 3px solid #206bc4;
  background-color: rgba(32, 107, 196, 0.1);
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667085;
  padding: 0.25rem;
}

.drag-handle:hover {
  color: #206bc4;
}

.drag-handle:active {
  cursor: grabbing !important;
}

tr[draggable="true"]:hover {
  background-color: rgba(0, 0, 0, 0.02);
}
</style>
