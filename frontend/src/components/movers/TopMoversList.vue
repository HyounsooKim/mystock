<template>
  <div class="movers-list">
    <div class="list-header">
      <h3 class="list-title">{{ title }}</h3>
      <span class="list-badge">{{ items.length }}</span>
    </div>
    <div class="list-content">
      <top-mover-card
        v-for="item in items"
        :key="item.ticker"
        :ticker="item.ticker"
        :price="item.price"
        :change-percentage="item.change_percentage"
        :volume="item.volume"
        :type="type"
      />
      
      <!-- Empty state -->
      <div v-if="items.length === 0" class="empty-state">
        <i class="ti ti-info-circle"></i>
        <p>데이터가 없습니다</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import TopMoverCard from './TopMoverCard.vue'

defineProps({
  title: {
    type: String,
    required: true
  },
  items: {
    type: Array,
    default: () => []
  },
  type: {
    type: String,
    default: 'neutral',
    validator: (value) => ['gainer', 'loser', 'active'].includes(value)
  }
})
</script>

<style scoped>
.movers-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 2px solid var(--tblr-border-color);
  background: var(--tblr-bg-surface-secondary);
  border-radius: 8px 8px 0 0;
}

.list-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--tblr-body-color);
}

.list-badge {
  background: var(--tblr-primary);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  max-height: calc(100vh - 300px);
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--tblr-muted);
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 1rem;
}

/* Dark mode support */
[data-bs-theme="dark"] .list-header {
  background: var(--tblr-bg-surface);
}
</style>
