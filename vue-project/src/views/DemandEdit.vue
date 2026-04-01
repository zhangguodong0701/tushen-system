<template>
  <div class="demand-edit-page">
    <!-- 返回按钮 -->
    <button class="back-btn" @click="router.push(`/demands/${route.params.id}`)">
      <i class="fas fa-arrow-left"></i> 返回详情
    </button>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i> 加载中...
    </div>

    <!-- 编辑表单 -->
    <div v-else-if="demand" class="edit-form-card">
      <h1>编辑需求</h1>
      <div class="form-group">
        <label>需求标题 *</label>
        <input v-model="editForm.title" type="text" placeholder="简要描述您的需求" />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>需求分类</label>
          <select v-model="editForm.category">
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
            <input v-model.number="editForm.budget_min" type="number" placeholder="最低" />
            <span>至</span>
            <input v-model.number="editForm.budget_max" type="number" placeholder="最高" />
            <span>元</span>
          </div>
        </div>
      </div>
      <div class="form-group">
        <label>工期要求</label>
        <input v-model="editForm.deadline" type="text" placeholder="预计完成时间，如：7天" />
      </div>
      <div class="form-group">
        <label>需求描述 *</label>
        <textarea v-model="editForm.description" placeholder="详细描述您的需求" rows="6"></textarea>
      </div>

      <!-- 付款方式选择 -->
      <div class="payment-config">
        <div class="section-header">
          <label>付款方式</label>
        </div>
        <div class="payment-type-selector">
          <label class="payment-type-option">
            <input type="radio" v-model="editForm.payment_type" value="一次性" />
            <span class="payment-type-card">
              <i class="fas fa-credit-card"></i>
              <strong>一次性付清</strong>
            </span>
          </label>
          <label class="payment-type-option">
            <input type="radio" v-model="editForm.payment_type" value="分阶段" />
            <span class="payment-type-card">
              <i class="fas fa-tasks"></i>
              <strong>分阶段付款</strong>
            </span>
          </label>
        </div>

        <!-- 分阶段付款配置 -->
        <div v-if="editForm.payment_type === '分阶段'" class="phases-editor">
          <div class="section-sub-header">
            <label>阶段配置</label>
            <button type="button" class="btn btn-sm" @click="addEditPhase">
              <i class="fas fa-plus"></i> 添加阶段
            </button>
          </div>
          <div v-if="editForm.payment_phases.length > 0">
            <div v-for="(phase, idx) in editForm.payment_phases" :key="idx" class="phase-editor-item">
              <input v-model="phase.name" type="text" placeholder="阶段名称" />
              <input v-model.number="phase.ratio" type="number" placeholder="比例" min="1" max="100" />
              <span>%</span>
              <button type="button" class="btn-icon" @click="removeEditPhase(idx)">
                <i class="fas fa-trash"></i>
              </button>
            </div>
            <div class="phases-total">
              总计：{{ editTotalRatio }}%
              <span v-if="editTotalRatio !== 100" class="error">（必须等于100%）</span>
            </div>
          </div>
          <div v-else class="phases-empty">
            <p>请添加付款阶段</p>
          </div>
        </div>
      </div>

      <!-- 图纸上传 -->
      <div class="form-group">
        <label>上传图纸文件</label>
        <div class="upload-area" @click="triggerEditFileUpload" :class="{ 'has-file': editUploadedFileName }">
          <input 
            ref="editFileInput"
            type="file" 
            accept=".dwg,.pdf,.zip,.rvt,.jpg,.jpeg,.png"
            style="display:none"
            @change="handleEditFileChange"
          />
          <template v-if="!editUploadedFileName">
            <i class="fas fa-cloud-upload-alt"></i>
            <p>点击或拖拽上传图纸文件</p>
            <small>支持 DWG, PDF, ZIP, RVT, JPG, PNG 格式</small>
          </template>
          <template v-else>
            <i class="fas fa-file-alt"></i>
            <p>{{ editUploadedFileName }}</p>
            <small>点击更换文件</small>
          </template>
        </div>
        <div v-if="editUploading" class="upload-progress">
          <i class="fas fa-spinner fa-spin"></i> 上传中...
        </div>
        <div v-if="editUploadSuccess" class="upload-success">
          <i class="fas fa-check-circle"></i> 上传成功
        </div>
      </div>

      <div class="form-actions">
        <button class="btn btn-outline" @click="router.push(`/demands/${route.params.id}`)">取消</button>
        <button class="btn btn-primary" @click="saveEdit" :disabled="submitting">
          {{ submitting ? '保存中...' : '保存修改' }}
        </button>
        <button v-if="demand.status === '草稿' || demand.status === '待完善'" class="btn btn-success" @click="publishDemand" :disabled="submitting">
          <i class="fas fa-paper-plane"></i> 发布需求
        </button>
      </div>
    </div>

    <!-- 需求不存在 -->
    <div v-else class="empty-state">
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

