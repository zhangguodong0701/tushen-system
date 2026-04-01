<template>
  <div class="profile-page">
    <div class="page-header">
      <h2>个人中心</h2>
    </div>

    <div class="profile-grid">
      <!-- 左侧主区域 -->
      <div class="main-column">
        <!-- 基本信息 -->
        <div class="card">
          <div class="card-header">
            <h3><i class="fas fa-user"></i> 基本信息</h3>
          </div>
          <div class="card-body">
            <div class="avatar-section">
              <div class="avatar-large">
                <i class="fas fa-user"></i>
              </div>
              <div class="user-info">
                <h4>{{ user.real_name }}</h4>
                <span class="role-tag" :class="user.role === '甲方' ? 'buyer' : 'seller'">
                  {{ user.role }}
                </span>
                <span v-if="user.user_type" class="user-type">{{ user.user_type }}</span>
              </div>
            </div>

            <div class="info-list">
              <div class="info-item">
                <label><i class="fas fa-phone"></i> 手机号</label>
                <span>{{ user.phone || '-' }}</span>
              </div>
              <div class="info-item">
                <label><i class="fas fa-envelope"></i> 邮箱</label>
                <span>{{ user.email || '-' }}</span>
              </div>
              <div class="info-item">
                <label><i class="fas fa-calendar"></i> 注册时间</label>
                <span>{{ formatTime(user.created_at) }}</span>
              </div>
              <div class="info-item">
                <label><i class="fas fa-shield-alt"></i> 实名认证</label>
                <span :class="authStatusClass">
                  {{ authStatusText }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧辅助区域 -->
      <div class="side-column">
        <!-- 认证信息 -->
        <div class="card">
          <div class="card-header">
            <h3><i class="fas fa-certificate"></i> 认证信息</h3>
          </div>
          <div class="card-body">
            <div v-if="user.auth_type === '个人'" class="auth-info">
              <div class="auth-item">
                <label>身份证正面</label>
                <div v-if="user.id_card_front" class="cert-preview">
                  <img :src="getFileUrl(user.id_card_front)" alt="身份证正面" />
                </div>
                <span v-else class="no-cert">未上传</span>
              </div>
              <div class="auth-item">
                <label>身份证背面</label>
                <div v-if="user.id_card_back" class="cert-preview">
                  <img :src="getFileUrl(user.id_card_back)" alt="身份证背面" />
                </div>
                <span v-else class="no-cert">未上传</span>
              </div>
            </div>
            <div v-else-if="user.auth_type === '企业'" class="auth-info">
              <div class="auth-item">
                <label>营业执照</label>
                <div v-if="user.business_license" class="cert-preview">
                  <img :src="getFileUrl(user.business_license)" alt="营业执照" />
                </div>
                <span v-else class="no-cert">未上传</span>
              </div>
            </div>
          <div v-else class="empty-auth">
            <i class="fas fa-id-card"></i>
            <p>尚未提交认证资料</p>
            <button class="btn btn-primary" @click="showAuthForm = true">
              <i class="fas fa-upload"></i> 提交认证
            </button>
          </div>
        </div>
        </div>

        <!-- 安全设置 -->
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
  return new Date(time).toLocaleString('zh-CN')
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
  max-width: 1000px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.profile-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 20px;
  align-items: start;
}

.main-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.side-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header h3 i {
  color: #667eea;
}

.card-body {
  padding: 20px;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #eee;
}

.avatar-large {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 32px;
}

.user-info h4 {
  margin: 0 0 8px 0;
  font-size: 20px;
}

.role-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  margin-right: 8px;
}

.role-tag.buyer {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.role-tag.seller {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.user-type {
  color: #999;
  font-size: 13px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.info-item label i {
  width: 16px;
  color: #999;
}

.status-pass {
  color: #10b981;
}

.status-pending {
  color: #f59e0b;
}

.status-none {
  color: #999;
}

.cert-preview {
  width: 100px;
  height: 70px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #eee;
}

.cert-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-cert {
  color: #999;
  font-size: 13px;
}

.empty-auth {
  text-align: center;
  padding: 32px;
  color: #999;
}

.empty-auth i {
  font-size: 40px;
  margin-bottom: 12px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
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
}

.security-title {
  font-weight: 500;
  color: #333;
}

.security-desc {
  font-size: 13px;
  color: #999;
  margin-top: 2px;
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

.form-field {
  margin-bottom: 20px;
}

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

.upload-area p {
  margin: 0;
  color: #666;
}

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
