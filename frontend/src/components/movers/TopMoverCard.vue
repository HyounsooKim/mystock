<template>
  <div 
    class="mover-card" 
    :class="moverClass"
    @click="goToDetail"
  >
    <div class="ticker">{{ ticker }}</div>
    <div class="change-pct" :class="changeClass">{{ changePercentage }}</div>
    <div class="price">${{ price }}</div>
    <div class="volume">{{ formattedVolume }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  ticker: {
    type: String,
    required: true
  },
  price: {
    type: String,
    required: true
  },
  changePercentage: {
    type: String,
    required: true
  },
  volume: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'neutral',
    validator: (value) => ['gainer', 'loser', 'active'].includes(value)
  }
})

const router = useRouter()

const moverClass = computed(() => {
  return `mover-${props.type}`
})

const changeClass = computed(() => {
  const percentage = parseFloat(props.changePercentage)
  if (percentage > 0) return 'positive'
  if (percentage < 0) return 'negative'
  return 'neutral'
})

const formattedVolume = computed(() => {
  const vol = parseInt(props.volume)
  if (vol >= 1000000000) {
    return (vol / 1000000000).toFixed(1) + 'B'
  } else if (vol >= 1000000) {
    return (vol / 1000000).toFixed(1) + 'M'
  } else if (vol >= 1000) {
    return (vol / 1000).toFixed(1) + 'K'
  }
  return vol.toString()
})

function goToDetail() {
  router.push(`/stock/${props.ticker}`)
}
</script>

<style scoped>
.mover-card {
  padding: 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid var(--tblr-border-color);
  background: var(--tblr-card-bg, #fff);
  margin-bottom: 0.5rem;
}

.mover-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--tblr-primary);
}

.mover-card .ticker {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--tblr-body-color);
}

.mover-card .change-pct {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.mover-card .change-pct.positive {
  color: #2fb344;
}

.mover-card .change-pct.negative {
  color: #d63939;
}

.mover-card .change-pct.neutral {
  color: var(--tblr-secondary);
}

.mover-card .price {
  font-size: 0.9rem;
  color: var(--tblr-secondary);
  margin-bottom: 0.25rem;
}

.mover-card .volume {
  font-size: 0.85rem;
  color: var(--tblr-muted);
}

/* Dark mode support */
[data-bs-theme="dark"] .mover-card {
  background: var(--tblr-bg-surface);
  border-color: var(--tblr-border-color-translucent);
}

[data-bs-theme="dark"] .mover-card:hover {
  border-color: var(--tblr-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
</style>