const demand = ref(null)
const loading = ref(false)
const submitting = ref(false)

// 编辑表单
const editForm = ref({
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
const editFileInput = ref(null)
const editUploadedFileName = ref('')
const editUploadedFileUrl = ref('')
const editUploading = ref(false)
const editUploadSuccess = ref(false)

// 编辑表单 - 计算总比例
const editTotalRatio = computed(() => {
  return editForm.value.payment_phases.reduce((sum, p) => sum + (p.ratio || 0), 0)
})

// 加载需求数据
async function loadDemand() {
  loading.value = true
  try {
    const id = route.params.id
    const data = await api.get(`/api/demands/${id}`)
    demand.value = data

    // 解析分阶段付款配置
    if (data.payment_phases && typeof data.payment_phases === 'string') {
      try {
        demand.value.payment_phases = JSON.parse(data.payment_phases)
      } catch {
        demand.value.payment_phases = []
      }
    }

    // 初始化编辑表单
    editForm.value = {
      title: data.title || '',
      category: data.profession || '',
      budget_min: data.budget_min || null,
      budget_max: data.budget_max || null,
      deadline: data.deadline || '',
      description: data.description || '',
      payment_type: data.payment_phases?.length > 0 ? '分阶段' : '一次性',
      payment_phases: data.payment_phases?.map(p => ({ ...p })) || []
    }

    // 加载已有图纸
    if (data.file_url) {
      const fileName = data.file_url.split('/').pop() || '已有图纸'
      editUploadedFileName.value = fileName
      editUploadedFileUrl.value = data.file_url
      editUploadSuccess.value = true
    }
  } catch (e) {
    authStore.toast('加载需求详情失败', 'error')
  } finally {
    loading.value = false
  }
}

// 编辑表单文件上传
function triggerEditFileUpload() {
  editFileInput.value?.click()
}

async function handleEditFileChange(event) {
  const file = event.target.files[0]
  if (!file) return

  editUploading.value = true
  editUploadedFileName.value = file.name

  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/api/demands/${route.params.id}/upload-file`, {
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

    editUploadedFileUrl.value = result.url
    editUploadSuccess.value = true
    authStore.toast('文件上传成功', 'success')
  } catch (e) {
    const msg = e?.message || e?.detail || String(e) || '上传失败'
    authStore.toast(msg, 'error')
    editUploadedFileName.value = ''
    editUploadSuccess.value = false
  } finally {
    editUploading.value = false
  }
}

// 添加阶段
function addEditPhase() {
  editForm.value.payment_phases.push({ name: '', ratio: 0 })
}

// 移除阶段
function removeEditPhase(idx) {
  editForm.value.payment_phases.splice(idx, 1)
}

// 保存编辑
async function saveEdit() {
  if (!editForm.value.title || !editForm.value.description) {
    authStore.toast('请填写必填项', 'error')
    return
  }
  if (editForm.value.payment_type === '分阶段') {
    const totalRatio = editForm.value.payment_phases.reduce((sum, p) => sum + (p.ratio || 0), 0)
    if (totalRatio !== 100) {
      authStore.toast('分阶段付款总比例必须为100%', 'error')
      return
    }
  }

  submitting.value = true
  try {
    const data = {
      title: editForm.value.title,
      profession: editForm.value.category,
      budget: editForm.value.budget_min || editForm.value.budget_max || 0,
      budget_min: editForm.value.budget_min,
      budget_max: editForm.value.budget_max,
      deadline: editForm.value.deadline,
      description: editForm.value.description,
      payment_type: editForm.value.payment_type,
      payment_phases: editForm.value.payment_type === '分阶段' && editForm.value.payment_phases.length > 0
        ? JSON.stringify(editForm.value.payment_phases)
        : ''
    }

    await api.put(`/api/demands/${route.params.id}`, data)
    authStore.toast('需求更新成功', 'success')
    // 跳转到详情页
    router.push(`/demands/${route.params.id}`)
  } catch (e) {
    const msg = e?.message || e?.detail || String(e) || '更新失败'
    authStore.toast(msg, 'error')
  } finally {
    submitting.value = false
  }
}

// 保存并发布
async function publishDemand() {
  // 先保存
  await saveEdit()
  // 然后发布
  try {
    await api.post(`/api/demands/${route.params.id}/publish`)
    authStore.toast('需求发布成功', 'success')
    router.push(`/demands/${route.params.id}`)
  } catch (e) {
    const msg = e?.message || e?.detail || String(e) || '发布失败'
    authStore.toast(msg, 'error')
  }
}

onMounted(() => {
  loadDemand()
})
</script>

<style scoped>
.demand-edit-page {
  width: 100%;
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

.edit-form-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.edit-form-card h1 {
  font-size: 24px;
  margin: 0 0 24px 0;
  color: #333;
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

.phases-empty {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #666;
  font-size: 14px;
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

.form-actions {
  margin-top: 32px;
  display: flex;
  justify-content: center;
  gap: 16px;
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

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
