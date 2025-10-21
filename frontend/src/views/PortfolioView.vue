<template>
  <app-layout page-title="포트폴리오" page-subtitle="나의 자산">
    <div class="row row-deck row-cards">
      <!-- Portfolio tabs -->
      <div class="col-12">
        <div class="card">
          <div class="card-header">
            <ul class="nav nav-tabs card-header-tabs">
              <li
                v-for="portfolio in portfolioStore.portfolios"
                :key="portfolio.id"
                class="nav-item"
              >
                <a
                  href="#"
                  class="nav-link"
                  :class="{ active: currentPortfolioId === portfolio.id }"
                  @click.prevent="selectPortfolio(portfolio)"
                >
                  {{ portfolio.name }}
                  <span class="badge bg-secondary ms-2">
                    {{ portfolio.holdings_count || 0 }}
                  </span>
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <!-- Loading state -->
      <div v-if="portfolioStore.loading" class="col-12">
        <div class="text-center py-5">
          <div class="spinner-border text-primary"></div>
        </div>
      </div>
      
      <!-- Portfolio content -->
      <template v-else-if="portfolioStore.summary">
        <div class="col-12">
          <div class="row">
            <!-- USD Portfolio Section -->
            <div 
              :class="portfolioStore.summary.krw_cost_basis > 0 ? 'col-lg-6' : 'col-12'"
              v-if="portfolioStore.summary.usd_cost_basis > 0"
            >
              <h4 class="mb-3">미국 주식 (USD)</h4>
              <div class="row">
                <!-- Left: Summary Cards (60%) -->
                <div class="col-lg-7">
                  <div class="row">
                    <div class="col-6 mb-3">
                      <div class="card">
                        <div class="card-body p-2">
                          <div class="subheader small">총 투자금</div>
                          <div class="h3 mb-0">
                            {{ formatUSD(portfolioStore.summary.usd_cost_basis) }}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div class="col-6 mb-3">
                      <div class="card">
                        <div class="card-body p-2">
                          <div class="subheader small">현재 가치</div>
                          <div class="h3 mb-0">
                            {{ formatUSD(portfolioStore.summary.usd_current_value) }}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div class="col-6 mb-3">
                      <div class="card">
                        <div class="card-body p-2">
                          <div class="subheader small">수익/손실</div>
                          <div
                            class="h3 mb-0"
                            :class="getProfitLossClass(portfolioStore.summary.usd_profit_loss)"
                          >
                            {{ formatUSD(portfolioStore.summary.usd_profit_loss) }}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div class="col-6 mb-3">
                      <div class="card">
                        <div class="card-body p-2">
                          <div class="subheader small">수익률</div>
                          <div
                            class="h3 mb-0"
                            :class="getProfitLossClass(portfolioStore.summary.usd_profit_loss)"
                          >
                            {{ formatPercent(portfolioStore.summary.usd_return_rate) }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Right: Treemap (40%) -->
                <div class="col-lg-5">
                  <PortfolioTreemap 
                    :holdings="usdHoldings" 
                    chart-height="240px"
                  />
                </div>
              </div>
            </div>
            
            <!-- KRW Portfolio Section -->
            <div 
              :class="portfolioStore.summary.usd_cost_basis > 0 ? 'col-lg-6' : 'col-12'"
              v-if="portfolioStore.summary.krw_cost_basis > 0"
            >
              <h4 class="mb-3">한국 주식 (KRW)</h4>
              <div class="row">
                <!-- Left: Summary Cards (60%) -->
                <div class="col-lg-7">
                  <div class="row">
                    <div class="col-6 mb-3">
                      <div class="card">
                        <div class="card-body p-2">
                          <div class="subheader small">총 투자금</div>
                          <div class="h3 mb-0">
                            {{ formatKRW(portfolioStore.summary.krw_cost_basis) }}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div class="col-6 mb-3">
                      <div class="card">
                        <div class="card-body p-2">
                          <div class="subheader small">현재 가치</div>
                          <div class="h3 mb-0">
                            {{ formatKRW(portfolioStore.summary.krw_current_value) }}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div class="col-6 mb-3">
                      <div class="card">
                        <div class="card-body p-2">
                          <div class="subheader small">수익/손실</div>
                          <div
                            class="h3 mb-0"
                            :class="getProfitLossClass(portfolioStore.summary.krw_profit_loss)"
                          >
                            {{ formatKRW(portfolioStore.summary.krw_profit_loss) }}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div class="col-6 mb-3">
                      <div class="card">
                        <div class="card-body p-2">
                          <div class="subheader small">수익률</div>
                          <div
                            class="h3 mb-0"
                            :class="getProfitLossClass(portfolioStore.summary.krw_profit_loss)"
                          >
                            {{ formatPercent(portfolioStore.summary.krw_return_rate) }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Right: Treemap (40%) -->
                <div class="col-lg-5">
                  <PortfolioTreemap 
                    :holdings="krwHoldings" 
                    chart-height="240px"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Holdings table -->
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">보유 종목</h3>
              <div class="card-actions">
                <button class="btn btn-primary" @click="showAddModal = true">
                  <i class="ti ti-plus"></i>
                  종목 추가
                </button>
              </div>
            </div>
            
            <div class="card-body">
              <!-- Empty state -->
              <div v-if="portfolioStore.holdings.length === 0" class="empty">
                <div class="empty-icon">
                  <i class="ti ti-briefcase"></i>
                </div>
                <p class="empty-title">보유 종목이 없습니다</p>
                <p class="empty-subtitle text-muted">
                  첫 번째 종목을 추가해보세요
                </p>
              </div>
              
              <!-- Holdings table -->
              <div v-else class="table-responsive">
                <table class="table table-vcenter card-table">
                  <thead>
                    <tr>
                      <th>종목코드</th>
                      <th>회사명</th>
                      <th class="text-end">수량</th>
                      <th class="text-end">평균단가</th>
                      <th class="text-end">투자금</th>
                      <th class="text-end">현재가</th>
                      <th class="text-end">평가금액</th>
                      <th class="text-end">손익</th>
                      <th class="text-end">수익률</th>
                      <th class="w-1"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="holding in portfolioStore.holdings" :key="holding.id">
                      <td>
                        <router-link :to="`/stock/${holding.symbol}`" class="text-reset">
                          {{ holding.symbol }}
                        </router-link>
                      </td>
                      <td>
                        <div class="text-muted">{{ holding.company_name || holding.symbol }}</div>
                      </td>
                      <td class="text-end">{{ holding.quantity }}</td>
                      <td class="text-end">{{ formatCurrency(holding.avg_price, holding.symbol) }}</td>
                      <td class="text-end">{{ formatCurrency(holding.cost_basis, holding.symbol) }}</td>
                      <td class="text-end">{{ formatCurrency(holding.current_price, holding.symbol) }}</td>
                      <td class="text-end">{{ formatCurrency(holding.current_value, holding.symbol) }}</td>
                      <td class="text-end" :class="getProfitLossClass(holding.profit_loss)">
                        {{ formatCurrency(holding.profit_loss, holding.symbol) }}
                      </td>
                      <td class="text-end" :class="getProfitLossClass(holding.profit_loss)">
                        {{ formatPercent(holding.return_rate) }}
                      </td>
                      <td>
                        <div class="btn-list">
                          <button
                            class="btn btn-sm btn-ghost-primary"
                            @click="handleEdit(holding)"
                            title="수정"
                          >
                            <i class="ti ti-edit"></i>
                          </button>
                          <button
                            class="btn btn-sm btn-ghost-danger"
                            @click="handleRemove(holding.id)"
                            title="삭제"
                          >
                            <i class="ti ti-trash"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
    
    <!-- Add holding modal (placeholder) -->
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
                  v-model="newHolding.symbol"
                  type="text"
                  class="form-control"
                  placeholder="예: AAPL, 005930.KS"
                  required
                />
              </div>
              <div class="mb-3">
                <label class="form-label">수량</label>
                <input
                  v-model.number="newHolding.quantity"
                  type="number"
                  class="form-control"
                  placeholder="10"
                  min="1"
                  required
                />
              </div>
              <div class="mb-3">
                <label class="form-label">평균단가</label>
                <input
                  v-model.number="newHolding.avgPrice"
                  type="number"
                  class="form-control"
                  placeholder="175.50"
                  step="0.01"
                  min="0.01"
                  required
                />
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn me-auto" @click="showAddModal = false">취소</button>
              <button type="submit" class="btn btn-primary" :disabled="portfolioStore.loading">
                추가
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
    
    <!-- Edit holding modal -->
    <div v-if="showEditModal" class="modal modal-blur fade show" style="display: block;">
      <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">종목 수정</h5>
            <button type="button" class="btn-close" @click="closeEditModal"></button>
          </div>
          <form @submit.prevent="handleUpdate">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">종목코드</label>
                <input
                  type="text"
                  class="form-control"
                  :value="editHolding.symbol"
                  disabled
                />
              </div>
              <div class="mb-3">
                <label class="form-label">수량</label>
                <input
                  v-model.number="editHolding.quantity"
                  type="number"
                  class="form-control"
                  placeholder="10"
                  min="1"
                  required
                />
              </div>
              <div class="mb-3">
                <label class="form-label">평균단가</label>
                <input
                  v-model.number="editHolding.avgPrice"
                  type="number"
                  class="form-control"
                  placeholder="175.50"
                  step="0.01"
                  min="0.01"
                  required
                />
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn me-auto" @click="closeEditModal">취소</button>
              <button type="submit" class="btn btn-primary" :disabled="portfolioStore.loading">
                수정
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </app-layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePortfolioStore } from '@/stores/portfolio'
import AppLayout from '@/components/layout/AppLayout.vue'
import PortfolioTreemap from '@/components/portfolio/PortfolioTreemap.vue'

const portfolioStore = usePortfolioStore()

// State
const showAddModal = ref(false)
const showEditModal = ref(false)
const newHolding = ref({
  symbol: '',
  quantity: null,
  avgPrice: null
})
const editHolding = ref({
  id: null,
  symbol: '',
  quantity: null,
  avgPrice: null
})

// Computed
const currentPortfolioId = computed(() => portfolioStore.currentPortfolio?.id)
const profitLossClass = computed(() => {
  const profitLoss = portfolioStore.summary?.total_profit_loss || 0
  return profitLoss >= 0 ? 'text-success' : 'text-danger'
})

// Separate holdings by stock type
const usdHoldings = computed(() => {
  const usd = portfolioStore.holdings.filter(h => !h.symbol.includes('.'))
  console.log('USD Holdings:', usd)
  return usd
})

const krwHoldings = computed(() => {
  const krw = portfolioStore.holdings.filter(h => h.symbol.includes('.'))
  console.log('KRW Holdings:', krw)
  return krw
})

// Lifecycle
onMounted(async () => {
  await portfolioStore.fetchPortfolios()
  
  if (portfolioStore.portfolios.length > 0) {
    await portfolioStore.fetchPortfolioSummary(portfolioStore.portfolios[0].id)
  }
})

// Methods
async function selectPortfolio(portfolio) {
  portfolioStore.setCurrentPortfolio(portfolio)
  await portfolioStore.fetchPortfolioSummary(portfolio.id)
}

async function handleAdd() {
  try {
    await portfolioStore.addHolding(
      currentPortfolioId.value,
      newHolding.value.symbol,
      newHolding.value.quantity,
      newHolding.value.avgPrice
    )
    
    // Reset form and close modal
    newHolding.value = { symbol: '', quantity: null, avgPrice: null }
    showAddModal.value = false
  } catch (error) {
    console.error('Failed to add holding:', error)
  }
}

async function handleRemove(holdingId) {
  if (confirm('이 종목을 포트폴리오에서 삭제하시겠습니까?')) {
    try {
      await portfolioStore.removeHolding(currentPortfolioId.value, holdingId)
    } catch (error) {
      console.error('Failed to remove holding:', error)
    }
  }
}

function handleEdit(holding) {
  editHolding.value = {
    id: holding.id,
    symbol: holding.symbol,
    quantity: holding.quantity,
    avgPrice: holding.avg_price
  }
  showEditModal.value = true
}

async function handleUpdate() {
  try {
    await portfolioStore.updateHolding(
      currentPortfolioId.value,
      editHolding.value.id,
      {
        quantity: editHolding.value.quantity,
        avg_price: editHolding.value.avgPrice
      }
    )
    
    closeEditModal()
  } catch (error) {
    console.error('Failed to update holding:', error)
    alert('종목 수정에 실패했습니다.')
  }
}

function closeEditModal() {
  showEditModal.value = false
  editHolding.value = {
    id: null,
    symbol: '',
    quantity: null,
    avgPrice: null
  }
}

// Check if symbol is US stock (doesn't end with .KS, .KQ, etc)
function isUSStock(symbol) {
  if (!symbol) return false
  return !symbol.includes('.')
}

function formatCurrency(value, symbol = null) {
  if (value === null || value === undefined) return '-'
  
  // For holdings table, check if symbol is US stock
  if (symbol && isUSStock(symbol)) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  }
  
  // Default to KRW for summary cards or Korean stocks
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW'
  }).format(value)
}

function formatUSD(value) {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value)
}

function formatKRW(value) {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW'
  }).format(value)
}

function formatPercent(value) {
  if (value === null || value === undefined) return '-'
  return `${value >= 0 ? '+' : ''}${Number(value).toFixed(2)}%`
}

function getProfitLossClass(value) {
  if (value === null || value === undefined) return ''
  return value >= 0 ? 'text-success' : 'text-danger'
}
</script>

<style scoped>
.modal.show {
  background-color: rgba(0, 0, 0, 0.5);
}
</style>
