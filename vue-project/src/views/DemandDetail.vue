<template>
  <div class="demand-detail-page">
    <!-- 返回按钮 -->
    <button class="back-btn" @click="router.push(isCreating ? '/demands' : '/demands')">
      <i class="fas fa-arrow-left"></i> 返回
    </button>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i> 加载中...
    </div>

    <!-- 创建需求表单 -->
    <template v-if="isCreating">
      <div class="create-form-card">
        <h1>发布新需求</h1>
        <div class="form-group">
          <label>需求标题 *</label>
          <input v-model="createForm.title" type="text" placeholder="简要描述您的需求" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>需求分类 *</label>
            <select v-model="createForm.category">
              <option value="">请选择分类</option>
              <option value="施工图审查">施工图审查</option>
              <option value="BIM审图">BIM审图</option>
              <option value="消防审查">消防审查</option>
              <option value="节能审查">节能审查</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="form-group">
            <label>预算范围</label>
            <div class="budget-inputs">
              <input v-model.number="createForm.budget_min" type="number" placeholder="最低" />
              <span>至</span>
              <input v-model.number="createForm.budget_max" type="number" placeholder="最高" />
              <span>元</span>
            </div>
          </div>
        </div>
        <div class="form-group">
          <label>工期要求</label>
          <input v-model="createForm.deadline" type="text" placeholder="预计完成时间，如：7天" />
        </div>
        <div class="form-group">
          <label>需求描述 *</label>
          <textarea v-model="createForm.description" placeholder="详细描述您的需求，包括项目背景、具体要求等" rows="6"></textarea>
        </div>

        <!-- 付款方式选择 -->
        <div class="payment-config">
          <div class="section-header">
            <label>付款方式</label>
          </div>
          <div class="payment-type-selector">
            <label class="payment-type-option">
              <input type="radio" v-model="createForm.payment_type" value="一次性" />
              <span class="payment-type-card">
                <i class="fas fa-credit-card"></i>
                <strong>一次性付清</strong>
                <small>验收完成后一次性支付全款</small>
              </span>
            </label>
            <label class="payment-type-option">
              <input type="radio" v-model="createForm.payment_type" value="分阶段" />
              <span class="payment-type-card">
                <i class="fas fa-tasks"></i>
                <strong>分阶段付款</strong>
                <small>按阶段里程碑分期支付</small>
              </span>
            </label>
          </div>
          
          <!-- 分阶段付款配置（仅分阶段时显示） -->
          <div v-if="createForm.payment_type === '分阶段'" class="phases-editor">
            <div class="section-sub-header">
              <label>阶段配置</label>
              <button type="button" class="btn btn-sm" @click="addPhase">
                <i class="fas fa-plus"></i> 添加阶段
              </button>
            </div>
            <div v-if="createForm.payment_phases.length > 0">
              <div v-for="(phase, idx) in createForm.payment_phases" :key="idx" class="phase-editor-item">
                <input v-model="phase.name" type="text" placeholder="阶段名称，如：需求确认" />
                <input v-model.number="phase.ratio" type="number" placeholder="比例" min="1" max="100" />
                <span>%</span>
                <button type="button" class="btn-icon" @click="removePhase(idx)">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
              <div class="phases-total">
                总计：{{ totalPhaseRatio }}%
                <span v-if="totalPhaseRatio !== 100" class="error">（必须等于100%）</span>
              </div>
            </div>
            <div v-else class="phases-empty">
              <p>请添加付款阶段，例如：需求确认(20%) → 图纸提交(50%) → 验收完成(30%)</p>
            </div>
          </div>
        </div>

        <!-- 图纸上传 -->
        <div class="form-group">
          <label>上传图纸文件</label>
          <div class="upload-area" @click="triggerFileUpload" :class="{ 'has-file': uploadedFileName }">
            <input 
              ref="fileInput"
              type="file" 
              accept=".dwg,.pdf,.zip,.rvt,.jpg,.jpeg,.png"
              style="display:none"
              @change="handleFileChange"
            />
            <template v-if="!uploadedFileName">
              <i class="fas fa-cloud-upload-alt"></i>
              <p>点击或拖拽上传图纸文件</p>
              <small>支持 DWG, PDF, ZIP, RVT, JPG, PNG 格式</small>
            </template>
            <template v-else>
              <i class="fas fa-file-alt"></i>
              <p>{{ uploadedFileName }}</p>
              <small>点击更换文件</small>
            </template>
          </div>
          <div v-if="uploadingFile" class="upload-progress">
            <i class="fas fa-spinner fa-spin"></i> 上传中...
          </div>
          <div v-if="uploadSuccess" class="upload-success">
            <i class="fas fa-check-circle"></i> 上传成功
          </div>
        </div>

        <div class="form-actions">
          <button class="btn btn-primary btn-lg" @click="submitDemand" :disabled="submitting || !isFormValid">
            {{ submitting ? '发布中...' : '发布需求' }}
          </button>
        </div>
      </div>
    </template>

    <!-- 需求详情（详情页面） -->
    <template v-if="demand">
      <!-- 需求基本信息 -->
      <div class="demand-info-card">
        <div class="info-header">
          <div>
            <span class="category-tag">{{ demand.profession }}</span>
            <span class="status-tag" :class="demand.status">{{ demand.status }}</span>
          </div>
          <div class="actions">
            <button v-if="isOwner && (demand.status === '草稿' || demand.status === '待完善')" class="btn btn-primary" @click="router.push(`/demands/${demand.id}/edit`)">
              <i class="fas fa-edit"></i> 编辑需求
            </button>
            <button v-if="isOwner && demand.status === '待审核'" class="btn btn-outline" @click="closeDemand">
              <i class="fas fa-times"></i> 关闭需求
            </button>
          </div>
        </div>

        <h1 class="demand-title">{{ demand.title }}</h1>

        <div class="info-grid">
          <div class="info-item">
            <label>预算范围</label>
            <span>{{ demand.budget ? `¥${demand.budget}` : '待议价' }}</span>
          </div>
          <div class="info-item">
            <label>付款方式</label>
            <span>
              <span v-if="demand.payment_phases && demand.payment_phases.length > 0" class="payment-type-tag stage">
                <i class="fas fa-tasks"></i> 分阶段付款
              </span>
              <span v-else class="payment-type-tag once">
                <i class="fas fa-credit-card"></i> 一次性付清
              </span>
            </span>
          </div>
          <div class="info-item">
            <label>分类</label>
            <span>{{ demand.profession }}</span>
          </div>
          <div class="info-item">
            <label>工期</label>
            <span>{{ demand.deadline || '待议' }}</span>
          </div>
          <div class="info-item">
            <label>发布时间</label>
            <span>{{ formatTime(demand.created_at) }}</span>
          </div>
          <div class="info-item">
            <label>发布者</label>
            <span>{{ demand.buyer_name }}</span>
          </div>
          <div class="info-item">
            <label>报价数量</label>
            <span>{{ quotes.length }} 个</span>
          </div>
        </div>

        <div class="description-section">
          <h3>需求描述</h3>
          <p>{{ demand.description }}</p>

        <!-- 附件下载 -->
        <div v-if="demand.file_url" class="demand-attachments">
          <a :href="API_BASE + demand.file_url" target="_blank" class="btn btn-outline">
            <i class="fas fa-download"></i> 下载图纸文件
          </a>
        </div>
      </div>

      <!-- 分阶段付款配置 -->
        <div v-if="demand.payment_phases && demand.payment_phases.length > 0" class="payment-phases-section">
          <h3>分阶段付款配置</h3>
          <div class="phases-list">
            <div v-for="(phase, idx) in demand.payment_phases" :key="idx" class="phase-item">
              <span class="phase-name">{{ phase.name }}</span>
              <span class="phase-ratio">{{ phase.ratio }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 报价区域 -->
      <div class="quotes-section">
        <h2>服务商报价</h2>

        <!-- 我的报价表单（仅乙方显示） -->
        <div v-if="authStore.isSeller && !hasQuoted && demand.status === '已发布'" class="quote-form">
          <h3>提交报价</h3>
          <div class="form-group">
            <label>报价金额 (元)</label>
            <input v-model.number="quoteForm.price" type="number" placeholder="输入您的报价" />
          </div>
          <div class="form-group">
            <label>报价说明</label>
            <textarea v-model="quoteForm.remark" placeholder="详细说明您的服务内容和优势"></textarea>
          </div>
          <button class="btn btn-primary" @click="submitQuote" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交报价' }}
          </button>
        </div>

        <!-- 已报价提示 -->
        <div v-else-if="authStore.isSeller && hasQuoted" class="quoted-tip">
          <i class="fas fa-check-circle"></i> 您已提交报价
        </div>

        <!-- 报价列表 -->
        <div v-if="quotes.length > 0" class="quotes-list">
          <div v-for="q in quotes" :key="q.id" class="quote-card" :class="{ 'my-quote': q.seller_id === authStore.user?.id }">
            <div class="quote-header">
              <div class="seller-info">
                <span class="seller-name">{{ q.seller_name }}</span>
                <span v-if="q.seller_real_name" class="real-name">（已实名）</span>
              </div>
              <div v-if="demand.chosen_quote_id === q.id" class="chosen-badge">
                <i class="fas fa-star"></i> 已中标
              </div>
            </div>

            <div class="quote-body">
              <div class="quote-price">
                <span class="label">报价</span>
                <span class="value">¥{{ q.price }}</span>
              </div>
              <div v-if="q.delivery_time" class="quote-delivery">
                <span class="label">工期</span>
                <span class="value">{{ q.delivery_time }}</span>
              </div>
              <div v-if="q.message" class="quote-message">
                <p>{{ q.message }}</p>
              </div>
            </div>

            <!-- 甲方操作：需求已发布/进行中时可选中标 -->
            <div v-if="isOwner && (demand.status === '已发布' || demand.status === '进行中') && !demand.chosen_quote_id" class="quote-actions">
              <button class="btn btn-primary" @click="chooseQuote(q)">
                <i class="fas fa-check"></i> 选为中标
              </button>
            </div>
          </div>
        </div>
        <div v-else class="empty-quotes">
          <p>暂无报价</p>
        </div>
      </div>
    </template>

    <!-- 需求不存在 -->
    <div v-if="!demand && !isEditing" class="empty-state">
      <i class="fas fa-exclamation-triangle"></i>
      <p>需求不存在或已被删除</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api, API_BASE } from '@/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isCreating = computed(() => route.path === '/demands/create')
