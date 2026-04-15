<template>
  <div class="login-page">
    <div class="login-left">
      <div class="brand">
        <div class="brand-icon">
          <i class="fas fa-drafting-compass"></i>
        </div>
        <div class="brand-text">
          <h1>图审云平台</h1>
          <p>专业的图纸审查服务交易平台</p>
        </div>
      </div>
      <div class="features">
        <div class="feature-item">
          <i class="fas fa-shield-alt"></i>
          <span>资金托管保障</span>
        </div>
        <div class="feature-item">
          <i class="fas fa-handshake"></i>
          <span>分阶段付款</span>
        </div>
        <div class="feature-item">
          <i class="fas fa-certificate"></i>
          <span>实名认证审核</span>
        </div>
        <div class="feature-item">
          <i class="fas fa-gavel"></i>
          <span>纠纷快速处理</span>
        </div>
      </div>
    </div>

    <div class="login-right">
      <div class="login-card">
        <div class="login-tabs">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'login' }"
            @click="activeTab = 'login'"
          >
            登录
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'register' }"
            @click="activeTab = 'register'"
          >
            注册
          </button>
        </div>

        <!-- 登录表单 -->
        <form v-if="activeTab === 'login'" @submit.prevent="handleLogin">
          <div class="form-field">
            <label>账号</label>
            <div class="input-wrapper">
              <i class="fas fa-user"></i>
              <input
                type="text"
                id="login-account"
                v-model="loginForm.account"
                placeholder="手机号/邮箱"
                list="login-history"
                @focus="showHistoryDropdown = true"
                @blur="handleAccountBlur"
              />
              <button
                type="button"
                class="history-toggle"
                @click.stop="toggleHistoryDropdown"
              >
                <i class="fas fa-chevron-down"></i>
              </button>
            </div>
            <!-- 历史账号下拉 -->
            <div
              v-if="showHistoryDropdown && loginHistory.length > 0"
              class="history-dropdown"
            >
              <div
                v-for="item in loginHistory"
                :key="item.account"
                class="history-item"
                @mousedown.prevent="selectHistory(item)"
              >
                <span>{{ item.account }}</span>
                <span class="history-pwd">{{ item.password ? '••••' : '' }}</span>
              </div>
            </div>
          </div>

          <div class="form-field">
            <label>密码</label>
            <div class="input-wrapper">
              <i class="fas fa-lock"></i>
              <input
                type="password"
                id="login-password"
                v-model="loginForm.password"
                placeholder="请输入密码"
              />
            </div>
          </div>

          <div class="form-row">
            <label class="checkbox-label">
              <input
                type="checkbox"
                id="remember-me"
                v-model="loginForm.rememberMe"
              />
              <span>记住账号密码</span>
            </label>
          </div>

          <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
            <i v-if="loading" class="fas fa-spinner fa-spin"></i>
            <span v-else>登 录</span>
          </button>
        </form>

        <!-- 注册表单 -->
        <form v-else @submit.prevent="handleRegister">
          <!-- 甲乙方角色选择 -->
          <div class="form-field">
            <label>角色选择 *</label>
            <div class="role-cards">
              <div
                class="role-card"
                :class="{ selected: registerForm.role === '甲方' }"
                @click="selectRole('甲方')"
              >
                <i class="fas fa-building"></i>
                <span>甲方</span>
                <small>发布需求/采购服务</small>
              </div>
              <div
                class="role-card"
                :class="{ selected: registerForm.role === '乙方' }"
                @click="selectRole('乙方')"
              >
                <i class="fas fa-drafting-compass"></i>
                <span>乙方</span>
                <small>承接项目/提供服务</small>
              </div>
            </div>
          </div>

          <!-- 用户类型选择 -->
          <div class="form-field" v-if="registerForm.role">
            <label>用户类型 *</label>
            <select v-model="registerForm.userType" id="reg-type">
              <option value="">请选择具体类型</option>
              <option
                v-for="type in currentTypeOptions"
                :key="type"
                :value="type"
              >
                {{ type }}
              </option>
            </select>
          </div>

          <div class="form-field">
            <label>手机号 *</label>
            <div class="input-wrapper">
              <i class="fas fa-mobile-alt"></i>
              <input
                type="tel"
                id="reg-phone"
                v-model="registerForm.phone"
                placeholder="请输入手机号"
                maxlength="11"
              />
            </div>
          </div>

          <div class="form-field">
            <label>邮箱（选填）</label>
            <div class="input-wrapper">
              <i class="fas fa-envelope"></i>
              <input
                type="email"
                id="reg-email"
                v-model="registerForm.email"
                placeholder="用于接收通知"
              />
            </div>
          </div>

          <div class="form-field">
            <label>姓名/名称 *</label>
            <div class="input-wrapper">
              <i class="fas fa-id-card"></i>
              <input
                type="text"
                id="reg-name"
                v-model="registerForm.name"
                placeholder="个人填写真名，企业填写公司全称"
              />
            </div>
          </div>

          <div class="form-field">
            <label>设置密码 *</label>
            <div class="input-wrapper">
              <i class="fas fa-lock"></i>
              <input
                type="password"
                v-model="registerForm.password"
                placeholder="至少6位"
                minlength="6"
              />
            </div>
          </div>

          <div class="form-field">
            <label>确认密码 *</label>
            <div class="input-wrapper">
              <i class="fas fa-lock"></i>
              <input
                type="password"
                v-model="registerForm.confirmPassword"
                placeholder="再次输入密码"
              />
            </div>
          </div>

          <button
            type="submit"
            class="btn btn-primary btn-block"
            :disabled="loading"
          >
            <i v-if="loading" class="fas fa-spinner fa-spin"></i>
            <span v-else>注 册</span>
          </button>
        </form>
      </div>
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

