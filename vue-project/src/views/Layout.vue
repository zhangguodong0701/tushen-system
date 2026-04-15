<template>
  <div class="layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo" @click="router.push('/')">
          <i class="fas fa-drafting-compass"></i>
          <span v-if="!sidebarCollapsed">图审云</span>
        </div>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <i :class="sidebarCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left'"></i>
        </button>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :class="{ active: route.path === '/' }">
          <i class="fas fa-home"></i>
          <span v-if="!sidebarCollapsed">工作台</span>
        </router-link>

        <template v-if="authStore.isBuyer || authStore.isAdmin">
          <router-link to="/demands/create" class="nav-item" :class="{ active: route.path === '/demands/create' }">
            <i class="fas fa-plus-circle"></i>
            <span v-if="!sidebarCollapsed">发布需求</span>
          </router-link>
        </template>

        <router-link to="/demands" class="nav-item" :class="{ active: route.path === '/demands' }">
          <i class="fas fa-list"></i>
          <span v-if="!sidebarCollapsed">需求大厅</span>
        </router-link>

        <router-link to="/my-demands" class="nav-item" :class="{ active: route.path === '/my-demands' }">
          <i class="fas fa-tasks"></i>
          <span v-if="!sidebarCollapsed">我的需求</span>
        </router-link>

        <router-link to="/my-quotes" class="nav-item" :class="{ active: route.path === '/my-quotes' }">
          <i class="fas fa-file-invoice-dollar"></i>
          <span v-if="!sidebarCollapsed">我的报价</span>
        </router-link>

        <router-link to="/orders" class="nav-item" :class="{ active: route.path === '/orders' }">
          <i class="fas fa-shopping-cart"></i>
          <span v-if="!sidebarCollapsed">订单管理</span>
        </router-link>

        <router-link to="/drawings" class="nav-item" :class="{ active: route.path === '/drawings' }">
          <i class="fas fa-drafting-compass"></i>
          <span v-if="!sidebarCollapsed">图纸管理</span>
        </router-link>

        <router-link to="/disputes" class="nav-item" :class="{ active: route.path === '/disputes' }">
          <i class="fas fa-gavel"></i>
          <span v-if="!sidebarCollapsed">纠纷处理</span>
        </router-link>

        <router-link to="/notifications" class="nav-item" :class="{ active: route.path === '/notifications' }">
          <i class="fas fa-bell"></i>
          <span v-if="!sidebarCollapsed">
            消息通知
            <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
          </span>
        </router-link>

        <!-- 审核员菜单 -->
        <template v-if="authStore.isReviewer">
          <div class="nav-divider"></div>
          <div class="nav-label" v-if="!sidebarCollapsed">审核中心</div>
          <router-link to="/reviewer" class="nav-item" :class="{ active: route.path === '/reviewer' }">
            <i class="fas fa-user-check"></i>
            <span v-if="!sidebarCollapsed">用户审核</span>
          </router-link>
        </template>

        <!-- 管理员菜单 -->
        <template v-if="authStore.isAdmin">
          <div class="nav-divider"></div>
          <div class="nav-label" v-if="!sidebarCollapsed">后台管理</div>
          <router-link to="/admin" class="nav-item" :class="{ active: route.path === '/admin' }">
            <i class="fas fa-cog"></i>
            <span v-if="!sidebarCollapsed">后台管理</span>
          </router-link>
        </template>

        <div class="nav-divider"></div>

        <router-link to="/profile" class="nav-item" :class="{ active: route.path === '/profile' }">
          <i class="fas fa-user"></i>
          <span v-if="!sidebarCollapsed">个人中心</span>
        </router-link>

        <router-link to="/feedback" class="nav-item" :class="{ active: route.path === '/feedback' }">
          <i class="fas fa-comment-dots"></i>
          <span v-if="!sidebarCollapsed">投诉反馈</span>
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <div class="main-wrapper">
      <!-- 顶部栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <h2 class="page-title">{{ pageTitle }}</h2>
        </div>
        <div class="topbar-right">
          <div class="user-info" @click="router.push('/notifications')">
            <i class="fas fa-bell"></i>
            <span v-if="unreadCount > 0" class="badge badge-red">{{ unreadCount }}</span>
          </div>
          <div class="user-dropdown" @click="showUserMenu = !showUserMenu">
            <div class="avatar">
              <i class="fas fa-user"></i>
            </div>
            <span>{{ authStore.user?.real_name || '用户' }}</span>
            <i class="fas fa-chevron-down"></i>
          </div>
          <div v-if="showUserMenu" class="dropdown-menu">
            <div class="dropdown-item" @click="router.push('/profile')">
              <i class="fas fa-user"></i> 个人中心
            </div>
            <div class="dropdown-item" @click="handleLogout">
              <i class="fas fa-sign-out-alt"></i> 退出登录
            </div>
          </div>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const sidebarCollapsed = ref(false)
