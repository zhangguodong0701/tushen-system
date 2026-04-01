<template>
  <div class="my-quotes-page">
    <div class="page-header">
      <h2>我的报价</h2>
    </div>

    <div class="card">
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <div v-else-if="quotes.length === 0" class="empty-state">
          <i class="fas fa-file-invoice-dollar"></i>
          <p>您还没有提交任何报价</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>需求</th>
              <th>报价金额</th>
              <th>报价说明</th>
              <th>状态</th>
              <th>报价时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="q in quotes" :key="q.id">
              <td><span class="badge badge-gray">#{{ q.id }}</span></td>
              <td>
                <a href="#" @click.prevent="router.push(`/demands/${q.demand_id}`)">{{ q.demand_title }}</a>
              </td>
              <td class="amount">¥{{ q.price }}</td>
              <td>{{ q.remark || '-' }}</td>
              <td>
                <span class="status-badge" :class="q.status">
                  {{ q.status }}
                </span>
              </td>
              <td>{{ formatTime(q.created_at) }}</td>
              <td>
                <button class="btn btn-sm btn-outline" @click="viewQuote(q)">
                  查看
                </button>
                <button
                  v-if="q.status === '待选择'"
                  class="btn btn-sm btn-outline"
                  @click="openEditModal(q)"
                >
                  编辑
                </button>
                <button
                  v-if="q.status === '待选择'"
                  class="btn btn-sm btn-danger"
                  @click="cancelQuote(q.id)"
                >
                  取消
                </button>
                <span v-if="q.status === '已中标'" class="win-badge">
                  <i class="fas fa-trophy"></i> 已中标
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 报价详情弹窗 -->
    <div v-if="selectedQuote" class="modal-overlay" @click.self="selectedQuote = null">
      <div class="modal">
        <div class="modal-header">
          <h3>报价详情</h3>
          <button class="btn-close" @click="selectedQuote = null">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="info-row">
            <label>需求：</label>
            <span>{{ selectedQuote.demand_title }}</span>
          </div>
          <div class="info-row">
            <label>报价金额：</label>
            <span class="amount">¥{{ selectedQuote.price }}</span>
          </div>
          <div class="info-row">
            <label>报价说明：</label>
            <p>{{ selectedQuote.remark || '暂无' }}</p>
          </div>
          <div class="info-row">
            <label>状态：</label>
            <span class="status-badge" :class="selectedQuote.status">
              {{ selectedQuote.status }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑报价弹窗 -->
    <div v-if="editForm.show" class="modal-overlay" @click.self="editForm.show = false">
      <div class="modal">
        <div class="modal-header">
          <h3>编辑报价</h3>
          <button class="btn-close" @click="editForm.show = false">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-field">
            <label>报价金额 (元) *</label>
            <input v-model.number="editForm.price" type="number" min="1" placeholder="请输入报价金额" />
          </div>
          <div class="form-field">
            <label>报价说明</label>
            <textarea v-model="editForm.remark" rows="4" placeholder="请输入报价说明、服务内容等"></textarea>
          </div>
          <div class="form-actions">
            <button class="btn btn-outline" @click="editForm.show = false">取消</button>
            <button class="btn btn-primary" @click="submitEditQuote" :disabled="editForm.submitting">
              <span v-if="editForm.submitting">提交中...</span>
              <span v-else>保存</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const quotes = ref([])
const loading = ref(false)
const selectedQuote = ref(null)
const editForm = ref({
  show: false,
  id: null,
  price: null,
  remark: '',
  submitting: false
})

async function loadQuotes() {
  loading.value = true
  try {
    quotes.value = await api.get('/api/quotes/my')
  } catch (e) {
    authStore.toast('加载报价列表失败', 'error')
  } finally {
    loading.value = false
  }
}

function viewQuote(q) {
  selectedQuote.value = q
}

function openEditModal(q) {
  editForm.value = {
    show: true,
    id: q.id,
    price: q.price,
    remark: q.remark || '',
    submitting: false
  }
}

async function submitEditQuote() {
  if (!editForm.value.price || editForm.value.price <= 0) {
    authStore.toast('请输入正确的报价金额', 'error')
    return
  }
  editForm.value.submitting = true
  try {
    await api.put(`/api/quotes/${editForm.value.id}`, {
      price: editForm.value.price,
      remark: editForm.value.remark
    })
    authStore.toast('报价已更新', 'success')
    editForm.value.show = false
    await loadQuotes()
  } catch (e) {
    authStore.toast(e.message || '更新报价失败', 'error')
  } finally {
    editForm.value.submitting = false
  }
}

async function cancelQuote(id) {
  if (!confirm('确定要取消此报价吗？取消后无法恢复。')) return
  try {
    await api.delete(`/api/quotes/${id}`)
    authStore.toast('报价已取消', 'success')
    await loadQuotes()
  } catch (e) {
    authStore.toast(e.message || '取消报价失败', 'error')
  }
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadQuotes()
})
</script>

<style scoped>
.my-quotes-page {
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

.data-table a {
  color: #667eea;
  text-decoration: none;
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

.status-badge.待选择 {
  background: #fff3cd;
  color: #856404;
}

.status-badge.已中标 {
  background: #d4edda;
  color: #155724;
}

.status-badge.未中标 {
  background: #e9ecef;
  color: #666;
}

.win-badge {
  color: #f59e0b;
  font-size: 13px;
}

.win-badge i {
  margin-right: 4px;
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
  line-height: 1.6;
}

.form-field {
  margin-bottom: 16px;
}

.form-field label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #666;
}

.form-field input,
.form-field textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #667eea;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-danger {
  background: #ef4444;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.btn-danger:hover {
  background: #dc2626;
}
</style>
