import { defineStore } from 'pinia'
import apiClient from '@/api/client'

export const useTopMoversStore = defineStore('topMovers', {
  state: () => ({
    topMovers: null,
    loading: false,
    error: null,
    lastUpdated: null
  }),

  getters: {
    hasData: (state) => !!state.topMovers,
    
    isStale: (state) => {
      if (!state.lastUpdated) return true
      const fifteenMinutes = 15 * 60 * 1000
      return Date.now() - state.lastUpdated > fifteenMinutes
    },

    topGainers: (state) => state.topMovers?.top_gainers || [],
    topLosers: (state) => state.topMovers?.top_losers || [],
    mostActive: (state) => state.topMovers?.most_actively_traded || [],
    lastUpdatedTime: (state) => state.topMovers?.last_updated || ''
  },

  actions: {
    async fetchTopMovers() {
      this.loading = true
      this.error = null
      
      try {
        const response = await apiClient.get('/stocks/top-movers')
        this.topMovers = response.data
        this.lastUpdated = Date.now()
      } catch (error) {
        console.error('Error fetching top movers:', error)
        this.error = error.response?.data?.detail || 'Failed to fetch top movers data'
        throw error
      } finally {
        this.loading = false
      }
    },

    async refreshTopMovers() {
      await this.fetchTopMovers()
    },

    clearError() {
      this.error = null
    }
  }
})
