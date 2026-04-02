<template>
  <div class="feedback-page">
    <!-- 提交反馈 -->
    <div class="card">
      <div class="card-header">
        <h3><i class="fas fa-comment-dots"></i> 提交反馈</h3>
      </div>
      <div class="card-body">
        <div class="form-field">
          <label>反馈内容 *</label>
          <textarea
            v-model="feedbackContent"
            placeholder="请详细描述您遇到的问题或建议（至少10字）"
            rows="5"
            style="background: white; min-height: 120px; width: 100%; box-sizing: border-box; border: 2px solid #e2e8f0; border-radius: 8px; padding: 10px 14px; font-size: 14px; resize: vertical;"
          ></textarea>
        </div>
        <button class="btn btn-primary" :disabled="submitting" @click="submitFeedback">
          <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
          <span v-else><i class="fas fa-paper-plane"></i> 提交反馈</span>
        </button>
      </div>
    </div>

    <!-- 我的反馈记录 -->
    <div class="card">
      <div class="card-header">
        <h3><i class="fas fa-history"></i> 我的反馈记录</h3>
      </div>
      <div class="card-body">
        <div v-if="loading" class="loading">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <div v-else-if="feedbacks.length === 0" class="empty-state">
          <i class="fas fa-comment-slash"></i>
          <p>暂无反馈记录</p>
        </div>
        <div v-else class="feedback-list">
          <div v-for="f in feedbacks" :key="f.id" class="feedback-item">
            <div class="feedback-header">
              <span class="feedback-time">{{ formatTime(f.created_at) }}</span>
              <span class="status-badge" :class="f.status">{{ f.status }}</span>
            </div>
            <div class="feedback-content">{{ f.content }}</div>
            <div v-if="f.reply" class="feedback-reply">
              <div class="reply-label"><i class="fas fa-reply"></i> 官方回复：</div>
              <div class="reply-content">{{ f.reply }}</div>
            </div>
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
const feedbackContent = ref('')
const feedbacks = ref([])
const loading = ref(false)
const submitting = ref(false)

async function submitFeedback() {
  if (!feedbackContent.value || feedbackContent.value.length < 10) {
    authStore.toast('反馈内容至少10个字', 'error')
    return
  }

  submitting.value = true
  try {
    await api.post('/api/feedback', { content: feedbackContent.value })
    authStore.toast('反馈提交成功！', 'success')
    feedbackContent.value = ''
    loadFeedbacks()
  } catch (e) {
    authStore.toast(e.message || '提交失败', 'error')
  } finally {
    submitting.value = false
  }
}

async function loadFeedbacks() {
  loading.value = true
  try {
    const data = await api.get('/api/feedback')
    feedbacks.value = data
  } catch (e) {
    authStore.toast('加载反馈记录失败', 'error')
  } finally {
    loading.value = false
  }
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadFeedbacks()
})
</script>

<style scoped>
.feedback-page {
  /* 移除 max-width 限制，让内容铺满 */
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.card {
  background: white;
  border-radius: 12px;
  margin-bottom: 24px;
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

.form-field {
  margin-bottom: 20px;
}

.form-field label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-field textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
}

.form-field textarea:focus {
  outline: none;
  border-color: #667eea;
}

.loading,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty-state i {
  font-size: 40px;
  margin-bottom: 12px;
}

.feedback-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feedback-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.feedback-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.feedback-time {
  font-size: 13px;
  color: #999;
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

.status-badge.已回复 {
  background: #d4edda;
  color: #155724;
}

.feedback-content {
  color: #333;
  line-height: 1.6;
}

.feedback-reply {
  margin-top: 12px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.reply-label {
  font-size: 13px;
  color: #667eea;
  margin-bottom: 6px;
}

.reply-content {
  color: #666;
  font-size: 14px;
}

.form-field textarea {
  background: white !important;
  min-height: 120px !important;
  width: 100%;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
}
</style>