const activeTab = ref('login')
const loading = ref(false)
const showHistoryDropdown = ref(false)

const loginForm = ref({
  account: '',
  password: '',
  rememberMe: false
})

const registerForm = ref({
  role: '',
  userType: '',
  phone: '',
  email: '',
  name: '',
  password: '',
  confirmPassword: ''
})

// 登录历史
const loginHistory = ref([])

// 用户类型选项
const typeOptions = {
  甲方: ['业主', '建设单位', '项目方'],
  乙方: ['设计院', '设计师', '材料商', '设备商']
}

const currentTypeOptions = computed(() => {
  return registerForm.value.role ? typeOptions[registerForm.value.role] || [] : []
})

// 加载登录历史
onMounted(() => {
  try {
    const history = localStorage.getItem('tushen_login_history')
    loginHistory.value = history ? JSON.parse(history) : []
  } catch (e) {
    loginHistory.value = []
  }
})

// 选择角色
function selectRole(role) {
  registerForm.value.role = role
  registerForm.value.userType = ''
}

// 选择历史账号
function selectHistory(item) {
  loginForm.value.account = item.account
  loginForm.value.password = item.password
  loginForm.value.rememberMe = true
  showHistoryDropdown.value = false
}

// 切换历史下拉
function toggleHistoryDropdown() {
  showHistoryDropdown.value = !showHistoryDropdown.value
  if (showHistoryDropdown.value && loginHistory.value.length === 0) {
    showHistoryDropdown.value = false
  }
}

// 账号输入框失焦处理
function handleAccountBlur() {
  setTimeout(() => {
    showHistoryDropdown.value = false
  }, 200)
}

// 保存登录历史
function saveLoginHistory(account, password) {
  try {
    let history = JSON.parse(localStorage.getItem('tushen_login_history') || '[]')
    history = history.filter(item => item.account !== account)
    history.unshift({ account, password, time: Date.now() })
    if (history.length > 10) history = history.slice(0, 10)
    localStorage.setItem('tushen_login_history', JSON.stringify(history))
    loginHistory.value = history
  } catch (e) {
    // 保存登录历史失败不影响登录，静默忽略
  }
}

// 登录处理
async function handleLogin() {
  const { account, password, rememberMe } = loginForm.value
  if (!account || !password) {
    authStore.toast('请填写账号和密码', 'error')
    return
  }

  loading.value = true
  try {
    const fd = new FormData()
    fd.append('username', account)
    fd.append('password', password)

    const response = await fetch(`${api.baseURL}/api/auth/login`, {
      method: 'POST',
      body: fd
    })
    const data = await response.json()

    if (!response.ok) {
      authStore.toast(data.detail || '登录失败', 'error')
      return
    }

    // 保存 token
    authStore.setToken(data.access_token)  // 同时更新 store

    // 保存登录历史
    if (rememberMe) {
      saveLoginHistory(account, password)
    }

    // 设置用户信息
    authStore.setUser(data.user)
    authStore.toast('登录成功，欢迎回来！', 'success')

    // 跳转到首页
    router.push('/')
  } catch (e) {
    authStore.toast('服务器连接失败，请确认后端已启动', 'error')
  } finally {
    loading.value = false
  }
}

