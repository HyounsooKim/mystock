<template>
  <div class="page page-center">
    <div class="container container-tight py-4">
      <div class="text-center mb-4">
        <h1 class="text-primary">
          <i class="ti ti-chart-candlestick me-2"></i>나의주식
        </h1>
        <p class="text-muted">개인 주식 포트폴리오 관리</p>
      </div>
      
      <form class="card card-md" @submit.prevent="handleRegister">
        <div class="card-body">
          <h2 class="card-title text-center mb-4">회원가입</h2>
          
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
          <div class="mb-3">
            <label class="form-label">비밀번호</label>
            <input
              v-model="password"
              type="password"
              class="form-control"
              placeholder="비밀번호 (8자 이상)"
              required
              minlength="8"
              autocomplete="new-password"
            />
            <small class="form-hint">
              비밀번호는 최소 8자 이상이어야 합니다.
            </small>
          </div>
          
          <!-- Password confirmation -->
          <div class="mb-3">
            <label class="form-label">비밀번호 확인</label>
            <input
              v-model="passwordConfirm"
              type="password"
              class="form-control"
              placeholder="비밀번호 확인"
              required
              minlength="8"
              autocomplete="new-password"
            />
          </div>
          
          <!-- Validation error -->
          <div v-if="validationError" class="alert alert-warning" role="alert">
            {{ validationError }}
          </div>
          
          <!-- Submit button -->
          <div class="form-footer">
            <button
              type="submit"
              class="btn btn-primary w-100"
              :disabled="authStore.loading"
            >
              <span v-if="authStore.loading" class="spinner-border spinner-border-sm me-2"></span>
              회원가입
            </button>
          </div>
        </div>
      </form>
      
      <!-- Login link -->
      <div class="text-center text-muted mt-3">
        이미 계정이 있으신가요?
        <router-link to="/login">로그인</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Form data
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const validationError = ref('')

// Methods
async function handleRegister() {
  authStore.clearError()
  validationError.value = ''
  
  // Validate password match
  if (password.value !== passwordConfirm.value) {
    validationError.value = '비밀번호가 일치하지 않습니다.'
    return
  }
  
  // Validate password length
  if (password.value.length < 8) {
    validationError.value = '비밀번호는 최소 8자 이상이어야 합니다.'
    return
  }
  
  try {
    await authStore.register(email.value, password.value)
    
    // Redirect to watchlist after successful registration
    router.push('/watchlist')
  } catch (error) {
    // Error already set in store
    console.error('Registration failed:', error)
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
