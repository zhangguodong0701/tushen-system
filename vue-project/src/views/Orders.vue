<template>
  <div class="orders-page">
    <div class="page-header">
      <h2>订单管理</h2>
    </div>

    <!-- 订单列表 -->
    <div class="card">
      <div class="card-body">
        <!-- 骨架屏 -->
        <div v-if="loading" class="skeleton-list">
          <table class="data-table">
            <thead><tr><th v-for="i in 6" :key="i"><div class="skeleton-line" style="width:60px;height:14px;"></div></th></tr></thead>
            <tbody>
              <tr v-for="i in 5" :key="i">
                <td v-for="j in 6" :key="j"><div class="skeleton-line" :style="`width:${60+Math.random()*30}px;height:14px;`"></div></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else-if="orders.length === 0" class="empty-state">
          <i class="fas fa-shopping-cart"></i>
          <p>暂无订单</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>订单ID</th>
              <th>需求标题</th>
              <th>金额</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.id">
              <td><span class="badge badge-gray">{{ order.id }}</span></td>
              <td>{{ order.demand_title || `需求 #${order.id}` }}</td>
              <td class="amount">¥{{ order.amount }}</td>
              <td>
                <span class="status-badge" :class="order.status">
                  {{ statusText(order.status) }}
                </span>
              </td>
              <td>{{ formatTime(order.created_at) }}</td>
              <td>
                <button class="btn btn-sm btn-outline" @click="viewOrder(order)">
                  查看详情
                </button>
                <button
                  v-if="order.status === '待支付' && isBuyer(order)"
                  class="btn btn-sm btn-primary"
                  @click="handlePay(order)"
                >
                  去支付
                </button>
                <button
                  v-if="order.status === '待验收' && isBuyer(order)"
                  class="btn btn-sm btn-success"
                  @click="handleAccept(order)"
                >
                  确认验收
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 订单详情弹窗 -->
    <div v-if="selectedOrder" class="modal-overlay" @click.self="closeOrderDetail">
      <div class="modal modal-large">
        <div class="modal-header">
          <h3>订单详情 - {{ selectedOrder.demand_title || `需求 #${selectedOrder.id}` }}</h3>
          <button class="btn-close" @click="closeOrderDetail">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="order-info-grid">
            <div class="info-item">
              <label>订单金额</label>
              <span class="amount">¥{{ selectedOrder.amount }}</span>
            </div>
            <div class="info-item">
              <label>订单状态</label>
              <span class="status-badge" :class="selectedOrder.status">
                {{ statusText(selectedOrder.status) }}
              </span>
            </div>
            <div class="info-item">
              <label>甲方</label>
              <span>{{ selectedOrder.buyer_name }}</span>
            </div>
            <div class="info-item">
              <label>乙方</label>
              <span>{{ selectedOrder.seller_name }}</span>
            </div>
          </div>

          <div class="info-section">
            <h4>订单描述</h4>
            <p>{{ selectedOrder.description || '暂无描述' }}</p>
          </div>

          <!-- 付款阶段 -->
          <div v-if="phases.length > 0" class="info-section">
            <h4>付款阶段</h4>
            <div class="phases-list">
              <div v-for="p in phases" :key="p.id" class="phase-item">
                <div class="phase-info">
                  <span class="phase-name">{{ p.name }}</span>
                  <span class="phase-ratio">{{ p.ratio }}%</span>
                  <span class="phase-amount">¥{{ p.amount?.toFixed(2) || (selectedOrder.amount * p.ratio / 100).toFixed(2) }}</span>
                </div>
                <span class="status-badge" :class="p.status">{{ p.status }}</span>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <button
              v-if="selectedOrder.status === '待支付' && isBuyer(selectedOrder)"
              class="btn btn-primary"
              @click="handlePay(selectedOrder)"
            >
              <i class="fas fa-credit-card"></i> 确认支付 ¥{{ selectedOrder.amount }}
            </button>
            <button
              v-if="selectedOrder.status === '待验收' && isBuyer(selectedOrder)"
              class="btn btn-success"
              @click="handleAccept(selectedOrder)"
            >
              <i class="fas fa-check"></i> 确认验收
            </button>
            <button
              v-if="selectedOrder.status === '进行中' || selectedOrder.status === '待验收'"
              class="btn btn-danger"
              @click="openDisputeForm(selectedOrder)"
            >
              <i class="fas fa-gavel"></i> 发起纠纷
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 发起纠纷表单弹窗 -->
    <div v-if="showDisputeForm" class="modal-overlay" @click.self="showDisputeForm = false">
      <div class="modal">
        <div class="modal-header">
          <h3>发起纠纷</h3>
          <button class="btn-close" @click="showDisputeForm = false">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>订单信息</label>
            <p class="order-info">{{ disputeOrder?.demand_title || `需求 #${disputeOrder?.id}` }} - ¥{{ disputeOrder?.amount }}</p>
          </div>
          <div class="form-group">
            <label>纠纷描述 *</label>
            <textarea v-model="disputeForm.description" placeholder="请详细描述纠纷原因，包括具体问题、沟通情况等" rows="5"></textarea>
          </div>
          <div class="form-actions">
            <button class="btn btn-outline" @click="showDisputeForm = false">取消</button>
            <button class="btn btn-danger" @click="submitDispute" :disabled="submitting || !disputeForm.description">
              {{ submitting ? '提交中...' : '提交纠纷' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="page <= 1" @click="changePage(page - 1)">
        <i class="fas fa-chevron-left"></i> 上一页
      </button>
      <span class="page-info">第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 条</span>
      <button :disabled="page >= totalPages" @click="changePage(page + 1)">
        下一页 <i class="fas fa-chevron-right"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const orders = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 12
const total = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)
const selectedOrder = ref(null)
const phases = ref([])

// 纠纷表单
const showDisputeForm = ref(false)
const disputeOrder = ref(null)
const disputeForm = ref({ description: '' })
const submitting = ref(false)

function changePage(p) {
  page.value = p
  loadOrders()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function loadOrders() {
  loading.value = true
  try {
    const data = await api.get(`/api/orders?page=${page.value}&page_size=${pageSize}`)
    orders.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    authStore.toast('加载订单列表失败', 'error')
  } finally {
    loading.value = false
  }
}

async function viewOrder(order) {
  selectedOrder.value = order
  // 加载付款阶段
  try {
    phases.value = await api.get(`/api/orders/${order.id}/phases`)
  } catch (e) {
    phases.value = []
  }
}

function isBuyer(order) {
  return authStore.user?.id === order.buyer_id
}

function isSeller(order) {
  return authStore.user?.id === order.seller_id
}

function statusText(status) {
  const map = {
    待支付: '待支付',
    进行中: '进行中',
    待验收: '待验收',
    已完成: '已完成',
    已取消: '已取消'
  }
  return map[status] || status
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

async function handlePay(order) {
  if (!confirm(`确认支付 ¥${order.amount}？`)) return
  try {
    await api.post(`/api/orders/${order.id}/pay`, {})
    authStore.toast('支付成功！', 'success')
    selectedOrder.value = null
    loadOrders()
  } catch (e) {
    authStore.toast(e.message || '支付失败', 'error')
  }
}

async function handleAccept(order) {
  if (!confirm('确认验收完成？')) return
  try {
    await api.post(`/api/orders/${order.id}/accept`, {})
    authStore.toast('验收成功！', 'success')
    selectedOrder.value = null
    loadOrders()
  } catch (e) {
    authStore.toast(e.message || '验收失败', 'error')
  }
}

function openDisputeForm(order) {
  disputeOrder.value = order
  disputeForm.value.description = ''
  showDisputeForm.value = true
}

async function submitDispute() {
  if (!disputeForm.value.description.trim()) {
    authStore.toast('请填写纠纷描述', 'error')
    return
  }
  
  submitting.value = true
  try {
    await api.post('/api/disputes', {
      order_id: disputeOrder.value.id,
      description: disputeForm.value.description
    })
    authStore.toast('纠纷已提交，客服将尽快处理', 'success')
    showDisputeForm.value = false
    selectedOrder.value = null
    loadOrders()
    router.push('/disputes')
  } catch (e) {
    authStore.toast(e.message || '提交纠纷失败', 'error')
  } finally {
    submitting.value = false
  }
}

function closeOrderDetail() {
  selectedOrder.value = null
  phases.value = []
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.orders-page {
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

.amount {
  color: #ef4444;
  font-weight: 600;
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

.status-badge.待支付 {
  background: #fff3cd;
  color: #856404;
}

.status-badge.进行中 {
  background: #cce5ff;
  color: #004085;
}

.status-badge.待验收 {
  background: #fed7d7;
  color: #c53030;
}

.status-badge.已完成 {
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
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-large {
  max-width: 700px;
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
  font-size: 18px;
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

.order-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.info-item label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.info-item span {
  font-size: 16px;
  font-weight: 500;
}

.info-section {
  margin-bottom: 24px;
}

.info-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #666;
}

.info-section p {
  margin: 0;
  color: #333;
  line-height: 1.6;
}

.phases-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.phase-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.phase-info {
  display: flex;
  gap: 16px;
  align-items: center;
}

.phase-name {
  font-weight: 500;
}

.phase-ratio {
  color: #667eea;
}

.phase-amount {
  color: #ef4444;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.btn-danger {
  background: #ef4444 !important;
  border-color: #ef4444 !important;
  color: white !important;
}

.btn-danger:hover {
  background: #dc2626 !important;
  border-color: #dc2626 !important;
}

.btn-danger:disabled {
  background: #fca5a5 !important;
  border-color: #fca5a5 !important;
  cursor: not-allowed;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
}

.order-info {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  margin: 0;
  color: #333;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 骨架屏 */
.skeleton-line {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.page-info {
  color: #666;
  font-size: 14px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination button:hover:not(:disabled) {
  background: #f5f7fa;
}
</style>
