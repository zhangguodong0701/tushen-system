<template>
  <div class="notifications-page">
    <div class="page-header">
      <h2>消息通知</h2>
      <button v-if="notifications.some(n => !n.is_read)" class="btn btn-outline" @click="markAllRead">
        <i class="fas fa-check-double"></i> 全部已读
      </button>
    </div>

    <div class="card">
      <div class="card-body">
        <!-- 骨架屏 -->
        <div v-if="loading" class="skeleton-list">
          <div v-for="i in 5" :key="i" class="skeleton-item">
            <div class="skeleton-icon"></div>
            <div class="skeleton-content">
              <div class="skeleton-line" style="width: 70%; height: 16px; margin-bottom: 8px;"></div>
              <div class="skeleton-line" style="width: 90%; height: 14px; margin-bottom: 6px;"></div>
              <div class="skeleton-line" style="width: 40%; height: 12px;"></div>
            </div>
          </div>
        </div>
        <div v-else-if="notifications.length === 0" class="empty-state">
          <i class="fas fa-bell-slash"></i>
          <p>暂无通知</p>
        </div>
        <div v-else class="notification-list">
          <div
            v-for="n in notifications"
            :key="n.id"
            class="notification-item"
            :class="{ unread: !n.is_read }"
            @click="handleNotification(n)"
          >
            <div class="notification-icon" :class="n.type">
              <i :class="getIcon(n.type)"></i>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ n.title }}</div>
              <div class="notification-message">{{ n.message }}</div>
              <div class="notification-time">{{ formatTime(n.created_at) }}</div>
            </div>
            <div v-if="!n.is_read" class="unread-dot"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="page <= 1" @click="changePage(page - 1)">
        <i class="fas fa-chevron-left"></i> 上一页
      </button>
      <span class="page-info">第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 条</span>
      <button :disabled="page >= totalPages" @click="changePage(page + 1)">
        下一页 <i class="fas fa-chevron-right"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const notifications = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)

function changePage(p) {
  page.value = p
  loadNotifications()
}

async function loadNotifications() {
  loading.value = true
  try {
    const data = await api.get(`/api/notifications?page=${page.value}&page_size=${pageSize}`)
    notifications.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    authStore.toast('加载通知失败', 'error')
  } finally {
    loading.value = false
  }
}

async function handleNotification(n) {
  if (!n.is_read) {
    try {
      await api.post(`/api/notifications/${n.id}/read`)
      n.is_read = true
      window.dispatchEvent(new CustomEvent('notifications-updated'))
    } catch (e) {
      console.error('标记已读失败', e)
    }
  }

  // 根据通知类型跳转
  if (n.order_id) {
    router.push('/orders')
  } else if (n.demand_id) {
    router.push(`/demands/${n.demand_id}`)
  }
}

async function markAllRead() {
  try {
    await api.post('/api/notifications/mark-all-read')
    notifications.value.forEach(n => n.is_read = true)
    window.dispatchEvent(new CustomEvent('notifications-updated'))
    authStore.toast('已全部标记为已读', 'success')
  } catch (e) {
    authStore.toast('操作失败', 'error')
  }
}

function getIcon(type) {
  const icons = {
    订单状态变更: 'fas fa-shopping-cart',
    报价通知: 'fas fa-file-invoice-dollar',
    系统通知: 'fas fa-bell',
    资金变动: 'fas fa-coins',
    纠纷通知: 'fas fa-gavel'
  }
  return icons[type] || 'fas fa-info-circle'
}

function formatTime(time) {
  if (!time) return '-'
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.notifications-page {
  /* 移除 max-width 限制，让内容铺满 */
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px;
  color: #999;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
}

.notification-list {
  display: flex;
  flex-direction: column;
}

.notification-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background 0.3s;
  position: relative;
}

.notification-item:hover {
  background: #f8f9fa;
}

.notification-item.unread {
  background: rgba(102, 126, 234, 0.03);
}

.notification-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 18px;
}

.notification-icon.订单状态变更 {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.notification-icon.报价通知 {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.notification-icon.系统通知 {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.notification-icon.资金变动 {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.notification-icon.纠纷通知 {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 14px;
  color: #666;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.unread-dot {
  position: absolute;
  top: 50%;
  right: 16px;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
}

/* 骨架屏 */
.skeleton-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  flex-shrink: 0;
}

.skeleton-content {
  flex: 1;
}

.skeleton-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.skeleton-line {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.page-info {
  color: #666;
  font-size: 14px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination button:hover:not(:disabled) {
  background: #f5f7fa;
}
</style>
