import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    // Debug log
    console.log('[API Client] Token from store:', authStore.token ? `${authStore.token.substring(0, 20)}...` : 'null')
    
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
      console.log('[API Client] Added Authorization header')
    } else {
      console.log('[API Client] No token available')
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      // Handle 401 Unauthorized - token expired or invalid
      if (error.response.status === 401) {
        const authStore = useAuthStore()
        authStore.logout()
        router.push('/login')
      }
      
      // Handle other errors
      console.error('API Error:', error.response.data)
    } else if (error.request) {
      console.error('Network Error:', error.message)
    } else {
      console.error('Request Error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

// API functions for stocks
export const stocksApi = {
  async getTopMovers() {
    const response = await apiClient.get('/stocks/market/top-movers')
    return response.data
  }
}

export default apiClient