// 注册处理
async function handleRegister() {
  const { role, userType, phone, email, name, password, confirmPassword } = registerForm.value

  if (!role) {
    authStore.toast('请选择角色（甲方/乙方）', 'error')
    return
  }
  if (!userType) {
    authStore.toast('请选择用户类型', 'error')
    return
  }
  if (!phone) {
    authStore.toast('请填写手机号', 'error')
    return
  }
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    authStore.toast('手机号格式不正确', 'error')
    return
  }
  if (!name) {
    authStore.toast('请填写姓名/名称', 'error')
    return
  }
  if (!password || password.length < 6) {
    authStore.toast('密码至少6位', 'error')
    return
  }
  if (password !== confirmPassword) {
    authStore.toast('两次密码输入不一致', 'error')
    return
  }

  loading.value = true
  try {
    const response = await fetch(`${api.baseURL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone,
        email,
        real_name: name,
        password,
        role,
        user_type: userType
      })
    })
    const data = await response.json()

    if (!response.ok) {
      authStore.toast(data.detail || '注册失败', 'error')
      return
    }

    authStore.toast('注册成功，请登录！', 'success')
    // 切换到登录页并填充账号
    activeTab.value = 'login'
    loginForm.value.account = phone
  } catch (e) {
    authStore.toast('服务器连接失败', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 1;
}

@media (max-width: 900px) {
  .login-left {
    display: none;
  }
  .login-right {
    width: 100%;
    max-width: 100%;
  }
}

.login-left {
  flex: 1;
  max-width: 50%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 48px;
  color: white;
  position: relative;
  z-index: 1;
  min-height: 100vh;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 48px;
}

.brand-icon {
  width: 64px;
  height: 64px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
}

.brand-text h1 {
  font-size: 32px;
  margin: 0 0 6px 0;
  font-weight: 600;
}

.brand-text p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-size: 15px;
}

.feature-item i {
  font-size: 18px;
  width: 20px;
}

.login-right {
  flex: 1;
  max-width: 50%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  position: relative;
  z-index: 1;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: white;
  border-radius: 20px;
  padding: 36px 32px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.login-tabs {
  display: flex;
  margin-bottom: 24px;
  background: #f0f2f5;
  border-radius: 10px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  background: none;
  font-size: 15px;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
  border-radius: 8px;
}

.tab-btn.active {
  color: #667eea;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tab-btn:not(.active):hover {
  color: #333;
}

.form-field {
  margin-bottom: 16px;
  position: relative;
}

.form-field label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrapper i {
  position: absolute;
  left: 12px;
  color: #999;
  font-size: 14px;
}

.input-wrapper input,
.form-field select {
  width: 100%;
  padding: 12px 14px 12px 40px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.3s ease;
  box-sizing: border-box;
  background: #fafbfc;
}

.form-field select {
  padding-left: 14px;
}

.input-wrapper input:hover,
.form-field select:hover {
  border-color: #b0b0b0;
}

.input-wrapper input:focus,
.form-field select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
  background: white;
}

.history-toggle {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 4px 8px;
}

.history-toggle:hover {
  color: #667eea;
}

.history-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-top: 4px;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item:hover {
  background: #f5f7fa;
}

.history-pwd {
  font-size: 12px;
  color: #999;
}

.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
}

.checkbox-label input {
  width: 16px;
  height: 16px;
}

.role-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.role-card {
  padding: 14px;
  border: 2px solid #ddd;
  border-radius: 10px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.role-card:hover {
  border-color: #667eea;
}

.role-card.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.role-card i {
  font-size: 24px;
  color: #667eea;
  margin-bottom: 6px;
}

.role-card span {
  display: block;
  font-weight: 600;
  color: #333;
}

.role-card small {
  display: block;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.btn-block {
  width: 100%;
  padding: 12px;
  font-size: 15px;
}
</style>
