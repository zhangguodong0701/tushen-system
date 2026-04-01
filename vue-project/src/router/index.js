import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'demands',
        name: 'Demands',
        component: () => import('@/views/Demands.vue')
      },
      {
        path: 'demands/create',
        name: 'CreateDemand',
        component: () => import('@/views/DemandDetail.vue')
      },
      {
        path: 'demands/:id',
        name: 'DemandDetail',
        component: () => import('@/views/DemandDetail.vue')
      },
      {
        path: 'demands/:id/edit',
        name: 'DemandEdit',
        component: () => import('@/views/DemandEdit.vue')
      },
      {
        path: 'my-demands',
        name: 'MyDemands',
        component: () => import('@/views/MyDemands.vue')
      },
      {
        path: 'my-quotes',
        name: 'MyQuotes',
        component: () => import('@/views/MyQuotes.vue')
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/views/Orders.vue')
      },
      {
        path: 'drawings',
        name: 'Drawings',
        component: () => import('@/views/Drawings.vue')
      },
      {
        path: 'disputes',
        name: 'Disputes',
        component: () => import('@/views/Disputes.vue')
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/Notifications.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue')
      },
      {
        path: 'feedback',
        name: 'Feedback',
        component: () => import('@/views/Feedback.vue')
      },
      {
        path: 'reviewer',
        name: 'Reviewer',
        component: () => import('@/views/Reviewer.vue')
      },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('@/views/Admin.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(r => r.meta.requiresAuth !== false)
  
  // 如果有 token 但没有 user 信息，先获取用户信息
  const storedToken = localStorage.getItem('tushen_token')
  if (storedToken && !authStore.token) {
    authStore.setToken(storedToken)
  }
  
  // 如果有 token 但没有 user，异步获取
  if (authStore.token && !authStore.user) {
    await authStore.fetchCurrentUser()
  }

  // 如果需要认证但未登录（无 token 或获取用户失败）
  if (requiresAuth && !authStore.token) {
    next('/login')
  } else if (to.path === '/login' && authStore.token) {
    // 有 token 则跳转到首页（不需要检查 user，因为已经在获取）
    next('/')
  } else {
    next()
  }
})

export default router
