<template>
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">
        <span class="me-2">{{ icon }}</span>
        {{ title }}
      </h3>
    </div>
    <div class="card-body">
      <!-- Empty state -->
      <div v-if="!movers || movers.length === 0" class="text-center py-4 text-muted">
        <i class="ti ti-info-circle fs-1 mb-2"></i>
        <p class="mb-0">데이터가 없습니다</p>
      </div>

      <!-- Movers grid -->
      <div v-else class="row g-3">
        <div 
          v-for="(mover, index) in displayedMovers" 
          :key="mover.ticker"
          class="col-12 col-md-6 col-lg-4 col-xl-3"
        >
          <TopMoverCard 
            :mover="mover"
            @click="handleStockClick"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import TopMoverCard from './TopMoverCard.vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    default: '📊'
  },
  movers: {
    type: Array,
    default: () => []
  },
  maxItems: {
    type: Number,
    default: 20
  }
})

const router = useRouter()

const displayedMovers = computed(() => {
  return props.movers.slice(0, props.maxItems)
})

function handleStockClick(symbol) {
  router.push(`/stock/${symbol}`)
}
</script>

<style scoped>
.fs-1 {
  font-size: 2rem;
}
</style>
