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
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <select v-model="filters.userStatus" @change="loadData()" class="filter-select">
          <option value="待审核">待审核</option>
          <option value="通过">已通过</option>
          <option value="驳回">已驳回</option>
        </select>
        <span class="filter-hint">筛选最早提交的用户优先处理</span>
      </div>
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
              <td>#{{ u.id }}</td>
              <td>
                <div>{{ u.real_name }}</div>
                <div class="text-muted">{{ u.phone }}</div>
              </td>
              <td>{{ u.role }} / {{ u.user_type }}</td>
              <td>{{ u.auth_type || '-' }}</td>
              <td>{{ formatTime(u.created_at) }}</td>
              <td>
                <div class="action-cell">
                  <!-- 仅待审核状态才显示通过/驳回按钮 -->
                  <template v-if="u.status === '待审核'">
                    <button class="btn btn-sm btn-success" @click="handleApprove(u)">通过</button>
                    <button class="btn btn-sm btn-danger" @click="handleReject(u)">驳回</button>
                  </template>
                  <!-- 已通过/已驳回显示状态标签 -->
                  <span v-else-if="u.status === '通过'" class="status-tag status-approved">✓ 已通过</span>
                  <span v-else-if="u.status === '驳回'" class="status-tag status-rejected">✗ 已驳回</span>
                  <button class="btn btn-sm btn-outline" @click="viewUserDetail(u)">详情</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 纠纷处理 -->
    <div v-if="activeTab === 'disputes'" class="card">
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <select v-model="filters.disputeStatus" @change="loadData()" class="filter-select">
          <option value="">全部状态</option>
          <option value="处理中">处理中</option>
          <option value="已解决">已解决</option>
        </select>
        <span class="filter-hint">筛选最早提交的用户优先处理</span>
      </div>
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
              <th>状态</th>
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
                <span :class="['status-tag', d.status === '处理中' ? 'status-pending' : 'status-approved']">
                  {{ d.status === '处理中' ? '⏳ 处理中' : '✓ 已解决' }}
                </span>
              </td>
              <td>
                <div class="action-cell">
                  <button v-if="d.status === '处理中'" class="btn btn-sm btn-primary" @click="handleDispute(d)">处理</button>
                  <button v-else class="btn btn-sm btn-outline" @click="handleDispute(d)">查看</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 投诉反馈 -->
    <div v-if="activeTab === 'feedbacks'" class="card">
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <select v-model="filters.feedbackStatus" @change="loadData()" class="filter-select">
          <option value="">全部状态</option>
          <option value="待处理">待处理</option>
          <option value="已处理">已处理</option>
        </select>
        <span class="filter-hint">筛选最早提交的用户优先处理</span>
      </div>
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

    <!-- 纠纷处理弹窗 -->
    <div v-if="selectedDispute" class="modal-overlay" @click.self="selectedDispute = null">
      <div class="modal dispute-modal">
        <div class="modal-header">
          <h3>处理纠纷 #{{ selectedDispute.id }}</h3>
          <button class="btn-close" @click="selectedDispute = null">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <!-- 基本信息 -->
          <div class="info-section">
            <h4>纠纷信息</h4>
            <div class="info-row">
              <label>关联订单：</label>
              <span>{{ selectedDispute.order_title || `订单 #${selectedDispute.order_id}` }}</span>
            </div>
            <div class="info-row">
              <label>纠纷类型：</label>
              <span>{{ selectedDispute.dispute_type }}</span>
            </div>
            <div class="info-row">
              <label>发起人：</label>
              <span>{{ selectedDispute.initiator_name }}</span>
            </div>
            <div class="info-row">
              <label>发起时间：</label>
              <span>{{ formatTime(selectedDispute.created_at) }}</span>
            </div>
            <div class="info-row">
              <label>当前状态：</label>
              <span :class="['status-badge', selectedDispute.status === '处理中' ? 'status-pending' : 'status-resolved']">
                {{ selectedDispute.status }}
              </span>
            </div>
          </div>

          <!-- 纠纷描述 -->
          <div class="info-section">
            <h4>纠纷描述</h4>
            <div class="description-box">{{ selectedDispute.description }}</div>
          </div>

          <!-- 证据材料 -->
          <div v-if="(selectedDispute.evidence_url || selectedDispute.evidence_files)" class="info-section">
            <h4>证据材料</h4>
            <div class="evidence-gallery">
              <div v-if="selectedDispute.evidence_url" class="evidence-item">
                <img :src="getFileUrl(selectedDispute.evidence_url)" alt="证据" />
              </div>
              <div v-if="selectedDispute.evidence_files" v-for="(url, idx) in JSON.parse(selectedDispute.evidence_files)" :key="idx" class="evidence-item">
                <img :src="getFileUrl(url)" alt="证据" />
              </div>
            </div>
          </div>

          <!-- 处理结果（如果已处理） -->
          <div v-if="selectedDispute.resolution" class="info-section">
            <h4>处理结果</h4>
            <div class="resolution-box">
              <div class="info-row">
                <label>处理方式：</label>
                <span>{{ selectedDispute.resolution.type === 'refund' ? '退款给甲方' : '放款给乙方' }}</span>
              </div>
              <div class="info-row">
                <label>处理时间：</label>
                <span>{{ formatTime(selectedDispute.resolved_at) }}</span>
              </div>
              <div v-if="selectedDispute.resolution.note" class="info-row">
                <label>处理备注：</label>
                <span>{{ selectedDispute.resolution.note }}</span>
              </div>
            </div>
          </div>

          <!-- 处理表单（如果未处理） -->
          <div v-if="selectedDispute.status === '处理中'" class="info-section">
            <h4>处理操作</h4>
            <div class="action-form">
              <div class="action-buttons">
                <button
                  class="btn btn-danger"
                  :disabled="processing"
                  @click="resolveDispute('refund')"
                >
                  <i class="fas fa-undo"></i> 退款给甲方
                </button>
                <button
                  class="btn btn-success"
                  :disabled="processing"
                  @click="resolveDispute('release')"
                >
                  <i class="fas fa-check"></i> 放款给乙方
                </button>
              </div>
              <div class="action-note">
                <textarea
                  v-model="disputeNote"
                  placeholder="输入处理备注（可选）..."
                  rows="3"
                ></textarea>
              </div>
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
const selectedDispute = ref(null)  // 当前处理的纠纷
const disputeNote = ref('')       // 纠纷处理备注
const processing = ref(false)     // 处理中状态
const replyContent = ref({})  // { [feedbackId]: string }

