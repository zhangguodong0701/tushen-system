// API 配置
// 外网访问时直接用 IP，内网/本地用 localhost
const env = import.meta.env
const hostname = window.location.hostname
const isLocalAccess = hostname === 'localhost' || hostname === '127.0.0.1'
export const API_BASE = isLocalAccess
  ? 'http://localhost:8000'
  : `http://${hostname}:8000`

// 封装的 API 模块
export const api = {
  baseURL: API_BASE,

  // ---- 统一响应规范化（Phase3 U2）----
  // 后端列表接口返回两种格式：
  //   1. 分页：{ items: [...], total: N }
  //   2. 数组：[ {...}, {...} ]
  // _normalize() 统一返回数组，同时保留原始 data（含 total/page 等元数据）
  _normalize(data) {
    return {
      items: Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : []),
      _raw: data  // 保留原始响应（含 total/page 等元数据）
    }
  },

  // 获取请求头
  getHeaders() {
    const token = localStorage.getItem('tushen_token')
    const headers = { 'Content-Type': 'application/json' }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  },

  // GET 请求（标准版，原样返回原始 JSON）
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

  // GET 请求（列表专用，自动规范化格式）
  // 用法：const { items, _raw } = await api.safeGet('/api/feedback')
  //   items = 数组（自动处理 data.items 和 data=[] 两种情况）
  //   _raw = 原始响应（含 total/page 等元数据）
  async safeGet(path) {
    const raw = await this.get(path)
    return this._normalize(raw)
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
