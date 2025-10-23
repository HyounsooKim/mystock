import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiClient from '@/api/client'

export const useTopMoversStore = defineStore('topmovers', () => {
  // State
  const topGainers = ref([])
  const topLosers = ref([])
  const mostActivelyTraded = ref([])
  const lastUpdated = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Actions
  async function fetchTopMovers() {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get('/stocks/top-movers')
      
      topGainers.value = response.data.top_gainers || []
      topLosers.value = response.data.top_losers || []
      mostActivelyTraded.value = response.data.most_actively_traded || []
      lastUpdated.value = response.data.last_updated
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '급등락 종목 조회에 실패했습니다.'
      console.error('Error fetching top movers:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    topGainers,
    topLosers,
    mostActivelyTraded,
    lastUpdated,
    loading,
    error,
    // Actions
    fetchTopMovers,
    clearError
  }
})