const tabs = ref([
  { key: 'users', label: '用户审核', count: 0 },
  { key: 'disputes', label: '纠纷处理', count: 0 },
  { key: 'feedbacks', label: '投诉反馈', count: 0 }
])

// 筛选条件
const filters = ref({
  userStatus: '待审核',  // 用户审核状态：待审核/通过/驳回
  disputeStatus: '',      // 纠纷状态：处理中/已解决
  feedbackStatus: ''    // 反馈状态：待处理/已处理
})

// 加载所有 tab 的数量（badge 显示用）
async function loadCounts() {
  try {
    const [pendingUsers, pendingDisputes, pendingFeedbacks] = await Promise.all([
      api.get('/api/admin/users?status=待审核').catch(() => []),
      api.get('/api/disputes?status=处理中').catch(() => []),
      api.get('/api/feedback?status=待处理').catch(() => [])
    ])
    tabs.value[0].count = pendingUsers.total || 0  // 待审核用户数
    tabs.value[1].count = Array.isArray(pendingDisputes) ? pendingDisputes.length : (pendingDisputes.total || 0)
    tabs.value[2].count = pendingFeedbacks.total || 0
  } catch {}
}

async function loadData() {
  loading.value = true
  try {
    // 先刷新所有 badge 数量
    await loadCounts()
    if (activeTab.value === 'users') {
      // 用户审核：支持按审核状态筛选
      const data = await api.get(`/api/admin/users?status=${filters.value.userStatus}`)
      users.value = data.items || data || []
    } else if (activeTab.value === 'disputes') {
      // 纠纷处理：支持按状态筛选
      let url = '/api/disputes'
      if (filters.value.disputeStatus) {
        url += `?status=${filters.value.disputeStatus}`
      }
      const data = await api.get(url)
      disputes.value = data.items || data || []
    } else if (activeTab.value === 'feedbacks') {
      // 投诉反馈：支持按状态筛选
      let url = '/api/feedback'
      if (filters.value.feedbackStatus) {
        url += `?status=${filters.value.feedbackStatus}`
      }
      const data = await api.get(url)
      feedbacks.value = data.items || data || []
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

async function handleDispute(d) {
  // 打开纠纷处理弹窗
  selectedDispute.value = d
  disputeNote.value = ''
}

async function resolveDispute(action) {
  if (!selectedDispute.value) return
  processing.value = true
  try {
    // 后端使用 Form 格式，需要用 FormData
    const formData = new FormData()
    formData.append('action', action)
    formData.append('result', disputeNote.value || (action === 'refund' ? '管理员裁决退款' : '管理员裁决放款'))
    await api.postForm(`/api/admin/disputes/${selectedDispute.value.id}/resolve`, formData)
    authStore.toast('处理成功', 'success')
    selectedDispute.value = null
    loadData()
  } catch (e) {
    authStore.toast(e.message || '处理失败', 'error')
  } finally {
    processing.value = false
  }
}

async function submitReply(f) {
  const content = (replyContent.value[f.id] || '').trim()
  if (!content) {
    authStore.toast('请输入回复内容', 'error')
    return
  }
  try {
    await api.post(`/api/feedback/${f.id}/reply`, { reply: content })
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
  margin-bottom: 16px;
  background: #f5f7fa;
  padding: 4px;
  border-radius: 10px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  min-width: 120px;
}

.filter-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.filter-hint {
  font-size: 13px;
  color: #999;
  margin-left: auto;
}

.status-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  margin-right: 6px;
}

.status-approved {
  background: #d4edda;
  color: #155724;
}

.status-pending {
  background: #fff3cd;
  color: #856404;
}

.status-rejected {
  background: #f8d7da;
  color: #721c24;
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

/* 纠纷处理弹窗样式 */
.dispute-modal {
  max-width: 700px;
}

.info-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.info-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.info-section h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #333;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.status-pending {
  background: #fef3cd;
  color: #856404;
}

.status-resolved {
  background: #d4edda;
  color: #155724;
}

.description-box {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  line-height: 1.6;
  color: #333;
}

.evidence-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.evidence-item {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #eee;
}

.evidence-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
}

.evidence-item img:hover {
  transform: scale(1.05);
}

.resolution-box {
  padding: 12px;
  background: #d4edda;
  border-radius: 8px;
}

.action-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.action-cell .btn {
  width: auto !important;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.action-buttons .btn {
  flex: 1;
  padding: 12px 20px;
  font-size: 15px;
}

.action-note textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
  box-sizing: border-box;
}

.action-note textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}
</style>
