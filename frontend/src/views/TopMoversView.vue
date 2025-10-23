<template>
  <app-layout page-title="급등락 종목" page-subtitle="시장 동향">
    <!-- Last updated info -->
    <div v-if="topMoversStore.lastUpdated" class="row mb-3">
      <div class="col-12">
        <div class="alert alert-info d-flex align-items-center">
          <i class="ti ti-info-circle me-2"></i>
          <span>
            마지막 업데이트: {{ formatLastUpdated(topMoversStore.lastUpdated) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="topMoversStore.loading" class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body text-center py-5">
            <div class="spinner-border text-primary mb-3"></div>
            <p class="text-muted mb-0">데이터를 불러오는 중...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="topMoversStore.error" class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <div class="empty">
              <div class="empty-icon">
                <i class="ti ti-alert-circle text-danger"></i>
              </div>
              <p class="empty-title">데이터를 불러오지 못했습니다</p>
              <p class="empty-subtitle text-muted">
                {{ topMoversStore.error }}
              </p>
              <div class="empty-action">
                <button class="btn btn-primary" @click="handleRetry">
                  <i class="ti ti-reload"></i>
                  다시 시도
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Top Movers Content -->
    <div v-else class="row row-deck row-cards">
      <!-- Top Gainers -->
      <div class="col-12 mb-4">
        <TopMoversList
          title="급등 상위 종목"
          icon="📈"
          :movers="topMoversStore.topGainers"
          :max-items="20"
        />
      </div>

      <!-- Top Losers -->
      <div class="col-12 mb-4">
        <TopMoversList
          title="급락 상위 종목"
          icon="📉"
          :movers="topMoversStore.topLosers"
          :max-items="20"
        />
      </div>

      <!-- Most Actively Traded -->
      <div class="col-12 mb-4">
        <TopMoversList
          title="거래량 상위 종목"
          icon="🔥"
          :movers="topMoversStore.mostActivelyTraded"
          :max-items="20"
        />
      </div>
    </div>
  </app-layout>
</template>

<script setup>
import { onMounted } from 'vue'
import { useTopMoversStore } from '@/stores/topmovers'
import AppLayout from '@/components/layout/AppLayout.vue'
import TopMoversList from '@/components/topmovers/TopMoversList.vue'

const topMoversStore = useTopMoversStore()

onMounted(async () => {
  await fetchData()
})

async function fetchData() {
  try {
    await topMoversStore.fetchTopMovers()
  } catch (error) {
    console.error('Failed to fetch top movers:', error)
  }
}

async function handleRetry() {
  topMoversStore.clearError()
  await fetchData()
}

function formatLastUpdated(timestamp) {
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  } catch (error) {
    return timestamp
  }
}
</script>

<style scoped>
.alert {
  border-radius: 0.5rem;
}

.empty {
  padding: 3rem 1rem;
}

.empty-icon {
  font-size: 3rem;
  color: var(--tblr-muted);
  margin-bottom: 1rem;
}

.empty-icon i {
  font-size: 3rem;
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.empty-subtitle {
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}
</style>
