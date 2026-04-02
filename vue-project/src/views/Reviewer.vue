<template>
  <div class="reviewer-page">
    <!-- Tab 切换 -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key; loadData()"
      >
        {{ tab.label }}
        <span v-if="tab.count" class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <!-- 用户审核 -->
    <div v-if="activeTab === 'users'" class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <div v-else-if="users.length === 0" class="empty-state">
          <i class="fas fa-users"></i>
          <p>暂无待审核用户</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户</th>
              <th>类型</th>
              <th>认证类型</th>
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
              <td>{{ u.role }} / {{ u.user_type }}</td>
              <td>{{ u.auth_type || '-' }}</td>
              <td>{{ formatTime(u.created_at) }}</td>
              <td>
                <button class="btn btn-sm btn-success" @click="handleApprove(u)">
                  通过
                </button>
                <button class="btn btn-sm btn-danger" @click="handleReject(u)">
                  驳回
                </button>
                <button class="btn btn-sm btn-outline" @click="viewUserDetail(u)">
                  详情
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 纠纷处理 -->
    <div v-if="activeTab === 'disputes'" class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <div v-else-if="disputes.length === 0" class="empty-state">
          <i class="fas fa-gavel"></i>
          <p>暂无待处理纠纷</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>订单</th>
              <th>类型</th>
              <th>发起人</th>
              <th>时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in disputes" :key="d.id">
              <td>#{{ d.id }}</td>
              <td>{{ d.order_title || `订单 #${d.order_id}` }}</td>
              <td>{{ d.dispute_type }}</td>
              <td>{{ d.initiator_name }}</td>
              <td>{{ formatTime(d.created_at) }}</td>
              <td>
                <button class="btn btn-sm btn-primary" @click="handleDispute(d)">
                  处理
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 投诉反馈 -->
    <div v-if="activeTab === 'feedbacks'" class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <div v-else-if="feedbacks.length === 0" class="empty-state">
          <i class="fas fa-comment-dots"></i>
          <p>暂无待处理反馈</p>
        </div>
        <div v-else class="feedback-list">
          <div v-for="f in feedbacks" :key="f.id" class="feedback-item">
            <div class="feedback-header">
              <span class="user">{{ f.user_name }}</span>
              <span class="time">{{ formatTime(f.created_at) }}</span>
            </div>
            <div class="feedback-content">{{ f.content }}</div>
            <div v-if="!f.reply" class="feedback-reply-form">
              <textarea
                v-model="replyContent[f.id]"
                placeholder="请输入回复内容..."
                rows="3"
                style="width: 100%; box-sizing: border-box;"
              ></textarea>
              <button class="btn btn-primary btn-sm" @click="submitReply(f)">
                提交回复
              </button>
            </div>
            <div v-else class="feedback-reply">
              <strong>官方回复：</strong>{{ f.reply }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 用户详情弹窗 -->
    <div v-if="selectedUser" class="modal-overlay" @click.self="selectedUser = null">
      <div class="modal">
        <div class="modal-header">
          <h3>用户详情</h3>
          <button class="btn-close" @click="selectedUser = null">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="info-row">
            <label>姓名：</label>
            <span>{{ selectedUser.real_name }}</span>
          </div>
          <div class="info-row">
            <label>手机号：</label>
            <span>{{ selectedUser.phone }}</span>
          </div>
          <div class="info-row">
            <label>邮箱：</label>
            <span>{{ selectedUser.email || '-' }}</span>
          </div>
          <div class="info-row">
            <label>角色：</label>
            <span>{{ selectedUser.role }} / {{ selectedUser.user_type }}</span>
          </div>
          <div v-if="selectedUser.auth_type === '个人'" class="cert-images">
            <label>身份证照片：</label>
            <div class="cert-row">
              <div v-if="selectedUser.id_card_front" class="cert-item">
                <img :src="getFileUrl(selectedUser.id_card_front)" alt="身份证正面" />
                <small>正面</small>
              </div>
              <div v-if="selectedUser.id_card_back" class="cert-item">
                <img :src="getFileUrl(selectedUser.id_card_back)" alt="身份证背面" />
                <small>背面</small>
              </div>
            </div>
          </div>
          <div v-if="selectedUser.auth_type === '企业'" class="cert-images">
            <label>营业执照：</label>
            <div v-if="selectedUser.business_license" class="cert-item">
              <img :src="getFileUrl(selectedUser.business_license)" alt="营业执照" />
            </div>
          </div>
        </div>
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
const disputes = ref([])
const feedbacks = ref([])
const selectedUser = ref(null)
const replyContent = ref({})  // { [feedbackId]: string }

const tabs = ref([
  { key: 'users', label: '用户审核', count: 0 },
  { key: 'disputes', label: '纠纷处理', count: 0 },
  { key: 'feedbacks', label: '投诉反馈', count: 0 }
])

// 加载所有 tab 的数量（badge 显示用）
async function loadCounts() {
  try {
    const [pendingUsers, pendingDisputes, allFeedbacks] = await Promise.all([
      api.get('/api/admin/users?status=待审核').catch(() => []),
      api.get('/api/disputes?status=待处理').catch(() => []),
      api.get('/api/admin/feedbacks').catch(() => [])
    ])
    tabs.value[0].count = pendingUsers.length
    tabs.value[1].count = pendingDisputes.length
    tabs.value[2].count = allFeedbacks.filter(f => !f.reply).length
  } catch {}
}

async function loadData() {
  loading.value = true
  try {
    // 先刷新所有 badge 数量
    await loadCounts()
    if (activeTab.value === 'users') {
      users.value = await api.get('/api/admin/users?status=待审核')
    } else if (activeTab.value === 'disputes') {
      disputes.value = await api.get('/api/disputes?status=待处理')
    } else if (activeTab.value === 'feedbacks') {
      feedbacks.value = await api.get('/api/admin/feedbacks')
    }
  } catch (e) {
    authStore.toast('加载数据失败', 'error')
  } finally {
    loading.value = false
  }
}

async function handleApprove(user) {
  try {
    await api.post(`/api/admin/users/${user.id}/approve`, {})
    authStore.toast('已通过审核', 'success')
    loadData()
  } catch (e) {
    authStore.toast(e.message || '操作失败', 'error')
  }
}

async function handleReject(user) {
  const reason = prompt('请输入驳回原因：')
  if (!reason) return
  try {
    await api.post(`/api/admin/users/${user.id}/reject`, { reason })
    authStore.toast('已驳回', 'success')
    loadData()
  } catch (e) {
    authStore.toast(e.message || '操作失败', 'error')
  }
}

function viewUserDetail(user) {
  selectedUser.value = user
}

function handleDispute(d) {
  // TODO: 打开纠纷处理弹窗
  authStore.toast('纠纷处理功能开发中', 'info')
}

async function submitReply(f) {
  const content = (replyContent.value[f.id] || '').trim()
  if (!content) {
    authStore.toast('请输入回复内容', 'error')
    return
  }
  try {
    await api.post(`/api/admin/feedbacks/${f.id}/reply`, { reply: content })
    authStore.toast('回复成功', 'success')
    delete replyContent.value[f.id]
    loadData()
  } catch (e) {
    authStore.toast(e.message || '回复失败', 'error')
  }
}

function getFileUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${api.baseURL}${path}`
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
.reviewer-page {
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
}

.tab {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.3s;
}

.tab.active {
  background: white;
  color: #667eea;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.tab-count {
  background: #ef4444;
  color: white;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  margin-left: 6px;
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

.feedback-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feedback-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.feedback-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.feedback-header .user {
  font-weight: 600;
  color: #333;
}

.feedback-header .time {
  font-size: 13px;
  color: #999;
}

.feedback-content {
  color: #333;
  line-height: 1.6;
  margin-bottom: 12px;
}

.feedback-reply-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.feedback-reply-form textarea {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
  box-sizing: border-box;
  background: white;
  font-family: inherit;
}

.feedback-reply-form button {
  align-self: flex-end;
  width: auto !important;
  min-width: 100px;
  padding: 10px 24px;
  display: inline-block !important;
}

.feedback-reply {
  padding: 12px;
  background: white;
  border-radius: 6px;
  font-size: 14px;
  color: #666;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  font-size: 18px;
}

.modal-body {
  padding: 24px;
}

.info-row {
  margin-bottom: 16px;
}

.info-row label {
  font-weight: 600;
  color: #666;
  margin-right: 8px;
}

.cert-images {
  margin-top: 16px;
}

.cert-images label {
  font-weight: 600;
  color: #666;
  display: block;
  margin-bottom: 8px;
}

.cert-row {
  display: flex;
  gap: 16px;
}

.cert-item {
  text-align: center;
}

.cert-item img {
  width: 200px;
  height: 140px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #eee;
}

.cert-item small {
  display: block;
  margin-top: 4px;
  color: #999;
}
</style>
