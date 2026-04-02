<template>
  <div class="demands-page">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <select v-model="filters.status" @change="loadDemands">
          <option value="">全部状态</option>
          <option value="待审核">待审核</option>
          <option value="进行中">进行中</option>
          <option value="已关闭">已关闭</option>
        </select>
        <select v-model="filters.category" @change="loadDemands">
          <option value="">全部分类</option>
          <option value="施工图">施工图审查</option>
          <option value="BIM">BIM审图</option>
          <option value="消防">消防审查</option>
          <option value="节能">节能审查</option>
        </select>
      </div>
      <div class="filter-right">
        <input
          v-model="filters.keyword"
          type="text"
          placeholder="搜索需求标题..."
          @keyup.enter="loadDemands"
        />
        <button class="btn btn-primary" @click="loadDemands">
          <i class="fas fa-search"></i> 搜索
        </button>
      </div>
    </div>

    <!-- 骨架屏 -->
    <div v-if="loading" class="skeleton-grid">
      <div v-for="i in 6" :key="i" class="skeleton-card">
        <div class="skeleton-line" style="width: 30%; height: 18px; margin-bottom: 12px;"></div>
        <div class="skeleton-line" style="width: 80%; height: 20px; margin-bottom: 8px;"></div>
        <div class="skeleton-line" style="width: 60%; height: 16px; margin-bottom: 16px;"></div>
        <div style="display: flex; gap: 12px;">
          <div class="skeleton-line" style="width: 80px; height: 14px;"></div>
          <div class="skeleton-line" style="width: 80px; height: 14px;"></div>
        </div>
      </div>
    </div>
    <div v-else-if="demands.length === 0" class="empty-state">
      <i class="fas fa-inbox"></i>
      <p>暂无相关需求</p>
      <button v-if="authStore.isBuyer" class="btn btn-primary" @click="router.push('/demands/create')">
        发布第一个需求
      </button>
    </div>
    <div v-else class="demands-grid">
      <div v-for="d in demands" :key="d.id" class="demand-card" @click="viewDetail(d.id)">
        <div class="demand-header">
          <span class="category-tag">{{ d.profession || '未分类' }}</span>
          <span class="status-tag" :class="d.status">{{ d.status }}</span>
        </div>
        <h3 class="demand-title">{{ d.title }}</h3>
        <p class="demand-desc">{{ d.description }}</p>
        <div class="demand-meta">
          <span><i class="fas fa-clock"></i> {{ formatTime(d.created_at) }}</span>
          <span><i class="fas fa-tag"></i> {{ d.budget ? `¥${d.budget}` : '待议价' }}</span>
          <span v-if="d.payment_phases && d.payment_phases.length > 0" class="payment-tag stage">
            <i class="fas fa-tasks"></i> 分阶段
          </span>
          <span v-else class="payment-tag once">
            <i class="fas fa-credit-card"></i> 一次性
          </span>
        </div>
        <div class="demand-footer">
          <span class="quote-count">
            <i class="fas fa-file-invoice-dollar"></i>
            {{ d.quote_count || 0 }} 个报价
          </span>
          <span class="buyer-name">{{ d.owner_name }}</span>
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

const filters = ref({
  status: '',
  category: '',
  keyword: ''
})

async function loadDemands() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.status) params.append('status', filters.value.status)
    if (filters.value.category) params.append('profession', filters.value.category)
    if (filters.value.keyword) params.append('keyword', filters.value.keyword)
    params.append('page', page.value)
    params.append('page_size', pageSize)

    const data = await api.get(`/api/demands?${params.toString()}`)
    demands.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    authStore.toast('加载需求列表失败', 'error')
  } finally {
    loading.value = false
  }
}

function viewDetail(id) {
  router.push(`/demands/${id}`)
}

function formatTime(time) {
  if (!time) return '-'
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadDemands()
})
</script>

<style scoped>
.demands-page {
  width: 100%;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-left,
.filter-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-bar select,
.filter-bar input {
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.filter-bar input {
  width: 200px;
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

.demands-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.demand-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.demand-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.demand-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.category-tag {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.待审核 {
  background: #fff3cd;
  color: #856404;
}

.status-tag.进行中 {
  background: #d4edda;
  color: #155724;
}

.status-tag.已关闭 {
  background: #e9ecef;
  color: #666;
}

.demand-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #333;
}

.demand-desc {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.demand-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #999;
  margin-bottom: 12px;
}

.demand-meta i {
  margin-right: 4px;
}

.demand-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.quote-count {
  color: #667eea;
  font-size: 13px;
}

.quote-count i {
  margin-right: 4px;
}

.buyer-name {
  color: #999;
  font-size: 13px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 32px;
}

.pagination button {
  padding: 8px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination button:hover:not(:disabled) {
  background: #f5f7fa;
}

.payment-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.payment-tag.once {
  background: #d4edda;
  color: #155724;
}

.payment-tag.stage {
  background: #cce5ff;
  color: #004085;
}

/* 骨架屏 */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.skeleton-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

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
</style>
