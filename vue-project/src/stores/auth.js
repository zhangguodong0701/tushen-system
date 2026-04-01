import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('tushen_token') || '')
  const user = ref(null)
  const toasts = ref([])

  const isLoggedIn = computed(() => !!token.value)
  // 乙方类型
  const YI_FANG_TYPES = ['设计院', '设计师', '材料商', '设备商']
  const isSeller = computed(() => {
    const ut = user.value?.user_type
    return ut && YI_FANG_TYPES.includes(ut) && user.value?.is_admin !== 1
  })
  // 甲方类型
  const JIA_FANG_TYPES = ['业主', '建设单位', '项目方']
  const isBuyer = computed(() => {
    const ut = user.value?.user_type
    return ut && JIA_FANG_TYPES.includes(ut) && user.value?.is_admin !== 1
  })
  const isAdmin = computed(() => user.value?.is_admin === 1)
  const isReviewer = computed(() => user.value?.is_reviewer === 1)

  function setUser(userData) {
    user.value = userData
  }

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('tushen_token', newToken)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('tushen_token')
  }

  function toast(msg, type = 'info') {
    const id = Date.now()
    toasts.value.push({ id, msg, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, 3500)
  }

  async function fetchCurrentUser() {
    if (!token.value) return null
    try {
      const response = await fetch(`${api.baseURL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      if (response.ok) {
        const data = await response.json()
        user.value = data
        return data
      } else if (response.status === 401) {
        // Token 过期，清除并重定向到登录
        logout()
        return null
      }
      // 其他错误不清除用户状态，保持登录状态
      return null
    } catch (e) {
      console.error('获取用户信息失败', e)
      // 网络错误时保持登录状态，不清除用户
      return null
    }
  }

  return {
    token,
    user,
    toasts,
    isLoggedIn,
    isBuyer,
    isSeller,
    isAdmin,
    isReviewer,
    setUser,
    setToken,
    logout,
    toast,
    fetchCurrentUser
  }
})
