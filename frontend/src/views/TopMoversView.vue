<template>
  <app-layout page-title="급등락 종목" page-subtitle="시장 동향">
    <div class="row row-cards">
      <div class="col-12">
        <!-- Last updated info and refresh button -->
        <div class="card mb-3">
          <div class="card-body d-flex justify-content-between align-items-center">
            <div>
              <i class="ti ti-clock me-2"></i>
              <span class="text-muted">마지막 업데이트: </span>
              <strong>{{ lastUpdated || 'N/A' }}</strong>
            </div>
            <button 
              class="btn btn-primary"
              @click="refreshData"
              :disabled="loading"
            >
              <i class="ti ti-refresh" :class="{ 'spinning': loading }"></i>
              새로고침
            </button>
          </div>
        </div>
      </div>
      
      <!-- Loading state -->
      <div v-if="loading" class="col-12">
        <div class="card">
          <div class="card-body text-center py-5">
            <div class="spinner-border text-primary mb-3"></div>
            <p class="text-muted">데이터를 불러오는 중...</p>
          </div>
        </div>
      </div>
      
      <!-- Error state -->
      <div v-else-if="error" class="col-12">
        <div class="alert alert-danger">
          <i class="ti ti-alert-circle me-2"></i>
          {{ error }}
        </div>
      </div>
      
      <!-- Data display -->
      <template v-else>
        <!-- Top Gainers -->
        <div class="col-12 col-md-6 col-lg-4">
          <div class="card h-100">
            <top-movers-list
              title="급등 TOP 20"
              :items="topGainers"
              type="gainer"
            />
          </div>
        </div>
        
        <!-- Top Losers -->
        <div class="col-12 col-md-6 col-lg-4">
          <div class="card h-100">
            <top-movers-list
              title="급락 TOP 20"
              :items="topLosers"
              type="loser"
            />
          </div>
        </div>
        
        <!-- Most Active -->
        <div class="col-12 col-md-6 col-lg-4">
          <div class="card h-100">
            <top-movers-list
              title="거래량 TOP 20"
              :items="mostActive"
              type="active"
            />
          </div>
        </div>
      </template>
    </div>
  </app-layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import TopMoversList from '@/components/movers/TopMoversList.vue'
import { stocksApi } from '@/api/client'

// State
const loading = ref(false)
const error = ref(null)
const topGainers = ref([])
const topLosers = ref([])
const mostActive = ref([])
const lastUpdated = ref('')

// Methods
async function fetchTopMovers() {
  loading.value = true
  error.value = null
  
  try {
    const data = await stocksApi.getTopMovers()
    
    topGainers.value = data.top_gainers || []
    topLosers.value = data.top_losers || []
    mostActive.value = data.most_actively_traded || []
    lastUpdated.value = data.last_updated || ''
  } catch (err) {
    console.error('Failed to fetch top movers:', err)
    error.value = err.response?.data?.detail || '데이터를 불러오는데 실패했습니다. 나중에 다시 시도해주세요.'
  } finally {
    loading.value = false
  }
}

function refreshData() {
  fetchTopMovers()
}

// Lifecycle
onMounted(() => {
  fetchTopMovers()
})
</script>

<style scoped>
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Ensure equal height cards on desktop */
@media (min-width: 992px) {
  .row-cards > [class*='col-'] {
    display: flex;
    flex-direction: column;
  }
  
  .row-cards > [class*='col-'] .card {
    flex: 1;
  }
}
</style>
