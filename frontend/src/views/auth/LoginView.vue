<template>
  <div class="page page-center">
    <div class="container container-tight py-4">
      <div class="text-center mb-4">
        <h1 class="text-primary">MyStock</h1>
        <p class="text-muted">나의 관심 주식</p>
      </div>
      
      <form class="card card-md" @submit.prevent="handleLogin">
        <div class="card-body">
          <h2 class="card-title text-center mb-4">로그인</h2>
          
          <!-- Error message -->
          <div v-if="authStore.error" class="alert alert-danger" role="alert">
            {{ authStore.error }}
          </div>
          
          <!-- Email -->
          <div class="mb-3">
            <label class="form-label">이메일</label>
            <input
              v-model="email"
              type="email"
              class="form-control"
              placeholder="이메일 주소"
              required
              autocomplete="email"
            />
          </div>
          
          <!-- Password -->
          <div class="mb-2">
            <label class="form-label">비밀번호</label>
            <input
              v-model="password"
              type="password"
              class="form-control"
              placeholder="비밀번호"
              required
              autocomplete="current-password"
            />
          </div>
          
          <!-- Submit button -->
          <div class="form-footer">
            <button
              type="submit"
              class="btn btn-primary w-100"
              :disabled="authStore.loading"
            >
              <span v-if="authStore.loading" class="spinner-border spinner-border-sm me-2"></span>
              로그인
            </button>
          </div>
        </div>
      </form>
      
      <!-- Register link -->
      <div class="text-center text-muted mt-3">
        계정이 없으신가요?
        <router-link to="/register">회원가입</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form data
const email = ref('')
const password = ref('')

// Methods
async function handleLogin() {
  authStore.clearError()
  
  try {
    await authStore.login(email.value, password.value)
    
    console.log('[LoginView] Login successful, token:', authStore.token ? `${authStore.token.substring(0, 20)}...` : 'null')
    console.log('[LoginView] isAuthenticated:', authStore.isAuthenticated)
    
    // Wait for next tick to ensure store is updated
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // Redirect to original page or watchlist
    const redirect = route.query.redirect || '/watchlist'
    router.push(redirect)
  } catch (error) {
    // Error already set in store
    console.error('Login failed:', error)
  }
}
</script>

<style scoped>
.page-center {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
}

.text-primary {
  color: var(--tblr-primary) !important;
}
</style>
