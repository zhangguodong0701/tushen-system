<template>
  <div class="my-demands-page">
    <div class="card">
      <div class="card-body">
        <!-- 骨架屏 -->
        <div v-if="loading" class="skeleton-list">
          <table class="data-table">
            <thead><tr><th v-for="i in 7" :key="i"><div class="skeleton-line" style="width:60px;height:14px;"></div></th></tr></thead>
            <tbody>
              <tr v-for="i in 5" :key="i">
                <td v-for="j in 7" :key="j"><div class="skeleton-line" :style="`width:${60+Math.random()*30}px;height:14px;`"></div></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else-if="demands.length === 0" class="empty-state">
          <i class="fas fa-tasks"></i>
          <p>您还没有发布任何需求</p>
          <button v-if="authStore.isBuyer" class="btn btn-primary" @click="router.push('/demands/create')">
            发布第一个需求
          </button>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>需求标题</th>
              <th>预算</th>
              <th>付款方式</th>
              <th>报价数</th>
              <th>状态</th>
              <th>发布时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in demands" :key="d.id">
              <td><span class="badge badge-gray">#{{ d.id }}</span></td>
              <td>
                <a href="#" @click.prevent="router.push(`/demands/${d.id}`)">{{ d.title }}</a>
              </td>
              <td>{{ d.budget_min && d.budget_max ? `¥${d.budget_min}-${d.budget_max}` : '待议价' }}</td>
              <td>
                <span v-if="d.payment_phases && d.payment_phases.length > 0" class="payment-tag stage">
                  <i class="fas fa-tasks"></i> 分阶段
                </span>
                <span v-else class="payment-tag once">
                  <i class="fas fa-credit-card"></i> 一次性
                </span>
              </td>
              <td>{{ d.quote_count || 0 }}</td>
              <td>
                <span 
                  class="status-badge" 
                  :class="d.status"
                  :style="getStatusStyle(d.status)"
                >{{ d.status }}</span>
              </td>
              <td>{{ formatTime(d.created_at) }}</td>
              <td style="vertical-align: middle">
                <span style="display: inline-flex; gap: 8px; align-items: center; flex-wrap: wrap">
                  <button class="btn btn-sm btn-outline" style="min-width: 56px; padding: 4px 12px" @click="router.push(`/demands/${d.id}`)">
                    查看
                  </button>
                  <button
                    v-if="d.status === '待审核' || d.status === '草稿' || d.status === '待完善'"
                    class="btn btn-sm btn-outline"
                    style="min-width: 56px; padding: 4px 12px"
                    @click="handleEdit(d)"
                  >
                    编辑
                  </button>
                  <button
                    v-if="d.status === '进行中' && !d.accepted_quote_id"
                    class="btn btn-sm btn-primary"
                    style="min-width: 56px; padding: 4px 12px"
                    @click="router.push(`/demands/${d.id}`)"
                  >
                    选标
                  </button>
                  <button
                    v-if="d.status === '进行中' && !d.chosen_quote_id"
                    class="btn btn-sm btn-outline"
                    style="min-width: 56px; padding: 4px 12px"
                    @click="handleClose(d)"
                  >
                    关闭
                  </button>
                  <button
                    v-else-if="d.status === '进行中'"
                    class="btn btn-sm btn-outline"
                    style="min-width: 56px; padding: 4px 12px; opacity: 0.5; cursor: not-allowed"
                    disabled
                    title="已有中标方，无法关闭"
                  >
                    关闭
                  </button>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
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

const demands = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 12
const total = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)

function changePage(p) {
  page.value = p
  loadDemands()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function loadDemands() {
  loading.value = true
  try {
    const data = await api.get(`/api/demands/my?page=${page.value}&page_size=${pageSize}`)
    demands.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    authStore.toast('加载需求列表失败', 'error')
  } finally {
    loading.value = false
  }
}

function handleEdit(d) {
  router.push(`/demands/${d.id}/edit`)
}

async function handleClose(d) {
  if (!confirm('确定要关闭此需求吗？关闭后将不再接受新的报价。')) return
  try {
    await api.post(`/api/demands/${d.id}/close`, {})
    authStore.toast('需求已关闭', 'success')
    loadDemands()
  } catch (e) {
    authStore.toast(e.message || '关闭失败', 'error')
  }
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleDateString('zh-CN')
}

function getStatusStyle(status) {
  const styles = {
    '待审核': 'background: #fff3cd; color: #856404;',
    '进行中': 'background: #d4edda; color: #155724;',
    '已关闭': 'background: #e9ecef; color: #666;',
    '草稿': 'background: #e2e3e5; color: #383d41;',
    '待完善': 'background: #e2e3e5; color: #383d41;',
    '已发布': 'background: #cce5ff; color: #004085;'
  }
  return styles[status] || 'background: #e9ecef; color: #666;'
}

onMounted(() => {
  loadDemands()
})
</script>

<style scoped>
.my-demands-page {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.data-table a:hover {
  text-decoration: underline;
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

.status-badge.待审核 {
  background: #fff3cd;
  color: #856404;
}

.status-badge.进行中 {
  background: #d4edda;
  color: #155724;
}

.status-badge.已关闭 {
  background: #e9ecef;
  color: #666;
}

.payment-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.payment-tag.once {
  background: #d4edda;
  color: #155724;
}

.payment-tag.stage {
  background: #cce5ff;
  color: #004085;
}

:deep(.btn) {
  display: inline-flex !important;
  flex-direction: row !important;
  width: auto !important;
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