const demand = ref(null)
const quotes = ref([])
const loading = ref(false)
const submitting = ref(false)
const hasQuoted = ref(false)

// 创建表单（发布新需求）
const createForm = ref({
  title: '',
  category: '',
  budget_min: null,
  budget_max: null,
  deadline: '',
  description: '',
  payment_type: '一次性',
  payment_phases: []
})

// 文件上传相关
const fileInput = ref(null)
const uploadedFileName = ref('')
const uploadedFileUrl = ref('')
const uploadingFile = ref(false)
const uploadSuccess = ref(false)
const tempDemandId = ref(null)

// 计算阶段总比例
const totalPhaseRatio = computed(() => {
  return createForm.value.payment_phases.reduce((sum, p) => sum + (p.ratio || 0), 0)
})

const isFormValid = computed(() => {
  const baseValid = createForm.value.title &&
    createForm.value.category &&
    createForm.value.description
  
  if (createForm.value.payment_type === '分阶段') {
    return baseValid && totalPhaseRatio.value === 100
  }
  
  return baseValid
})

function addPhase() {
  createForm.value.payment_phases.push({ name: '', ratio: 0 })
}

function removePhase(idx) {
  createForm.value.payment_phases.splice(idx, 1)
}

// 文件上传
function triggerFileUpload() {
  fileInput.value?.click()
}

