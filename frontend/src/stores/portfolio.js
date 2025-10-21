import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

export const usePortfolioStore = defineStore('portfolio', () => {
  // State
  const portfolios = ref([])
  const currentPortfolio = ref(null)
  const holdings = ref([])
  const summary = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const hasPortfolios = computed(() => portfolios.value.length > 0)
  const currentPortfolioName = computed(() => currentPortfolio.value?.name || '')
  const totalHoldings = computed(() => summary.value?.total_holdings || 0)
  const isAtLimit = computed(() => totalHoldings.value >= 100)

  // Actions
  async function fetchPortfolios() {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get('/portfolios')
      portfolios.value = response.data
      
      // Set first portfolio as current if none selected
      if (!currentPortfolio.value && response.data.length > 0) {
        currentPortfolio.value = response.data[0]
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '포트폴리오 조회에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchPortfolioSummary(portfolioId) {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get(`/portfolios/${portfolioId}/summary`)
      
      currentPortfolio.value = response.data.portfolio
      holdings.value = response.data.holdings
      summary.value = response.data.summary
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '포트폴리오 요약 조회에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addHolding(portfolioId, symbol, quantity, avgPrice, notes = null) {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.post(`/portfolios/${portfolioId}/holdings`, {
        symbol: symbol.toUpperCase(),
        quantity: parseInt(quantity),
        avg_price: parseFloat(avgPrice),
        notes
      })
      
      // Refresh portfolio summary
      await fetchPortfolioSummary(portfolioId)
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '종목 추가에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateHolding(portfolioId, holdingId, data) {
    loading.value = true
    error.value = null
    
    try {
      const updateData = {}
      
      if (data.quantity !== undefined) {
        updateData.quantity = parseInt(data.quantity)
      }
      if (data.avg_price !== undefined) {
        updateData.avg_price = parseFloat(data.avg_price)
      }
      if (data.notes !== undefined) {
        updateData.notes = data.notes
      }
      
      const response = await apiClient.put(
        `/portfolios/${portfolioId}/holdings/${holdingId}`,
        updateData
      )
      
      // Update in local state
      const index = holdings.value.findIndex(h => h.id === holdingId)
      if (index !== -1) {
        holdings.value[index] = response.data
      }
      
      // Refresh summary calculations
      await fetchPortfolioSummary(portfolioId)
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '종목 수정에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function removeHolding(portfolioId, holdingId) {
    loading.value = true
    error.value = null
    
    try {
      await apiClient.delete(`/portfolios/${portfolioId}/holdings/${holdingId}`)
      
      // Remove from local state
      holdings.value = holdings.value.filter(h => h.id !== holdingId)
      
      // Refresh summary
      await fetchPortfolioSummary(portfolioId)
    } catch (err) {
      error.value = err.response?.data?.detail || '종목 삭제에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  function setCurrentPortfolio(portfolio) {
    currentPortfolio.value = portfolio
  }

  function clearError() {
    error.value = null
  }

  function resetStore() {
    portfolios.value = []
    currentPortfolio.value = null
    holdings.value = []
    summary.value = null
    loading.value = false
    error.value = null
  }

  return {
    // State
    portfolios,
    currentPortfolio,
    holdings,
    summary,
    loading,
    error,
    
    // Getters
    hasPortfolios,
    currentPortfolioName,
    totalHoldings,
    isAtLimit,
    
    // Actions
    fetchPortfolios,
    fetchPortfolioSummary,
    addHolding,
    updateHolding,
    removeHolding,
    setCurrentPortfolio,
    clearError,
    resetStore
  }
})
