<template>
  <div class="disputes-page">
    <!-- 纠纷列表 -->
    <div class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <div v-else-if="disputes.length === 0" class="empty-state">
          <i class="fas fa-gavel"></i>
          <p>暂无纠纷记录</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>编号</th>
              <th>订单</th>
              <th>纠纷类型</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in disputes" :key="d.id">
              <td><span class="badge badge-gray">{{ d.serial_number || `#${d.id}` }}</span></td>
              <td>{{ d.order_title || d.order_serial_number || '关联订单' }}</td>
              <td>{{ d.dispute_type }}</td>
              <td>
                <span class="status-badge" :class="d.status">
                  {{ d.status }}
                </span>
              </td>
              <td>{{ formatTime(d.created_at) }}</td>
              <td>
                <button class="btn btn-sm btn-outline" @click="viewDispute(d)">
                  查看详情
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 纠纷详情弹窗 -->
    <div v-if="selectedDispute" class="modal-overlay" @click.self="selectedDispute = null">
      <div class="modal">
        <!-- 标题栏 -->
        <div class="modal-header">
          <div class="header-left">
            <div class="header-icon">
              <i class="fas fa-gavel"></i>
            </div>
            <div class="header-text">
              <h3>纠纷详情</h3>
              <span class="header-sub">{{ selectedDispute.serial_number || `#${selectedDispute.id}` }}</span>
            </div>
          </div>
          <button class="btn-close" @click="selectedDispute = null">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <!-- 内容区 -->
        <div class="modal-body">
          <!-- 状态卡片 -->
          <div class="status-card" :class="selectedDispute.status">
            <div class="status-item">
              <span class="status-label">纠纷类型</span>
              <span class="status-value">{{ selectedDispute.dispute_type }}</span>
            </div>
            <div class="status-divider"></div>
            <div class="status-item">
              <span class="status-label">当前状态</span>
              <span class="status-badge" :class="selectedDispute.status">
                {{ selectedDispute.status }}
              </span>
            </div>
            <div class="status-divider"></div>
            <div class="status-item">
              <span class="status-label">关联订单</span>
              <span class="status-value">{{ selectedDispute.order_title || selectedDispute.order_serial_number || '关联订单' }}</span>
            </div>
          </div>

          <!-- 纠纷描述 -->
          <div class="detail-section">
            <div class="section-header">
              <i class="fas fa-file-alt"></i>
              <span>纠纷描述</span>
            </div>
            <div class="section-content">
              {{ selectedDispute.description || '暂无描述' }}
            </div>
          </div>

          <!-- 处理结果 -->
          <div v-if="selectedDispute.result" class="detail-section">
            <div class="section-header success">
              <i class="fas fa-check-circle"></i>
              <span>处理结果</span>
            </div>
            <div class="section-content result-content">
              {{ selectedDispute.result }}
            </div>
          </div>

          <!-- 证据附件 -->
          <div v-if="selectedDispute.evidence_url" class="detail-section">
            <div class="section-header">
              <i class="fas fa-paperclip"></i>
              <span>证据附件</span>
            </div>
            <div class="evidence-item">
              <i class="fas fa-file-pdf"></i>
              <span class="evidence-name">证据文件</span>
              <a :href="api.baseURL + selectedDispute.evidence_url" target="_blank" class="btn btn-sm btn-outline">
                <i class="fas fa-download"></i>
                下载查看
              </a>
            </div>
          </div>

          <!-- 时间信息 -->
          <div class="time-info">
            <i class="far fa-clock"></i>
            提交时间：{{ formatTime(selectedDispute.created_at) }}
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="selectedDispute = null">关闭</button>
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
const disputes = ref([])
const loading = ref(false)
const selectedDispute = ref(null)

async function loadDisputes() {
  loading.value = true
  try {
    const data = await api.get('/api/disputes')
    // 处理分页格式：后端返回 {total, page, page_size, items: []}
    disputes.value = data.items || data || []
  } catch (e) {
    authStore.toast('加载纠纷列表失败', 'error')
  } finally {
    loading.value = false
  }
}

function viewDispute(d) {
  selectedDispute.value = d
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadDisputes()
})
</script>

<style scoped>
.disputes-page {
  width: 100%;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.loading,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty-state i {
  font-size: 36px;
  margin-bottom: 12px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #666;
  font-size: 12px;
  text-transform: uppercase;
}

.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.badge-gray {
  background: #e9ecef;
  color: #666;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.待处理 {
  background: #fff3cd;
  color: #856404;
}

.status-badge.处理中 {
  background: #cce5ff;
  color: #004085;
}

.status-badge.已解决 {
  background: #d4edda;
  color: #155724;
}

/* 弹窗样式 - B端设计规范 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 560px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 标题栏 */
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.header-text h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-sub {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
  display: block;
}

.btn-close {
  width: 32px;
  height: 32px;
  background: #f5f5f5;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  background: #e8e8e8;
  color: #333;
}

/* 内容区 */
.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}

/* 状态卡片 */
.status-card {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: #f8f9fa;
  border-radius: 10px;
  margin-bottom: 20px;
}

.status-card.待处理 {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(255, 193, 7, 0.05));
  border: 1px solid rgba(255, 193, 7, 0.3);
}

.status-card.处理中 {
  background: linear-gradient(135deg, rgba(0, 123, 255, 0.1), rgba(0, 123, 255, 0.05));
  border: 1px solid rgba(0, 123, 255, 0.3);
}

.status-card.已解决 {
  background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(40, 167, 69, 0.05));
  border: 1px solid rgba(40, 167, 69, 0.3);
}

.status-item {
  flex: 1;
  text-align: center;
}

.status-label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 6px;
}

.status-value {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.status-divider {
  width: 1px;
  height: 40px;
  background: #e0e0e0;
  margin: 0 16px;
}

/* 详情区块 */
.detail-section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.section-header i {
  color: #667eea;
  font-size: 14px;
}

.section-header.success i {
  color: #28a745;
}

.section-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.7;
  color: #555;
}

.result-content {
  background: linear-gradient(135deg, rgba(40, 167, 69, 0.08), rgba(40, 167, 69, 0.02));
  border: 1px solid rgba(40, 167, 69, 0.2);
  color: #28a745;
}

/* 证据附件 */
.evidence-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  gap: 12px;
}

.evidence-item i {
  font-size: 24px;
  color: #dc3545;
}

.evidence-name {
  flex: 1;
  font-size: 14px;
  color: #333;
}

/* 时间信息 */
.time-info {
  text-align: center;
  font-size: 12px;
  color: #999;
  padding-top: 16px;
  border-top: 1px dashed #eee;
  margin-top: 16px;
}

.time-info i {
  margin-right: 6px;
}

/* 底部按钮 */
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  flex-shrink: 0;
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
}

.btn-secondary:hover {
  background: #e8e8e8;
  color: #333;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-outline {
  background: white;
  border: 1px solid #ddd;
  color: #667eea;
}

.btn-outline:hover {
  background: #f8f9fa;
  border-color: #667eea;
}
</style>
