<template>
  <div class="card">
    <div class="card-header" :class="headerClass">
      <h3 class="card-title">
        <i :class="iconClass" class="me-2"></i>
        {{ title }}
      </h3>
    </div>
    <div class="card-body p-0">
      <div v-if="stocks.length === 0" class="text-center py-5 text-muted">
        <i class="ti ti-info-circle" style="font-size: 2rem;"></i>
        <p class="mt-2">데이터가 없습니다</p>
      </div>
      <div v-else class="table-responsive">
        <table class="table table-vcenter card-table table-hover">
          <thead>
            <tr>
              <th class="w-1">#</th>
              <th class="sortable-header" @click="toggleSort('ticker')">
                티커
                <i v-if="sortKey === 'ticker'" :class="sortIcon" class="ms-1"></i>
              </th>
              <th>회사명</th>
              <th class="text-end sortable-header" @click="toggleSort('price')">
                가격
                <i v-if="sortKey === 'price'" :class="sortIcon" class="ms-1"></i>
              </th>
              <th class="text-end sortable-header" @click="toggleSort('change_amount')">
                변화
                <i v-if="sortKey === 'change_amount'" :class="sortIcon" class="ms-1"></i>
              </th>
              <th class="text-end sortable-header" @click="toggleSort('change_percentage')">
                변화율
                <i v-if="sortKey === 'change_percentage'" :class="sortIcon" class="ms-1"></i>
              </th>
              <th class="text-end sortable-header" @click="toggleSort('volume')">
                거래량
                <i v-if="sortKey === 'volume'" :class="sortIcon" class="ms-1"></i>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(stock, index) in displayedStocks"
              :key="stock.ticker"
              @click="navigateToStock(stock.ticker)"
              class="cursor-pointer"
            >
              <td class="text-muted">{{ index + 1 }}</td>
              <td>
                <strong class="ticker-symbol">{{ stock.ticker }}</strong>
              </td>
              <td>
                <span class="text-muted">{{ getCompanyNameSync(stock.ticker) }}</span>
              </td>
              <td class="text-end">
                <span class="price-value">${{ formatPrice(stock.price) }}</span>
              </td>
              <td class="text-end" :class="getChangeClass(stock.change_amount)">
                {{ formatChange(stock.change_amount) }}
              </td>
              <td class="text-end" :class="getChangeClass(stock.change_amount)">
                <strong>{{ formatPercentage(stock.change_percentage) }}</strong>
              </td>
              <td class="text-end text-muted">
                {{ formatVolume(stock.volume) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCompanyNameSync } from '@/utils/symbolLookup'

const router = useRouter()

const props = defineProps({
  stocks: {
    type: Array,
    required: true,
    default: () => []
  },
  type: {
    type: String,
    required: true,
    validator: (value) => ['gainers', 'losers', 'active'].includes(value)
  },
  title: {
    type: String,
    required: true
  },
  maxItems: {
    type: Number,
    default: 20
  }
})

// Sorting state
const sortKey = ref(null)
const sortOrder = ref('asc') // 'asc' or 'desc'

const headerClass = computed(() => {
  switch (props.type) {
    case 'gainers':
      return 'bg-red-lt'
    case 'losers':
      return 'bg-blue-lt'
    case 'active':
      return 'bg-gray-lt'
    default:
      return ''
  }
})

const iconClass = computed(() => {
  switch (props.type) {
    case 'gainers':
      return 'ti ti-trending-up text-red'
    case 'losers':
      return 'ti ti-trending-down text-blue'
    case 'active':
      return 'ti ti-activity text-gray'
    default:
      return 'ti ti-chart-line'
  }
})

const sortIcon = computed(() => {
  return sortOrder.value === 'asc' ? 'ti ti-arrow-up' : 'ti ti-arrow-down'
})

const sortedStocks = computed(() => {
  if (!sortKey.value) {
    return props.stocks
  }

  const sorted = [...props.stocks].sort((a, b) => {
    let aVal, bVal

    switch (sortKey.value) {
      case 'ticker':
        aVal = a.ticker
        bVal = b.ticker
        break
      case 'price':
        aVal = parseFloat(a.price)
        bVal = parseFloat(b.price)
        break
      case 'change_amount':
        aVal = parseFloat(a.change_amount)
        bVal = parseFloat(b.change_amount)
        break
      case 'change_percentage':
        aVal = parseFloat(String(a.change_percentage).replace('%', ''))
        bVal = parseFloat(String(b.change_percentage).replace('%', ''))
        break
      case 'volume':
        aVal = parseInt(a.volume)
        bVal = parseInt(b.volume)
        break
      default:
        return 0
    }

    if (sortKey.value === 'ticker') {
      // String comparison
      if (sortOrder.value === 'asc') {
        return aVal.localeCompare(bVal)
      } else {
        return bVal.localeCompare(aVal)
      }
    } else {
      // Numeric comparison
      if (sortOrder.value === 'asc') {
        return aVal - bVal
      } else {
        return bVal - aVal
      }
    }
  })

  return sorted
})

const displayedStocks = computed(() => {
  return sortedStocks.value.slice(0, props.maxItems)
})

function formatPrice(price) {
  const numPrice = parseFloat(price)
  if (numPrice >= 1) {
    return numPrice.toFixed(3)
  }
  return numPrice.toFixed(3)
}

function formatChange(change) {
  const numChange = parseFloat(change)
  if (numChange > 0) {
    return `+${numChange.toFixed(2)}`
  }
  return numChange.toFixed(2)
}

function formatPercentage(percentage) {
  // Remove '%' if present and parse as float
  const percentStr = String(percentage).replace('%', '')
  const numPercent = parseFloat(percentStr)
  if (isNaN(numPercent)) {
    return percentage
  }
  return `${numPercent.toFixed(2)}%`
}

function toggleSort(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

function formatVolume(volume) {
  const numVolume = parseInt(volume)
  if (numVolume >= 1_000_000_000) {
    return `${(numVolume / 1_000_000_000).toFixed(2)}B`
  } else if (numVolume >= 1_000_000) {
    return `${(numVolume / 1_000_000).toFixed(2)}M`
  } else if (numVolume >= 1_000) {
    return `${(numVolume / 1_000).toFixed(2)}K`
  }
  return numVolume.toString()
}

function getChangeClass(change) {
  const numChange = parseFloat(change)
  if (numChange > 0) {
    return 'text-green'
  } else if (numChange < 0) {
    return 'text-red'
  }
  return ''
}

function navigateToStock(ticker) {
  router.push(`/stock/${ticker}`)
}
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}

.cursor-pointer:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

[data-bs-theme="dark"] .cursor-pointer:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.sortable-header:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

[data-bs-theme="dark"] .sortable-header:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.sortable-header i {
  font-size: 0.8rem;
  margin-left: 0.25rem;
  vertical-align: middle;
}

.ticker-symbol {
  font-family: monospace;
  font-size: 0.95rem;
}

.price-value {
  font-family: monospace;
  font-size: 0.9rem;
}

.bg-red-lt {
  background-color: rgba(214, 57, 57, 0.1);
}

.bg-blue-lt {
  background-color: rgba(59, 130, 246, 0.1);
}

.bg-gray-lt {
  background-color: rgba(107, 114, 128, 0.1);
}

.text-red {
  color: #d63939;
}

.text-green {
  color: #2fb344;
}

.text-blue {
  color: #3b82f6;
}

.text-gray {
  color: #6b7280;
}

[data-bs-theme="dark"] .bg-red-lt {
  background-color: rgba(214, 57, 57, 0.15);
}

[data-bs-theme="dark"] .bg-blue-lt {
  background-color: rgba(59, 130, 246, 0.15);
}

[data-bs-theme="dark"] .bg-gray-lt {
  background-color: rgba(107, 114, 128, 0.15);
}
</style>
