// API 配置
export const API_BASE = 'http://localhost:8000'

// 封装的 API 模块
export const api = {
  baseURL: API_BASE,

  // 获取请求头
  getHeaders() {
    const token = localStorage.getItem('tushen_token')
    const headers = { 'Content-Type': 'application/json' }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  },

  // GET 请求
  async get(path) {
    const res = await fetch(`${this.baseURL}${path}`, {
      headers: this.getHeaders()
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(error.detail || '请求失败')
    }
    return res.json()
  },

  // POST 请求
  async post(path, data) {
    const res = await fetch(`${this.baseURL}${path}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(error.detail || '请求失败')
    }
    return res.json()
  },

  // FormData POST 请求（用于文件上传）
  async postForm(path, formData) {
    const token = localStorage.getItem('tushen_token')
    const headers = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    const res = await fetch(`${this.baseURL}${path}`, {
      method: 'POST',
      headers,
      body: formData
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(error.detail || '请求失败')
    }
    return res.json()
  },

  // PUT 请求
  async put(path, data) {
    const res = await fetch(`${this.baseURL}${path}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(error.detail || '请求失败')
    }
    return res.json()
  },

  // DELETE 请求
  async delete(path) {
    const res = await fetch(`${this.baseURL}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders()
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(error.detail || '请求失败')
    }
    return res.json()
  },

  // 认证相关
  auth: {
    login(username, password) {
      const fd = new FormData()
      fd.append('username', username)
      fd.append('password', password)
      return fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        body: fd
      }).then(r => r.json())
    },
    register(data) {
      return fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).then(r => r.json())
    },
    me() {
      const token = localStorage.getItem('tushen_token')
      return fetch(`${API_BASE}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(r => r.json())
    }
  },

  // 需求相关
  demands: {
    list(params = {}) {
      const query = new URLSearchParams(params).toString()
      return api.get(`/api/demands${query ? '?' + query : ''}`)
    },
    mine() {
      return api.get('/api/demands/my')
    },
    get(id) {
      return api.get(`/api/demands/${id}`)
    },
    create(data) {
      return api.post('/api/demands', data)
    },
    update(id, data) {
      return api.put(`/api/demands/${id}`, data)
    },
    delete(id) {
      return api.delete(`/api/demands/${id}`)
    }
  },

  // 订单相关
  orders: {
    list() {
      return api.get('/api/orders')
    },
    get(id) {
      return api.get(`/api/orders/${id}`)
    },
    pay(id) {
      return api.post(`/api/orders/${id}/pay`, {})
    },
    complete(id) {
      return api.post(`/api/orders/${id}/accept`, {})
    }
  },

  // 通知相关
  notifications: {
    list() {
      return api.get('/api/notifications')
    },
    markRead(id) {
      return api.post(`/api/notifications/${id}/read`, {})
    }
  }
}

export default api