async function handleFileChange(event) {
  const file = event.target.files[0]
  if (!file) return

  uploadingFile.value = true
  uploadedFileName.value = file.name

  try {
    if (!tempDemandId.value) {
      const data = {
        title: createForm.value.title || '未命名需求（待完善）',
        category: createForm.value.category || '',
        budget: createForm.value.budget_min || createForm.value.budget_max || 0,
        budget_min: createForm.value.budget_min,
        budget_max: createForm.value.budget_max,
        deadline: createForm.value.deadline,
        description: createForm.value.description || '请完善需求描述',
        payment_type: createForm.value.payment_type,
        payment_phases: createForm.value.payment_type === '分阶段' && createForm.value.payment_phases.length > 0
          ? JSON.stringify(createForm.value.payment_phases)
          : ''
      }
      const result = await api.post('/api/demands', data)
      tempDemandId.value = result.id
    }

    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/api/demands/${tempDemandId.value}/upload-file`, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + authStore.token
      },
      body: formData
    })

    const result = await response.json()
    if (!response.ok) {
      const errMsg = typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail) || '文件上传失败'
      throw new Error(errMsg)
    }

    uploadedFileUrl.value = result.url
    uploadSuccess.value = true
    authStore.toast('文件上传成功', 'success')
  } catch (e) {
    const msg = e?.message || e?.detail || String(e) || '上传失败'
    authStore.toast(msg, 'error')
    uploadedFileName.value = ''
    uploadSuccess.value = false
  } finally {
    uploadingFile.value = false
  }
}

async function submitDemand() {
  if (!isFormValid.value) {
    const msg = createForm.value.payment_type === '分阶段' 
      ? '请填写必填项，且分阶段付款总比例必须为100%'
      : '请填写必填项'
    authStore.toast(msg, 'error')
    return
  }

  submitting.value = true
  try {
    const data = {
      title: createForm.value.title,
      category: createForm.value.category,
      budget_min: createForm.value.budget_min,
      budget_max: createForm.value.budget_max,
      deadline: createForm.value.deadline,
      description: createForm.value.description,
      payment_type: createForm.value.payment_type,
      payment_phases: createForm.value.payment_type === '分阶段' && createForm.value.payment_phases.length > 0 
        ? JSON.stringify(createForm.value.payment_phases) 
        : ''
    }

    await api.post('/api/demands', data)
    authStore.toast('需求发布成功，等待审核', 'success')
    router.push('/my-demands')
  } catch (e) {
    const msg = e?.message || e?.detail || String(e) || '发布失败'
    authStore.toast(msg, 'error')
  } finally {
    submitting.value = false
  }
}

// 报价表单
const quoteForm = ref({
  price: null,
  remark: ''
})

const isOwner = computed(() => {
  return demand.value && authStore.user && demand.value.owner_id === authStore.user.id
})

async function loadDemand() {
  loading.value = true
  try {
    const id = route.params.id
    const data = await api.get(`/api/demands/${id}`)
    demand.value = data

    if (data.payment_phases && typeof data.payment_phases === 'string') {
      try {
        demand.value.payment_phases = JSON.parse(data.payment_phases)
      } catch {
        demand.value.payment_phases = []
      }
    }

    await loadQuotes()
  } catch (e) {
    authStore.toast('加载需求详情失败', 'error')
  } finally {
    loading.value = false
  }
}

async function loadQuotes() {
  try {
    const id = route.params.id
    const data = await api.get(`/api/demands/${id}/quotes`)
    quotes.value = data.quotes || data || []

    if (authStore.user) {
      hasQuoted.value = quotes.value.some(q => q.seller_id === authStore.user.id)
    }
  } catch (e) {
    console.error('加载报价失败', e)
  }
}

async function submitQuote() {
  if (!quoteForm.value.price) {
    authStore.toast('请输入报价金额', 'error')
    return
  }

  submitting.value = true
  try {
    await api.post(`/api/demands/${route.params.id}/quotes`, quoteForm.value)
    authStore.toast('报价提交成功', 'success')
    quoteForm.value = { price: null, remark: '' }
    await loadQuotes()
  } catch (e) {
    authStore.toast(e.message || '提交报价失败', 'error')
  } finally {
    submitting.value = false
  }
}

async function chooseQuote(quote) {
  if (!confirm(`确定选择 "${quote.seller_name}" 的报价（¥${quote.price}）为中标吗？`)) {
    return
  }

  try {
    await api.post(`/api/demands/${route.params.id}/select-winner/${quote.id}`)
    authStore.toast('已选择中标方', 'success')
    await loadDemand()
  } catch (e) {
    authStore.toast(e.message || '操作失败', 'error')
  }
}

async function closeDemand() {
  if (!confirm('确定关闭此需求吗？关闭后将无法再接收报价。')) {
    return
  }

  try {
    await api.post(`/api/demands/${route.params.id}/close`)
    authStore.toast('需求已关闭', 'success')
    await loadDemand()
  } catch (e) {
    authStore.toast(e.message || '关闭需求失败', 'error')
  }
}

function formatTime(time) {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  if (!isCreating.value) {
    loadDemand()
  }
})
</script>

<style scoped>
.demand-detail-page {
  /* 移除 max-width 限制，让表单铺满内容区 */
}

.btn-success {
  background: #28a745 !important;
  border-color: #28a745 !important;
  color: white !important;
}

.btn-success:hover {
  background: #218838 !important;
  border-color: #218838 !important;
}

.back-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 14px;
  margin-bottom: 20px;
  padding: 8px 0;
}

.back-btn:hover {
  text-decoration: underline;
}

.loading, .empty-state {
  text-align: center;
  padding: 60px;
  color: #999;
}

.demand-info-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.category-tag {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  margin-right: 8px;
}

.status-tag {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.status-tag.待审核 { background: #fff3cd; color: #856404; }
.status-tag.待接单 { background: #cce5ff; color: #004085; }
.status-tag.进行中 { background: #d4edda; color: #155724; }
.status-tag.已完成 { background: #d1e7dd; color: #0f5132; }
.status-tag.已关闭 { background: #e9ecef; color: #666; }

.demand-title {
  font-size: 24px;
  margin: 0 0 20px 0;
  color: #333;
}

.demand-attachments {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  color: #999;
}

.info-item span {
  font-size: 14px;
  color: #333;
}

.description-section {
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.description-section h3 {
  font-size: 16px;
  margin: 0 0 12px 0;
  color: #333;
}

.description-section p {
  margin: 0;
  color: #666;
  line-height: 1.8;
}

.payment-phases-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.payment-phases-section h3 {
  font-size: 16px;
  margin: 0 0 12px 0;
  color: #333;
}

.phases-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.phase-item {
  background: #f5f7fa;
  padding: 10px 16px;
  border-radius: 8px;
  display: flex;
  gap: 12px;
}

.phase-name {
  color: #333;
}

.phase-ratio {
  color: #667eea;
  font-weight: 600;
}

.quotes-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.quotes-section h2 {
  font-size: 18px;
  margin: 0 0 20px 0;
  color: #333;
}

.quote-form {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.quote-form h3 {
  font-size: 16px;
  margin: 0 0 16px 0;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 6px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.form-group textarea {
  height: 100px;
  resize: vertical;
}

.quoted-tip {
  background: #d4edda;
  color: #155724;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 24px;
}

.quoted-tip i {
  margin-right: 8px;
}

.quotes-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quote-card {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s;
}

.quote-card:hover {
  border-color: #667eea;
}

.quote-card.my-quote {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.02);
}

.quote-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.seller-name {
  font-weight: 600;
  color: #333;
}

.real-name {
  color: #28a745;
  font-size: 12px;
}

.chosen-badge {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
}

.chosen-badge i {
  margin-right: 4px;
}

.quote-body {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.quote-price, .quote-delivery {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quote-price .label, .quote-delivery .label {
  font-size: 12px;
  color: #999;
}

.quote-price .value {
  font-size: 20px;
  font-weight: 600;
  color: #667eea;
}

.quote-delivery .value {
  font-size: 14px;
  color: #333;
}

.quote-message {
  width: 100%;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.quote-message p {
  margin: 0;
  color: #666;
  line-height: 1.6;
}

.quote-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.empty-quotes {
  text-align: center;
  padding: 40px;
  color: #999;
}

/* 创建表单样式 */
.create-form-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.create-form-card h1 {
  font-size: 24px;
  margin: 0 0 24px 0;
  color: #333;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.budget-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.budget-inputs input {
  flex: 1;
}

.budget-inputs span {
  color: #666;
}

select {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background: white;
}

.payment-config {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 12px;
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-sm:hover {
  background: #5a6fd6;
}

.phases-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.phase-editor-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.phase-editor-item input:first-child {
  flex: 2;
}

.phase-editor-item input[type="number"] {
  width: 80px;
  flex: none;
}

.phase-editor-item span {
  color: #666;
}

.btn-icon {
  background: #ff4757;
  color: white;
  border: none;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-icon:hover {
  background: #ff3344;
}

.phases-total {
  font-size: 14px;
  color: #666;
  padding-top: 8px;
  border-top: 1px dashed #ddd;
}

.phases-total .error {
  color: #ff4757;
  margin-left: 8px;
}

/* 付款方式选择器 */
.payment-type-selector {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.payment-type-option {
  flex: 1;
  cursor: pointer;
}

.payment-type-option input {
  display: none;
}

.payment-type-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  transition: all 0.3s;
  background: #fafafa;
}

.payment-type-option input:checked + .payment-type-card {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.payment-type-card i {
  font-size: 28px;
  color: #667eea;
  margin-bottom: 8px;
}

.payment-type-card strong {
  font-size: 15px;
  color: #333;
  margin-bottom: 4px;
}

.payment-type-card small {
  font-size: 12px;
  color: #999;
}

.section-sub-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-sub-header label {
  font-weight: 600;
  color: #666;
}

.phases-empty {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #666;
  font-size: 14px;
}

/* 需求详情页付款方式标签 */
.payment-type-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
}

.payment-type-tag.once {
  background: #d4edda;
  color: #155724;
}

.payment-type-tag.stage {
  background: #cce5ff;
  color: #004085;
}

/* 文件上传区域 */
.upload-area {
  border: 2px dashed #ddd;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafafa;
}

.upload-area:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.upload-area i {
  font-size: 36px;
  color: #667eea;
  margin-bottom: 12px;
}

.upload-area p {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 14px;
}

.upload-area small {
  color: #999;
  font-size: 12px;
}

.upload-area.has-file {
  border-color: #28a745;
  background: rgba(40, 167, 69, 0.05);
}

.upload-area.has-file i {
  color: #28a745;
}

.upload-progress {
  margin-top: 12px;
  color: #667eea;
  font-size: 13px;
}

.upload-success {
  margin-top: 12px;
  color: #28a745;
  font-size: 13px;
}

.upload-success i {
  margin-right: 4px;
}

/* 编辑表单样式 */
.edit-form {
  margin-top: 24px;
  border: 2px solid #667eea;
}

.form-actions {
  margin-top: 32px;
  display: flex;
  justify-content: center;
}

.btn-lg {
  padding: 14px 48px;
  font-size: 16px;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .quote-body {
    flex-direction: column;
    gap: 12px;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
