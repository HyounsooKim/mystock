<template>
  <AppLayout
    page-title="급등락 종목들"
    page-subtitle="Top Market Movers"
  >
    <!-- Error Alert -->
    <div v-if="error" class="alert alert-danger alert-dismissible" role="alert">
      <div class="d-flex">
        <div>
          <i class="ti ti-alert-circle me-2"></i>
        </div>
        <div>
          <h4 class="alert-title">데이터 로드 실패</h4>
          <div class="text-muted">{{ error }}</div>
        </div>
      </div>
      <a class="btn-close" @click="clearError"></a>
    </div>

    <!-- Last Updated Info -->
    <div v-if="lastUpdatedTime && !loading" class="mb-3">
      <div class="text-muted">
        <i class="ti ti-clock me-1"></i>
        마지막 업데이트: {{ lastUpdatedTime }}
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !hasData" class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body text-center py-5">
            <div class="spinner-border text-primary mb-3" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted">데이터를 불러오는 중...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Top Movers Content -->
    <div v-else-if="hasData" class="row row-cols-1 row-cols-md-3 g-4">
      <!-- Top Gainers -->
      <div class="col">
        <TopMoversList
          :stocks="topGainers"
          type="gainers"
          title="급등 종목"
        />
      </div>

      <!-- Top Losers -->
      <div class="col">
        <TopMoversList
          :stocks="topLosers"
          type="losers"
          title="급락 종목"
        />
      </div>

      <!-- Most Active -->
      <div class="col">
        <TopMoversList
          :stocks="mostActive"
          type="active"
          title="거래량 상위"
        />
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!loading && !hasData" class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body text-center py-5">
            <i class="ti ti-chart-line text-muted" style="font-size: 4rem;"></i>
            <h3 class="mt-3">데이터 없음</h3>
            <p class="text-muted">급등락 종목 데이터를 불러올 수 없습니다.</p>
            <button @click="refresh" class="btn btn-primary mt-3">
              <i class="ti ti-refresh me-2"></i>
              다시 시도
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Refresh Button (Floating) -->
    <div v-if="hasData" class="floating-refresh">
      <button
        @click="refresh"
        class="btn btn-primary btn-icon"
        :disabled="loading"
        title="새로고침"
      >
        <i class="ti ti-refresh" :class="{ 'spinning': loading }"></i>
      </button>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useTopMoversStore } from '@/stores/topMovers'
import AppLayout from '@/components/layout/AppLayout.vue'
import TopMoversList from '@/components/stocks/TopMoversList.vue'

const topMoversStore = useTopMoversStore()

// Computed properties
const loading = computed(() => topMoversStore.loading)
const error = computed(() => topMoversStore.error)
const hasData = computed(() => topMoversStore.hasData)
const topGainers = computed(() => topMoversStore.topGainers)
const topLosers = computed(() => topMoversStore.topLosers)
const mostActive = computed(() => topMoversStore.mostActive)
const lastUpdatedTime = computed(() => topMoversStore.lastUpdatedTime)

// Methods
async function refresh() {
  try {
    await topMoversStore.refreshTopMovers()
  } catch (err) {
    console.error('Failed to refresh top movers:', err)
  }
}

function clearError() {
  topMoversStore.clearError()
}

// Lifecycle
onMounted(async () => {
  // Fetch data if not already loaded or if stale
  if (!hasData.value || topMoversStore.isStale) {
    try {
      await topMoversStore.fetchTopMovers()
    } catch (err) {
      console.error('Failed to fetch top movers:', err)
    }
  }
})
</script>

<style scoped>
.floating-refresh {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
}

.btn-icon {
  width: 3rem;
  height: 3rem;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 1.25rem;
}

.btn-icon:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

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

/* Responsive adjustments */
@media (max-width: 767px) {
  .floating-refresh {
    bottom: 1rem;
    right: 1rem;
  }

  .btn-icon {
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1rem;
  }
}
</style>
