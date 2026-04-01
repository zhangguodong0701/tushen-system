<template>
  <div class="profile-page">
    <!-- 个人信息头部 -->
    <div class="profile-header">
      <div class="profile-avatar">
        <i class="fas fa-user"></i>
      </div>
      <div class="profile-meta">
        <div class="profile-name-row">
          <h2 class="profile-name">{{ user.real_name || '未填写姓名' }}</h2>
          <span v-if="authStore.isAdmin" class="badge badge-admin">
            <i class="fas fa-shield-alt"></i> 平台管理员
          </span>
          <span v-else-if="authStore.isReviewer" class="badge badge-reviewer">
            <i class="fas fa-user-shield"></i> 平台审核员
          </span>
          <span v-else class="badge" :class="user.role === '甲方' ? 'badge-buyer' : 'badge-seller'">
            <i :class="user.role === '甲方' ? 'fas fa-building' : 'fas fa-briefcase'"></i>
            {{ user.role || '用户' }}
          </span>
        </div>
        <div class="profile-sub">
          <span v-if="user.phone" class="sub-item"><i class="fas fa-phone"></i> {{ user.phone }}</span>
          <span v-if="user.email" class="sub-item"><i class="fas fa-envelope"></i> {{ user.email }}</span>
          <span v-if="user.created_at" class="sub-item"><i class="fas fa-calendar"></i> {{ formatTime(user.created_at) }}</span>
        </div>
        <div class="profile-badges">
          <template v-if="!authStore.isAdmin && !authStore.isReviewer">
            <span v-if="user.status === '通过'" class="verify-badge verify-ok">
              <i class="fas fa-check-circle"></i> 已实名认证
            </span>
            <span v-else-if="user.status === '待审核'" class="verify-badge verify-pending">
              <i class="fas fa-clock"></i> 认证审核中
            </span>
            <span v-else class="verify-badge verify-none">
              <i class="fas fa-times-circle"></i> 未认证
            </span>
          </template>
          <span v-if="!authStore.isAdmin && !authStore.isReviewer && user.user_type" class="type-badge">{{ user.user_type }}</span>
        </div>
      </div>
    </div>

    <!-- 实名认证卡片 -->
    <div v-if="!authStore.isAdmin && !authStore.isReviewer" class="card">
      <div class="card-header">
        <h3><i class="fas fa-id-card"></i> 实名认证</h3>
        <span class="card-tag" :class="authStatusClass">{{ authStatusText }}</span>
      </div>
      <div class="card-body">
        <div v-if="user.auth_type === '个人'" class="cert-grid">
          <div class="cert-item">
            <div class="cert-label"><i class="fas fa-id-card-alt"></i> 身份证正面</div>
            <div v-if="user.id_card_front" class="cert-preview">
              <img :src="getFileUrl(user.id_card_front)" alt="身份证正面" />
            </div>
            <span v-else class="cert-missing">未上传</span>
          </div>
          <div class="cert-item">
            <div class="cert-label"><i class="fas fa-id-card"></i> 身份证背面</div>
            <div v-if="user.id_card_back" class="cert-preview">
              <img :src="getFileUrl(user.id_card_back)" alt="身份证背面" />
            </div>
            <span v-else class="cert-missing">未上传</span>
          </div>
        </div>
        <div v-else-if="user.auth_type === '企业'" class="cert-grid cert-grid-single">
          <div class="cert-item">
            <div class="cert-label"><i class="fas fa-building"></i> 营业执照</div>
            <div v-if="user.business_license" class="cert-preview cert-preview-wide">
              <img :src="getFileUrl(user.business_license)" alt="营业执照" />
            </div>
            <span v-else class="cert-missing">未上传</span>
          </div>
        </div>
        <div v-else class="empty-auth">
          <div class="empty-auth-icon"><i class="fas fa-cloud-upload-alt"></i></div>
          <p>尚未提交认证资料</p>
          <button class="btn btn-primary" @click="showAuthForm = true">
            <i class="fas fa-upload"></i> 提交认证
          </button>
        </div>
      </div>
    </div>

    <!-- 安全设置卡片 -->
    <div class="card">
      <div class="card-header">
        <h3><i class="fas fa-lock"></i> 安全设置</h3>
      </div>
      <div class="card-body">
        <div class="security-item">
          <div class="security-info">
            <i class="fas fa-key"></i>
            <div>
              <div class="security-title">登录密码</div>
              <div class="security-desc">定期更换密码，保障账号安全</div>
            </div>
          </div>
          <button class="btn btn-outline btn-sm" @click="showPasswordForm = true">
            修改
          </button>
        </div>
      </div>
    </div>

    <!-- 认证表单弹窗 -->
    <div v-if="showAuthForm" class="modal-overlay" @click.self="showAuthForm = false">
      <div class="modal">
        <div class="modal-header">
          <h3>实名认证</h3>
          <button class="btn-close" @click="showAuthForm = false">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-field">
            <label>认证类型</label>
            <select v-model="authForm.type">
              <option value="个人">个人认证</option>
              <option value="企业">企业认证</option>
            </select>
          </div>

          <template v-if="authForm.type === '个人'">
            <div class="form-field">
              <label>身份证正面 *</label>
              <div class="upload-area" @click="triggerUpload('front')">
                <i class="fas fa-cloud-upload-alt"></i>
                <p>点击上传身份证正面照片</p>
                <input type="file" ref="frontInput" accept="image/*" @change="handleCertUpload('front', $event)" style="display:none" />
              </div>
              <div v-if="authForm.id_card_front" class="upload-preview">
                <img :src="authForm.id_card_front" alt="预览" />
              </div>
            </div>
            <div class="form-field">
              <label>身份证背面 *</label>
              <div class="upload-area" @click="triggerUpload('back')">
                <i class="fas fa-cloud-upload-alt"></i>
                <p>点击上传身份证背面照片</p>
                <input type="file" ref="backInput" accept="image/*" @change="handleCertUpload('back', $event)" style="display:none" />
              </div>
              <div v-if="authForm.id_card_back" class="upload-preview">
                <img :src="authForm.id_card_back" alt="预览" />
              </div>
            </div>
          </template>

          <template v-else>
            <div class="form-field">
              <label>营业执照 *</label>
              <div class="upload-area" @click="triggerUpload('license')">
                <i class="fas fa-cloud-upload-alt"></i>
                <p>点击上传营业执照照片</p>
                <input type="file" ref="licenseInput" accept="image/*" @change="handleCertUpload('license', $event)" style="display:none" />
              </div>
              <div v-if="authForm.business_license" class="upload-preview">
                <img :src="authForm.business_license" alt="预览" />
              </div>
            </div>
          </template>

          <div class="form-actions">
            <button class="btn btn-outline" @click="showAuthForm = false">取消</button>
            <button class="btn btn-primary" :disabled="submitting" @click="submitAuth">
              <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
              <span v-else>提交认证</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'

