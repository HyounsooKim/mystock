<template>
  <div class="page page-center">
    <div class="container-tight py-4">
      <div class="empty">
        <div class="empty-header">404</div>
        <p class="empty-title">페이지를 찾을 수 없습니다</p>
        <p class="empty-subtitle text-muted">
          요청하신 페이지가 존재하지 않거나 삭제되었습니다. 
        </p>
        <div class="empty-action">
          <router-link to="/" class="btn btn-primary">
            <i class="ti ti-arrow-left"></i>
            메인으로 돌아가기
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.page-center {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-header {
  font-size: 6rem;
  font-weight: 300;
  line-height: 1;
  color: var(--tblr-muted);
}
</style>
