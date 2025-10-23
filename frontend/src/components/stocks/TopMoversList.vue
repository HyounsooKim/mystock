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
              <th>티커</th>
              <th class="text-end">가격</th>
              <th class="text-end">변화</th>
              <th class="text-end">변화율</th>
              <th class="text-end">거래량</th>
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
              <td class="text-end">
                <span class="price-value">${{ formatPrice(stock.price) }}</span>
              </td>
              <td class="text-end" :class="getChangeClass(stock.change_amount)">
                {{ formatChange(stock.change_amount) }}
              </td>
              <td class="text-end" :class="getChangeClass(stock.change_amount)">
                <strong>{{ stock.change_percentage }}</strong>
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'

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

const displayedStocks = computed(() => {
  return props.stocks.slice(0, props.maxItems)
})

function formatPrice(price) {
  const numPrice = parseFloat(price)
  if (numPrice >= 1) {
    return numPrice.toFixed(2)
  }
  return numPrice.toFixed(4)
}

function formatChange(change) {
  const numChange = parseFloat(change)
  if (numChange > 0) {
    return `+${numChange.toFixed(2)}`
  }
  return numChange.toFixed(2)
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
