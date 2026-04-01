<template>
  <div class="disputes-page">
    <div class="page-header">
      <h2>纠纷处理</h2>
    </div>

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
              <th>ID</th>
              <th>订单</th>
              <th>纠纷类型</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in disputes" :key="d.id">
              <td><span class="badge badge-gray">#{{ d.id }}</span></td>
              <td>{{ d.order_title || `订单 #${d.order_id}` }}</td>
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
        <div class="modal-header">
          <h3>纠纷详情</h3>
          <button class="btn-close" @click="selectedDispute = null">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="info-row">
            <label>订单：</label>
            <span>{{ selectedDispute.order_title || `订单 #${selectedDispute.order_id}` }}</span>
          </div>
          <div class="info-row">
            <label>纠纷类型：</label>
            <span>{{ selectedDispute.dispute_type }}</span>
          </div>
          <div class="info-row">
            <label>状态：</label>
            <span class="status-badge" :class="selectedDispute.status">
              {{ selectedDispute.status }}
            </span>
          </div>
          <div class="info-row">
            <label>描述：</label>
            <p>{{ selectedDispute.description }}</p>
          </div>
          <div v-if="selectedDispute.result" class="info-row">
            <label>处理结果：</label>
            <p>{{ selectedDispute.result }}</p>
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
const disputes = ref([])
const loading = ref(false)
const selectedDispute = ref(null)

async function loadDisputes() {
  loading.value = true
  try {
    const data = await api.get('/api/disputes')
    disputes.value = data
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
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.loading {
  text-align: center;
  padding: 40px;
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
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
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
  max-width: 500px;
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
}

.info-row p {
  margin: 8px 0 0 0;
  color: #333;
}
</style>
