<template>
  <div class="admin-page">
    <!-- Tab 切换 -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key; loadData()"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 用户管理 -->
    <div v-if="activeTab === 'users'" class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户</th>
              <th>角色</th>
              <th>认证状态</th>
              <th>黑名单</th>
              <th>注册时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td>
                <div>{{ u.real_name }}</div>
                <div class="text-muted">{{ u.phone }}</div>
              </td>
              <td>
                <span v-if="u.is_admin" class="role-badge admin">管理员</span>
                <span v-else-if="u.is_reviewer" class="role-badge reviewer">审核员</span>
                <span v-else>{{ u.role }} / {{ u.user_type }}</span>
              </td>
              <td>
                <span class="status-badge" :class="u.status">{{ u.status }}</span>
              </td>
              <td>
                <span :class="u.is_blacklisted ? 'text-danger' : 'text-success'">
                  {{ u.is_blacklisted ? '是' : '否' }}
                </span>
              </td>
              <td>{{ formatTime(u.created_at) }}</td>
              <td>
                <button
                  v-if="!u.is_admin && !u.is_reviewer && u.status === '通过' && !u.is_blacklisted"
                  class="btn btn-sm btn-outline"
                  @click="blacklistUser(u)"
                >
                  <i class="fas fa-ban"></i>
                </button>
                <button
                  v-if="u.is_blacklisted"
                  class="btn btn-sm btn-outline"
                  @click="unblacklistUser(u)"
                >
                  <i class="fas fa-check"></i> 解禁
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 需求管理 -->
    <div v-if="activeTab === 'demands'" class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>需求标题</th>
              <th>发布者</th>
              <th>状态</th>
              <th>发布时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in demands" :key="d.id">
              <td>{{ d.id }}</td>
              <td>{{ d.title }}</td>
              <td>{{ d.buyer_name }}</td>
              <td>
                <span class="status-badge" :class="d.status">{{ d.status }}</span>
              </td>
              <td>{{ formatTime(d.created_at) }}</td>
              <td>
                <button class="btn btn-sm btn-outline" @click="viewDemand(d)">
                  查看
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 订单管理 -->
    <div v-if="activeTab === 'orders'" class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>订单</th>
              <th>甲方</th>
              <th>乙方</th>
              <th>金额</th>
              <th>状态</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in orders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ o.title }}</td>
              <td>{{ o.buyer_name }}</td>
              <td>{{ o.seller_name }}</td>
              <td class="amount">¥{{ o.amount }}</td>
              <td>
                <span class="status-badge" :class="o.status">{{ o.status }}</span>
              </td>
              <td>{{ formatTime(o.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 资金记录 -->
    <div v-if="activeTab === 'funds'" class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户</th>
              <th>类型</th>
              <th>金额</th>
              <th>关联订单</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="f in funds" :key="f.id">
              <td>{{ f.id }}</td>
              <td>{{ f.user_name }}</td>
              <td>{{ f.type }}</td>
              <td :class="f.amount > 0 ? 'text-success' : 'text-danger'">
                {{ f.amount > 0 ? '+' : '' }}{{ f.amount }}
              </td>
              <td>{{ f.order_id ? `#${f.order_id}` : '-' }}</td>
              <td>{{ formatTime(f.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 黑名单 -->
    <div v-if="activeTab === 'blacklist'" class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <div v-else-if="blacklist.length === 0" class="empty-state">
          <i class="fas fa-users-slash"></i>
          <p>黑名单为空</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户</th>
              <th>手机号</th>
              <th>原因</th>
              <th>操作人</th>
              <th>加入时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in blacklist" :key="b.id">
              <td>{{ b.id }}</td>
              <td>{{ b.user_name }}</td>
              <td>{{ b.phone }}</td>
              <td>{{ b.reason || '-' }}</td>
              <td>{{ b.operator_name }}</td>
              <td>{{ formatTime(b.created_at) }}</td>
              <td>
                <button class="btn btn-sm btn-success" @click="unblacklistUser(b)">
                  解除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'

const authStore = useAuthStore()

const activeTab = ref('users')
const loading = ref(false)
const users = ref([])
const demands = ref([])
const orders = ref([])
const funds = ref([])
const blacklist = ref([])

const tabs = [
  { key: 'users', label: '用户管理' },
  { key: 'demands', label: '需求管理' },
  { key: 'orders', label: '订单管理' },
  { key: 'funds', label: '资金记录' },
  { key: 'blacklist', label: '黑名单' }
]

async function loadData() {
  loading.value = true
  try {
    if (activeTab.value === 'users') {
      const res = await api.get('/api/admin/users')
      users.value = res.items || res || []
    } else if (activeTab.value === 'demands') {
      const res = await api.get('/api/admin/demands')
      demands.value = res.items || res || []
    } else if (activeTab.value === 'orders') {
      const res = await api.get('/api/admin/orders')
      orders.value = res.items || res || []
    } else if (activeTab.value === 'funds') {
      const res = await api.get('/api/admin/fund-records')
      funds.value = res.items || res || []
    } else if (activeTab.value === 'blacklist') {
      const res = await api.get('/api/admin/blacklist')
      blacklist.value = res.items || res || []
    }
  } catch (e) {
    authStore.toast('加载数据失败', 'error')
  } finally {
    loading.value = false
  }
}

async function blacklistUser(user) {
  if (!confirm(`确定将 ${user.real_name} 加入黑名单？`)) return
  try {
    await api.post(`/api/admin/users/${user.id}/blacklist`, {})
    authStore.toast('已加入黑名单', 'success')
    loadData()
  } catch (e) {
    authStore.toast(e.message || '操作失败', 'error')
  }
}

async function unblacklistUser(user) {
  if (!confirm(`确定解除 ${user.real_name} 的黑名单？`)) return
  try {
    await api.post(`/api/admin/users/${user.id}/unblacklist`)
    authStore.toast('已解除黑名单', 'success')
    loadData()
  } catch (e) {
    authStore.toast(e.message || '操作失败', 'error')
  }
}

function viewDemand(d) {
  window.open(`/demands/${d.id}`, '_blank')
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.admin-page {
  width: 100%;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  background: #f5f7fa;
  padding: 4px;
  border-radius: 10px;
  overflow-x: auto;
}

.tab {
  padding: 12px 20px;
  border: none;
  background: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab.active {
  background: white;
  color: #667eea;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.loading {
  text-align: center;
  padding: 60px;
  color: #999;
}

.empty-state {
  text-align: center;
  padding: 60px;
  color: #999;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #666;
}

.text-muted {
  font-size: 12px;
  color: #999;
}

.amount {
  color: #ef4444;
  font-weight: 600;
}

.text-success {
  color: #10b981;
}

.text-danger {
  color: #ef4444;
}

.role-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.role-badge.admin {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.role-badge.reviewer {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.待审核,
.status-badge.待处理 {
  background: #fff3cd;
  color: #856404;
}

.status-badge.通过,
.status-badge.进行中,
.status-badge.已解决 {
  background: #d4edda;
  color: #155724;
}

.status-badge.驳回,
.status-badge.已取消 {
  background: #e9ecef;
  color: #666;
}
</style>