const authStore = useAuthStore()

const user = computed(() => authStore.user || {})
const showAuthForm = ref(false)
const showPasswordForm = ref(false)
const submitting = ref(false)

const authForm = ref({
  type: '个人',
  id_card_front: '',
  id_card_back: '',
  business_license: ''
})

const authStatusClass = computed(() => {
  if (user.value.status === '通过') return 'status-pass'
  if (user.value.status === '待审核') return 'status-pending'
  return 'status-none'
})

const authStatusText = computed(() => {
  if (user.value.status === '通过') return '已认证 ✓'
  if (user.value.status === '待审核') return '审核中'
  if (user.value.status === '驳回') return '已驳回'
  return '未认证'
})

function getFileUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${api.baseURL}${path}`
}

function formatTime(time) {
  if (!time) return '-'
  try {
    // 处理空格格式时间 "2026-03-30 10:00:00"
    const normalized = String(time).replace(' ', 'T')
    const date = new Date(normalized)
    if (isNaN(date.getTime())) return String(time)
    return date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return String(time)
  }
}

function triggerUpload(type) {
  const refs = { front: 'frontInput', back: 'backInput', license: 'licenseInput' }
  document.querySelector(`[ref="${refs[type]}"]`)?.click()
}

async function handleCertUpload(type, event) {
  const file = event.target.files[0]
  if (!file) return

  try {
    const formData = new FormData()
    const fieldMap = {
      front: 'id_card_front',
      back: 'id_card_back',
      license: 'business_license'
    }
    formData.append('file', file)
    formData.append('type', fieldMap[type])

    const data = await api.postForm('/api/auth/upload-cert', formData)
    authForm.value[fieldMap[type]] = data.url

    // 预览
    const reader = new FileReader()
    reader.onload = (e) => {
      authForm.value[fieldMap[type]] = e.target.result
    }
    reader.readAsDataURL(file)
  } catch (e) {
    authStore.toast('上传失败', 'error')
  }
}

async function submitAuth() {
  submitting.value = true
  try {
    await api.post('/api/auth/certification', authForm.value)
    authStore.toast('认证资料已提交，等待审核', 'success')
    showAuthForm.value = false
    authStore.fetchCurrentUser()
  } catch (e) {
    authStore.toast(e.message || '提交失败', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  authStore.fetchCurrentUser()
})
</script>

<style scoped>
.profile-page {
  max-width: 800px;
}

.profile-header {
  display: flex;
  align-items: flex-start;
  gap: 24px;
  background: white;
  border-radius: 12px;
  padding: 28px 28px 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.profile-avatar {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 32px;
  flex-shrink: 0;
}

.profile-meta {
  flex: 1;
  min-width: 0;
}

.profile-name-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.profile-name {
  margin: 0;
  font-size: 22px;
  color: #1a1a2e;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.badge i { font-size: 11px; }

.badge-admin {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.badge-reviewer {
  background: rgba(102, 126, 234, 0.12);
  color: #667eea;
}

.badge-buyer {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.badge-seller {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.profile-sub {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
}

.sub-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sub-item i { color: #999; width: 14px; }

.profile-badges {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.verify-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.verify-ok {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.verify-pending {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.verify-none {
  background: rgba(156, 163, 175, 0.1);
  color: #9ca3af;
}

.type-badge {
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  background: #f3f4f6;
  color: #6b7280;
}

.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 16px;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header h3 i { color: #667eea; }

.card-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.card-body { padding: 20px; }

.cert-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.cert-grid-single { grid-template-columns: 1fr; }

.cert-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.cert-preview {
  width: 100%;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #eee;
}

.cert-preview-wide { height: 160px; }

.cert-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cert-missing {
  display: block;
  width: 100%;
  height: 80px;
  line-height: 80px;
  text-align: center;
  color: #c0c0c0;
  border: 1px dashed #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
}

.empty-auth {
  text-align: center;
  padding: 28px;
  color: #999;
}

.empty-auth-icon {
  font-size: 40px;
  margin-bottom: 10px;
  color: #d0d0d0;
}

.empty-auth p { margin: 0 0 16px; }

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.security-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.security-info > i {
  width: 40px;
  height: 40px;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.security-title { font-weight: 500; color: #333; }

.security-desc { font-size: 13px; color: #999; margin-top: 2px; }

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
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

.modal-header h3 { margin: 0; }

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  font-size: 18px;
}

.modal-body { padding: 24px; }

.form-field { margin-bottom: 20px; }

.form-field label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-field select,
.upload-area {
  width: 100%;
  padding: 12px;
  border: 1px dashed #ddd;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.02);
}

.upload-area i {
  font-size: 32px;
  color: #999;
  margin-bottom: 8px;
}

.upload-area p { margin: 0; color: #666; }

.upload-preview {
  margin-top: 12px;
  width: 150px;
  height: 100px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #eee;
}

.upload-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}
</style>
