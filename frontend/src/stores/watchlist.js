import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

export const useWatchlistStore = defineStore('watchlist', () => {
  // State
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const count = computed(() => items.value.length)
  const hasItems = computed(() => items.value.length > 0)
  const isAtLimit = computed(() => items.value.length >= 50)

  // Actions
  async function fetchWatchlist() {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get('/watchlist')
      items.value = response.data.items
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '관심종목 조회에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addStock(symbol, notes = null) {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.post('/watchlist', {
        symbol: symbol.toUpperCase(),
        notes
      })
      
      // Refresh watchlist
      await fetchWatchlist()
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '종목 추가에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateStock(symbol, data) {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.put(`/watchlist/${symbol}`, data)
      
      // Update in local state
      const index = items.value.findIndex(item => item.symbol === symbol)
      if (index !== -1) {
        items.value[index] = { ...items.value[index], ...data }
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '종목 수정에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function removeStock(symbol) {
    loading.value = true
    error.value = null
    
    try {
      await apiClient.delete(`/watchlist/${symbol}`)
      
      // Remove from local state
      items.value = items.value.filter(item => item.symbol !== symbol)
    } catch (err) {
      error.value = err.response?.data?.detail || '종목 삭제에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function reorderWatchlist(symbolOrder) {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.put('/watchlist/reorder', {
        symbol_order: symbolOrder
      })
      
      // Update local state with new order from response
      items.value = response.data.items
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '순서 변경에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateNotes(symbol, notes) {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.put(`/watchlist/${symbol}`, {
        notes
      })
      
      // Update in local state
      const index = items.value.findIndex(item => item.symbol === symbol)
      if (index !== -1) {
        items.value[index].notes = notes
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '메모 수정에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  function resetStore() {
    items.value = []
    loading.value = false
    error.value = null
  }

  return {
    // State
    items,
    loading,
    error,
    
    // Getters
    count,
    hasItems,
    isAtLimit,
    
    // Actions
    fetchWatchlist,
    addStock,
    updateStock,
    updateNotes,
    removeStock,
    reorderWatchlist,
    clearError,
    resetStore
  }
})
