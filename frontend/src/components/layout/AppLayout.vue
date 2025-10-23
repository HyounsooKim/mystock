<template>
  <div class="page">
    <!-- Navbar -->
    <header class="navbar navbar-expand-md navbar-light d-print-none">
      <div class="container-xl">
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbar-menu">
          <span class="navbar-toggler-icon"></span>
        </button>
        
        <h1 class="navbar-brand navbar-brand-autodark d-none-navbar-horizontal pe-0 pe-md-3">
          <a href="/">
            <span class="navbar-brand-text">MyStock</span>
          </a>
        </h1>
        
        <div class="navbar-nav flex-row order-md-last">
          <!-- Theme toggle -->
          <div class="nav-item">
            <div class="theme-toggle-switch" @click="toggleTheme">
              <div class="theme-toggle-track" :class="{ dark: isDark }">
                <div class="theme-toggle-thumb" :class="{ dark: isDark }">
                  <i v-if="isDark" class="ti ti-moon"></i>
                  <i v-else class="ti ti-sun"></i>
                </div>
                <div class="theme-toggle-icons">
                  <i class="ti ti-sun light-icon"></i>
                  <i class="ti ti-moon dark-icon"></i>
                </div>
              </div>
            </div>
          </div>
          
          <!-- User dropdown -->
          <div class="nav-item dropdown ms-3">
            <a href="#" class="nav-link p-0" data-bs-toggle="dropdown" aria-expanded="false">
              <div class="user-badge">
                <i class="ti ti-user"></i>
                <span class="user-id">{{ userId }}</span>
                <i class="ti ti-chevron-down ms-1" style="font-size: 0.75rem;"></i>
              </div>
            </a>
            <div class="dropdown-menu dropdown-menu-end dropdown-menu-arrow">
              <div class="dropdown-item-text">
                <div class="text-muted small">로그인 정보</div>
                <div class="fw-bold">{{ userId }}</div>
              </div>
              <div class="dropdown-divider"></div>
              <a href="#" class="dropdown-item text-danger" @click.prevent="handleLogout">
                <i class="ti ti-logout me-2"></i>
                로그아웃
              </a>
            </div>
          </div>
        </div>
      </div>
    </header>
    
    <!-- Navigation tabs -->
    <div class="navbar-expand-md">
      <div class="collapse navbar-collapse" id="navbar-menu">
        <div class="navbar navbar-light">
          <div class="container-xl">
            <ul class="navbar-nav">
              <li class="nav-item">
                <router-link to="/watchlist" class="nav-link" active-class="active">
                  <span class="nav-link-icon d-md-none d-lg-inline-block">
                    <i class="ti ti-star"></i>
                  </span>
                  <span class="nav-link-title">
                    관심종목
                  </span>
                </router-link>
              </li>
              <li class="nav-item">
                <router-link to="/portfolio" class="nav-link" active-class="active">
                  <span class="nav-link-icon d-md-none d-lg-inline-block">
                    <i class="ti ti-briefcase"></i>
                  </span>
                  <span class="nav-link-title">
                    포트폴리오
                  </span>
                </router-link>
              </li>
              <li class="nav-item">
                <router-link to="/top-movers" class="nav-link" active-class="active">
                  <span class="nav-link-icon d-md-none d-lg-inline-block">
                    <i class="ti ti-trending-up"></i>
                  </span>
                  <span class="nav-link-title">
                    급등락 종목
                  </span>
                </router-link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Page wrapper -->
    <div class="page-wrapper">
      <!-- Page header -->
      <div class="page-header d-print-none">
        <div class="container-xl">
          <div class="row g-2 align-items-center">
            <div class="col">
              <div class="page-pretitle">
                {{ pageSubtitle }}
              </div>
              <h2 class="page-title">
                {{ pageTitle }}
              </h2>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Page body -->
      <div class="page-body">
        <div :class="fullWidth ? 'container-fluid' : 'container-xl'">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// State
const isDark = ref(false)

// Props
const props = defineProps({
  pageTitle: {
    type: String,
    default: ''
  },
  pageSubtitle: {
    type: String,
    default: ''
  }
})

// Computed
const userName = computed(() => authStore.userName)
const userEmail = computed(() => authStore.userEmail)
const userId = computed(() => {
  const email = authStore.userEmail || ''
  if (email) {
    // Extract ID from email (part before @) - keep original case
    const id = email.split('@')[0]
    return id
  }
  return '?'
})
const userInitial = computed(() => {
  const email = authStore.userEmail || ''
  return email ? email.charAt(0).toUpperCase() : '?'
})

// Lifecycle
onMounted(() => {
  // Check saved theme preference
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.body.setAttribute('data-bs-theme', 'dark')
  } else {
    isDark.value = false
    document.body.setAttribute('data-bs-theme', 'light')
  }
})

// Methods
function toggleTheme() {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  document.body.setAttribute('data-bs-theme', theme)
  localStorage.setItem('theme', theme)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar-brand-text {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--tblr-primary);
}

/* Dark mode support for MyStock logo */
[data-bs-theme="dark"] .navbar-brand-text {
  color: #fff;
}

/* User badge with icon and ID */
.user-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background-color: var(--tblr-primary);
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: var(--tblr-border-radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.user-badge:hover {
  background-color: var(--tblr-primary-darken);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.user-badge i {
  font-size: 1rem;
}

.user-id {
  line-height: 1;
}

/* Dropdown menu styling */
.dropdown-menu {
  min-width: 200px;
  padding: 0.5rem;
  border-radius: var(--tblr-border-radius);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.dropdown-item-text {
  padding: 0.5rem 0.75rem;
}

.dropdown-item.text-danger:hover {
  background-color: rgba(214, 57, 57, 0.1);
  color: var(--tblr-danger) !important;
}

.avatar {
  background-color: var(--tblr-primary);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  min-width: 2.5rem;
  height: 2.5rem;
  padding: 0 0.75rem;
  font-size: 0.875rem;
  border-radius: var(--tblr-border-radius);
  white-space: nowrap;
}

/* Theme toggle switch */
.theme-toggle-switch {
  cursor: pointer;
  padding: 0.25rem;
  user-select: none;
}

.theme-toggle-track {
  position: relative;
  width: 60px;
  height: 30px;
  background: #74c0fc;
  border-radius: 15px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.theme-toggle-track.dark {
  background: #4c6ef5;
}

.theme-toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 26px;
  height: 26px;
  background: white;
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fd7e14;
  font-size: 16px;
}

.theme-toggle-thumb.dark {
  left: 32px;
  color: #4c6ef5;
}

.theme-toggle-thumb i {
  transition: transform 0.3s ease;
}

.theme-toggle-switch:hover .theme-toggle-thumb {
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
  transform: scale(1.05);
}

.theme-toggle-switch:active .theme-toggle-thumb {
  transform: scale(0.95);
}

.theme-toggle-icons {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px;
  pointer-events: none;
  font-size: 14px;
}

.light-icon {
  color: rgba(255, 255, 255, 0.9);
}

.dark-icon {
  color: rgba(255, 255, 255, 0.9);
}
</style>
