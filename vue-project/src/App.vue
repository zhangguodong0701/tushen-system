<template>
  <div id="app">
    <!-- Toast 容器 -->
    <div class="toast-container">
      <div
        v-for="toast in authStore.toasts"
        :key="toast.id"
        :class="['toast', toast.type]"
      >
        <i :class="toastIcon(toast.type)"></i>
        {{ toast.msg }}
      </div>
    </div>

    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 初始化时验证用户状态
onMounted(() => {
  authStore.fetchCurrentUser()
})

function toastIcon(type) {
  if (type === 'success') return 'fas fa-check-circle'
  if (type === 'error') return 'fas fa-exclamation-circle'
  return 'fas fa-info-circle'
}
</script>

<style>
/* 全局重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  background: transparent;
}

/* Toast 样式 */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  padding: 14px 20px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  animation: slideIn 0.3s ease;
}

.toast.success {
  background: #10b981;
  color: white;
}

.toast.error {
  background: #ef4444;
  color: white;
}

.toast.info {
  border-left: 4px solid #3b82f6;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
