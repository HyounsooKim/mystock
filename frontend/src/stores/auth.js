import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(null)
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const userName = computed(() => user.value?.name || '')
  const userEmail = computed(() => user.value?.email || '')

  // Actions
  function initializeAuth() {
    // Load token and user from localStorage on app start
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('auth_user')
    
    if (storedToken && storedUser) {
      token.value = storedToken
      user.value = JSON.parse(storedUser)
    }
  }

  async function register(email, password) {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.post('/auth/register', {
        email,
        password
      })
      
      const { token: tokenData, user: userData } = response.data
      const access_token = tokenData.access_token
      
      // Save to state (registration already includes token)
      token.value = access_token
      user.value = userData
      
      // Save to localStorage
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('auth_user', JSON.stringify(userData))
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '회원가입에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function login(email, password) {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.post('/auth/login', {
        email,
        password
      })
      
      console.log('[Auth Store] Login response:', response.data)
      
      const { token: tokenData, user: userData } = response.data
      const access_token = tokenData.access_token
      
      console.log('[Auth Store] Extracted token:', access_token ? `${access_token.substring(0, 20)}...` : 'null')
      console.log('[Auth Store] User data:', userData)
      
      // Save to state
      token.value = access_token
      user.value = userData
      
      // Save to localStorage
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('auth_user', JSON.stringify(userData))
      
      console.log('[Auth Store] Token saved. Current token value:', token.value ? `${token.value.substring(0, 20)}...` : 'null')
      console.log('[Auth Store] isAuthenticated:', isAuthenticated.value)
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '로그인에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchProfile() {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get('/auth/me')
      
      user.value = response.data
      localStorage.setItem('auth_user', JSON.stringify(response.data))
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '프로필 조회에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteAccount() {
    loading.value = true
    error.value = null
    
    try {
      await apiClient.delete('/auth/me')
      logout()
    } catch (err) {
      error.value = err.response?.data?.detail || '계정 삭제에 실패했습니다.'
      throw err
    } finally {
      loading.value = false
    }
  }

  function logout() {
    // Clear state
    token.value = null
    user.value = null
    error.value = null
    
    // Clear localStorage
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    token,
    user,
    loading,
    error,
    
    // Getters
    isAuthenticated,
    userName,
    userEmail,
    
    // Actions
    initializeAuth,
    register,
    login,
    fetchProfile,
    deleteAccount,
    logout,
    clearError
  }
})
