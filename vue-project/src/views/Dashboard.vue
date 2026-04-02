<template>
  <div class="dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-text">
        <h1>你好，{{ authStore.user?.real_name || '用户' }}！</h1>
        <p>
          <span class="role-tag" :class="getRoleClass()">
            {{ getRoleText() }}
          </span>
          {{ welcomeMessage }}
        </p>
      </div>
      <div class="quick-actions">
        <button v-if="authStore.isBuyer" class="btn btn-gradient" @click="router.push('/demands/create')">
          <i class="fas fa-plus"></i> 发布需求
        </button>
        <button v-if="authStore.isReviewer" class="btn btn-gradient" @click="router.push('/reviewer')">
          <i class="fas fa-clipboard-check"></i> 审核中心
        </button>
        <button v-if="authStore.isAdmin" class="btn btn-gradient" @click="router.push('/admin')">
          <i class="fas fa-cog"></i> 后台管理
        </button>
        <button class="btn btn-secondary" @click="router.push('/demands')">
          <i class="fas fa-search"></i> 浏览需求
        </button>
      </div>
    </div>

    <!-- 普通用户统计卡片 -->
    <div v-if="authStore.isBuyer || authStore.isSeller" class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(102, 126, 234, 0.1); color: #667eea;">
          <i class="fas fa-list"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.demands }}</div>
          <div class="stat-label">发布的需求</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(16, 185, 129, 0.1); color: #10b981;">
          <i class="fas fa-file-invoice-dollar"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.quotes }}</div>
          <div class="stat-label">我的报价</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(245, 158, 11, 0.1); color: #f59e0b;">
          <i class="fas fa-shopping-cart"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.orders }}</div>
          <div class="stat-label">进行中的订单</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(239, 68, 68, 0.1); color: #ef4444;">
          <i class="fas fa-bell"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ unreadCount }}</div>
          <div class="stat-label">未读消息</div>
        </div>
      </div>
    </div>

    <!-- 审核员/管理员统计卡片 -->
    <div v-else-if="authStore.isReviewer || authStore.isAdmin" class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(102, 126, 234, 0.1); color: #667eea;">
          <i class="fas fa-users"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ adminStats.pendingUsers }}</div>
          <div class="stat-label">待审核用户</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(16, 185, 129, 0.1); color: #10b981;">
          <i class="fas fa-file-alt"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ adminStats.pendingDemands }}</div>
          <div class="stat-label">待审核需求</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(239, 68, 68, 0.1); color: #ef4444;">
          <i class="fas fa-gavel"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ adminStats.pendingDisputes }}</div>
          <div class="stat-label">待处理纠纷</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(245, 158, 11, 0.1); color: #f59e0b;">
          <i class="fas fa-chart-line"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ adminStats.totalUsers }}</div>
          <div class="stat-label">总用户数</div>
        </div>
      </div>
    </div>

    <!-- 最近活动 - 普通用户 -->
    <div v-if="authStore.isBuyer || authStore.isSeller" class="content-grid">
      <div class="card">
        <div class="card-header">
          <h3><i class="fas fa-clock"></i> 最近通知</h3>
          <router-link to="/notifications" class="link">查看全部</router-link>
        </div>
        <div class="card-body">
          <div v-if="notifications.length === 0" class="empty-state">
            <i class="fas fa-bell-slash"></i>
            <p>暂无通知</p>
          </div>
          <div v-else class="notification-list">
            <div
              v-for="n in notifications.slice(0, 5)"
              :key="n.id"
              class="notification-item"
              :class="{ unread: !n.is_read }"
              @click="handleNotificationClick(n)"
            >
              <div class="notification-icon">
                <i :class="getNotificationIcon(n.type)"></i>
              </div>
              <div class="notification-content">
                <div class="notification-title">{{ n.title }}</div>
                <div class="notification-time">{{ formatTime(n.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3><i class="fas fa-tasks"></i> 进行中的订单</h3>
          <router-link to="/orders" class="link">查看全部</router-link>
        </div>
        <div class="card-body">
          <div v-if="activeOrders.length === 0" class="empty-state">
            <i class="fas fa-inbox"></i>
            <p>暂无进行中的订单</p>
          </div>
          <div v-else class="order-list">
            <div
              v-for="order in activeOrders.slice(0, 5)"
              :key="order.id"
              class="order-item"
              @click="router.push('/orders')"
            >
              <div class="order-info">
                <div class="order-title">{{ order.title || `订单 #${order.id}` }}</div>
                <div class="order-meta">
                  <span class="status-badge" :class="order.status">{{ statusText(order.status) }}</span>
                  <span class="order-amount">¥{{ formatAmount(order.amount) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 待处理事项 - 审核员/管理员 -->
    <div v-else-if="authStore.isReviewer || authStore.isAdmin" class="content-grid">
      <div class="card">
        <div class="card-header">
          <h3><i class="fas fa-user-clock"></i> 待审核用户</h3>
          <router-link to="/reviewer" class="link">查看全部</router-link>
        </div>
        <div class="card-body">
          <div v-if="pendingUsers.length === 0" class="empty-state">
            <i class="fas fa-check-circle"></i>
            <p>暂无待审核用户</p>
          </div>
          <div v-else class="user-list">
            <div
              v-for="user in pendingUsers.slice(0, 5)"
              :key="user.id"
              class="user-item"
              @click="router.push('/reviewer')"
            >
              <div class="user-avatar">
                <i class="fas fa-user"></i>
              </div>
              <div class="user-info">
                <div class="user-name">{{ user.real_name || '未实名' }}</div>
                <div class="user-meta">{{ user.phone }} · {{ formatTime(user.created_at) }}</div>
              </div>
              <span class="badge badge-warning">待审核</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3><i class="fas fa-exclamation-circle"></i> 待处理纠纷</h3>
          <router-link to="/disputes" class="link">查看全部</router-link>
        </div>
        <div class="card-body">
          <div v-if="pendingDisputes.length === 0" class="empty-state">
            <i class="fas fa-check-circle"></i>
            <p>暂无待处理纠纷</p>
          </div>
          <div v-else class="dispute-list">
            <div
              v-for="d in pendingDisputes.slice(0, 5)"
              :key="d.id"
              class="dispute-item"
              @click="router.push('/disputes')"
            >
              <div class="dispute-info">
                <div class="dispute-title">{{ d.title || `纠纷 #${d.id}` }}</div>
                <div class="dispute-meta">
                  <span class="badge badge-danger">处理中</span>
                  <span class="dispute-amount">¥{{ formatAmount(d.amount) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
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
const activeOrders = ref([])
const stats = ref({ demands: 0, quotes: 0, orders: 0 })

// 管理员/审核员数据
const adminStats = ref({ pendingUsers: 0, pendingDemands: 0, pendingDisputes: 0, totalUsers: 0 })
const pendingUsers = ref([])
const pendingDisputes = ref([])

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

const welcomeMessage = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好，今天有什么计划？'
  if (hour < 18) return '下午好，继续加油！'
  return '晚上好，注意休息！'
})

function getRoleText() {
  if (authStore.isAdmin) return '管理员'
  if (authStore.isReviewer) return '审核员'
  if (authStore.user?.role === '甲方') return '甲方'
  if (authStore.user?.role === '乙方') return '乙方'
  return '用户'
}

function getRoleClass() {
  if (authStore.isAdmin) return 'admin'
  if (authStore.isReviewer) return 'reviewer'
  if (authStore.user?.role === '甲方') return 'buyer'
  return 'seller'
}

async function loadDashboard() {
  if (!authStore.token) return

  // 加载通知
  try {
    const res = await fetch(`${api.baseURL}/api/notifications`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      notifications.value = await res.json()
    }
  } catch (e) {
    console.error('加载通知失败', e)
  }

  // 加载订单
  try {
    const res = await fetch(`${api.baseURL}/api/orders`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      activeOrders.value = data.filter(o => !['已完成', '已取消', '已关闭'].includes(o.status))
      stats.value.orders = activeOrders.value.length
    }
  } catch (e) {
    console.error('加载订单失败', e)
  }

  // 加载需求
  try {
    const res = await fetch(`${api.baseURL}/api/demands/my`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      stats.value.demands = data.length
    }
  } catch (e) {
    console.error('加载需求失败', e)
  }

  // 加载报价
  try {
    const res = await fetch(`${api.baseURL}/api/quotes/my`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      stats.value.quotes = data.length
    }
  } catch (e) {
    console.error('加载报价失败', e)
  }
}

async function loadAdminDashboard() {
  if (!authStore.isReviewer && !authStore.isAdmin) return

  // 加载待审核用户
  try {
    const res = await fetch(`${api.baseURL}/api/admin/users?status=pending&page=1&page_size=5`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      pendingUsers.value = data.items || []
      adminStats.value.pendingUsers = data.total || pendingUsers.value.length
    }
  } catch (e) {
    console.error('加载待审核用户失败', e)
  }

  // 加载待审核需求
  try {
    const res = await fetch(`${api.baseURL}/api/admin/demands?status=pending&page=1&page_size=5`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      adminStats.value.pendingDemands = data.total || 0
    }
  } catch (e) {
    console.error('加载待审核需求失败', e)
  }

  // 加载待处理纠纷
  try {
    const res = await fetch(`${api.baseURL}/api/disputes?status=处理中`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      pendingDisputes.value = Array.isArray(data) ? data : (data.items || [])
      adminStats.value.pendingDisputes = pendingDisputes.value.length
    }
  } catch (e) {
    console.error('加载纠纷失败', e)
  }

  // 加载总用户数
  try {
    const res = await fetch(`${api.baseURL}/api/admin/users?page=1&page_size=1`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      adminStats.value.totalUsers = data.total || 0
    }
  } catch (e) {
    console.error('加载用户总数失败', e)
  }
}

function getNotificationIcon(type) {
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
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${Math.floor(diff / 86400000)}天前`
}

function statusText(status) {
  const map = {
    待支付: '待支付',
    进行中: '进行中',
    已完成: '已完成',
    已取消: '已取消',
    审核中: '审核中'
  }
  return map[status] || status
}

// 格式化金额显示
function formatAmount(amount) {
  if (!amount) return '0'
  amount = Number(amount)
  if (amount >= 100000000) {
    return (amount / 100000000).toFixed(1) + '亿'
  } else if (amount >= 10000) {
    return (amount / 10000).toFixed(1) + '万'
  } else if (amount >= 1000) {
    return amount.toLocaleString('zh-CN')
  }
  return amount.toString()
}

function handleNotificationClick(n) {
  // 标记已读
  if (!n.is_read) {
    fetch(`${api.baseURL}/api/notifications/${n.id}/read`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    n.is_read = true
  }
}

onMounted(() => {
  loadDashboard()
  loadAdminDashboard()
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
}

.welcome-text h1 {
  margin: 0 0 8px 0;
  font-size: 26px;
  color: white;
}

.welcome-text p {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
}

.role-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.role-tag.buyer,
.role-tag.seller {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.role-tag.admin,
.role-tag.reviewer {
  background: rgba(255, 255, 255, 0.3);
  color: white;
}

.quick-actions {
  display: flex;
  gap: 12px;
}

.btn-gradient {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  background: white;
  color: #667eea;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-gradient:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.btn-secondary {
  padding: 12px 24px;
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-radius: 10px;
  background: transparent;
  color: white;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: white;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 28px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
}

.stat-value {
  font-size: 30px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #888;
  margin-top: 4px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #333;
}

.card-header h3 i {
  color: #667eea;
  font-size: 18px;
}

.link {
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

.link:hover {
  text-decoration: underline;
}

.card-body {
  padding: 16px 24px 24px;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: #999;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 15px;
}

.notification-list,
.order-list,
.user-list,
.dispute-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notification-item {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.notification-item:hover {
  background: #f8f9fa;
}

.notification-item.unread {
  background: rgba(102, 126, 234, 0.06);
}

.notification-icon {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  flex-shrink: 0;
}

.notification-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.order-item {
  padding: 14px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #f0f0f0;
}

.order-item:hover {
  background: #f8f9fa;
  border-color: #e0e0e0;
}

.order-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 500;
}

.order-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.待支付 {
  background: #fef3cd;
  color: #856404;
}

.status-badge.进行中 {
  background: #d4edda;
  color: #155724;
}

.status-badge.已完成 {
  background: #cce5ff;
  color: #004085;
}

.order-amount {
  font-size: 15px;
  font-weight: 700;
  color: #ef4444;
}

/* 用户列表样式 */
.user-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #f0f0f0;
}

.user-item:hover {
  background: #f8f9fa;
  border-color: #e0e0e0;
}

.user-avatar {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  flex-shrink: 0;
}

.user-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.user-meta {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.badge-warning {
  background: #fff3cd;
  color: #856404;
}

.badge-danger {
  background: #f8d7da;
  color: #721c24;
}

/* 纠纷列表样式 */
.dispute-item {
  padding: 14px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #f0f0f0;
}

.dispute-item:hover {
  background: #f8f9fa;
  border-color: #e0e0e0;
}

.dispute-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 500;
}

.dispute-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dispute-amount {
  font-size: 15px;
  font-weight: 700;
  color: #ef4444;
}
</style>
