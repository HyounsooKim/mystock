<template>
  <div 
    class="card card-sm card-hover" 
    @click="handleClick"
    style="cursor: pointer; transition: all 0.2s;"
  >
    <div class="card-body">
      <div class="row align-items-center">
        <div class="col">
          <div class="font-weight-medium mb-1">
            {{ mover.ticker }}
          </div>
          <div class="text-muted small">
            ${{ parseFloat(mover.price).toFixed(2) }}
          </div>
        </div>
        <div class="col-auto">
          <div 
            class="badge"
            :class="changeColor"
          >
            {{ mover.change_percentage }}
          </div>
          <div 
            class="text-muted small mt-1"
            :class="changeTextColor"
          >
            {{ formattedChangeAmount }}
          </div>
        </div>
      </div>
      <div class="text-muted small mt-2">
        <i class="ti ti-chart-bar"></i>
        Vol: {{ formattedVolume }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  mover: {
    type: Object,
    required: true,
    validator: (value) => {
      return value.ticker && value.price && value.change_percentage
    }
  }
})

const emit = defineEmits(['click'])

const changeAmount = computed(() => {
  return parseFloat(props.mover.change_amount || 0)
})

const isPositive = computed(() => {
  return changeAmount.value >= 0
})

const changeColor = computed(() => {
  return isPositive.value ? 'badge-success-subtle' : 'badge-danger-subtle'
})

const changeTextColor = computed(() => {
  return isPositive.value ? 'text-success' : 'text-danger'
})

const formattedChangeAmount = computed(() => {
  const amount = changeAmount.value
  const sign = amount >= 0 ? '+' : ''
  return `${sign}$${Math.abs(amount).toFixed(2)}`
})

const formattedVolume = computed(() => {
  const volume = parseInt(props.mover.volume || 0)
  if (volume >= 1_000_000_000) {
    return `${(volume / 1_000_000_000).toFixed(2)}B`
  } else if (volume >= 1_000_000) {
    return `${(volume / 1_000_000).toFixed(2)}M`
  } else if (volume >= 1_000) {
    return `${(volume / 1_000).toFixed(2)}K`
  }
  return volume.toString()
})

function handleClick() {
  emit('click', props.mover.ticker)
}
</script>

<style scoped>
.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.font-weight-medium {
  font-weight: 600;
  font-size: 1rem;
}

.badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}

.badge-success-subtle {
  background-color: rgba(47, 179, 68, 0.1);
  color: var(--tblr-success);
}

.badge-danger-subtle {
  background-color: rgba(214, 57, 57, 0.1);
  color: var(--tblr-danger);
}
</style>