const showUserMenu = ref(false)
const unreadCount = ref(0)

const pageTitles = {
  '/': '工作台',
  '/demands': '需求大厅',
  '/demands/create': '发布需求',
  '/my-demands': '我的需求',
  '/my-quotes': '我的报价',
  '/orders': '订单管理',
  '/drawings': '图纸管理',
  '/disputes': '纠纷处理',
  '/notifications': '消息通知',
  '/profile': '个人中心',
  '/feedback': '投诉反馈',
  '/reviewer': '审核中心',
  '/admin': '后台管理'
}

const pageTitle = computed(() => pageTitles[route.path] || '图审云平台')

async function loadNotifications() {
  if (!authStore.token) return
  try {
    const res = await fetch(`${api.baseURL}/api/notifications`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      unreadCount.value = (data.items || []).filter(n => !n.is_read).length
    }
  } catch (e) {
    authStore.toast('加载通知失败', 'error')
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function handleClickOutside(e) {
  if (showUserMenu.value && !e.target.closest('.user-dropdown')) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  authStore.fetchCurrentUser()
  loadNotifications()
  document.addEventListener('click', handleClickOutside)
  
  // 监听通知更新事件
  document.addEventListener('notifications-updated', loadNotifications)
  
  // 定时刷新通知
  const interval = setInterval(loadNotifications, 30000)
  onUnmounted(() => {
    clearInterval(interval)
    document.removeEventListener('notifications-updated', loadNotifications)
  })
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.layout {
  position: relative;
  min-height: 100vh;
  background: #f5f7fa;
}

/* 侧边栏 */
.sidebar {
  width: 220px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 100;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
  cursor: pointer;
}

.logo i {
  font-size: 28px;
  color: #667eea;
}

.collapse-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 4px;
}

.collapse-btn:hover {
  color: white;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: #aaa;
  text-decoration: none;
  transition: all 0.3s;
  position: relative;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.nav-item.active {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.nav-item i {
  width: 20px;
  text-align: center;
}

.nav-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 12px 20px;
}

.nav-label {
  padding: 8px 20px;
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
}

.badge {
  background: #ef4444;
  color: white;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  margin-left: 8px;
}

/* 主内容区 */
.main-wrapper {
  position: absolute;
  left: 220px;
  right: 0;
  top: 0;
  bottom: 0;
  transition: left 0.3s;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 侧边栏折叠时，内容区跟随移动 */
.layout.sidebar-collapsed .main-wrapper {
  left: 64px;
}

.topbar {
  height: 64px;
  background: white;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.topbar-left {
  display: flex;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
}

.user-info {
  position: relative;
  cursor: pointer;
  padding: 8px;
}

.user-info i {
  font-size: 20px;
  color: #666;
}

.badge-red {
  position: absolute;
  top: 0;
  right: 0;
  background: #ef4444;
  color: white;
  font-size: 10px;
  padding: 2px 5px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 8px;
}

.user-dropdown:hover {
  background: #f5f7fa;
}

.avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  min-width: 160px;
  margin-top: 8px;
  z-index: 100;
}

.dropdown-item {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background 0.3s;
}

.dropdown-item:hover {
  background: #f5f7fa;
}

.dropdown-item:first-child {
  border-radius: 8px 8px 0 0;
}

.dropdown-item:last-child {
  border-radius: 0 0 8px 8px;
}

.main-content {
  padding: 24px;
}
</style>
