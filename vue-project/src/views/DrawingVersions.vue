<template>
  <div class="versions-page">
    <div class="page-header">
      <button class="btn btn-back" @click="router.push('/drawings')">
        <i class="fas fa-arrow-left"></i> 返回图纸列表
      </button>
      <h2>版本历史</h2>
    </div>

    <!-- 版本概览 -->
    <div v-if="versionInfo" class="version-info-card">
      <div class="info-header">
        <i class="fas fa-file-alt file-icon"></i>
        <div class="info-text">
          <h3>{{ versionInfo.filename }}</h3>
          <p class="subtitle">{{ versionInfo.order_title }}</p>
        </div>
      </div>
      <div class="info-stats">
        <div class="stat">
          <span class="stat-value">{{ versionInfo.versions.length }}</span>
          <span class="stat-label">版本总数</span>
        </div>
        <div class="stat">
          <span class="stat-value">{{ versionInfo.versions[0]?.version || '-' }}</span>
          <span class="stat-label">当前版本</span>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i> 加载中...
    </div>

    <!-- 版本列表 -->
    <div v-else-if="versionInfo && versionInfo.versions.length > 0" class="versions-timeline">
      <div v-for="(v, index) in versionInfo.versions" :key="v.id" class="version-item" :class="{ 'is-latest': index === 0 }">
        <div class="timeline-connector">
          <div class="timeline-dot" :class="{ 'latest': index === 0 }"></div>
          <div v-if="index < versionInfo.versions.length - 1" class="timeline-line"></div>
        </div>
        <div class="version-content">
          <div class="version-header">
            <div class="version-badge-large">
              <span class="version-num">{{ v.version }}</span>
              <span v-if="index === 0" class="latest-tag">最新</span>
            </div>
            <div class="version-meta">
              <span class="uploader">
                <i class="fas fa-user"></i> {{ v.uploader_name || '未知' }}
              </span>
              <span class="date">
                <i class="fas fa-clock"></i> {{ formatTime(v.created_at) }}
              </span>
            </div>
          </div>

          <div class="version-body">
            <!-- 状态标签 -->
            <div class="status-indicator">
              <span v-if="v.comments" class="status-tag has-comments">
                <i class="fas fa-comment"></i> 有修改意见
              </span>
              <span v-else class="status-tag ok">
                <i class="fas fa-check"></i> 审核通过
              </span>
            </div>

            <!-- 操作按钮 -->
            <div class="version-actions">
              <button class="btn btn-sm btn-outline" @click="downloadVersion(v)" title="下载">
                <i class="fas fa-download"></i> 下载
              </button>
              <button v-if="v.comments" class="btn btn-sm btn-outline" @click="viewComments(v)" title="查看意见">
                <i class="fas fa-eye"></i> 意见
              </button>
            </div>
          </div>

          <!-- 意见预览 -->
          <div v-if="v.comments && selectedVersion?.id !== v.id" class="comments-preview" @click="viewComments(v)">
            <i class="fas fa-quote-left"></i>
            {{ v.comments.substring(0, 100) }}{{ v.comments.length > 100 ? '...' : '' }}
            <span class="expand-hint">点击查看全部</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="versionInfo" class="empty-state">
      <i class="fas fa-history"></i>
      <p>暂无版本历史</p>
    </div>

    <!-- 意见详情模态框 -->
    <div v-if="showCommentsModal" class="modal-overlay" @click.self="showCommentsModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ selectedVersion?.version }} 版本详情</h3>
          <button class="close-btn" @click="showCommentsModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="comment-section">
            <h4><i class="fas fa-comment-dots"></i> 修改意见</h4>
            <div v-if="selectedVersion?.comments" class="comment-text">
              {{ selectedVersion.comments }}
            </div>
            <div v-else class="no-comment">
              <i class="fas fa-check-circle"></i> 暂无修改意见
            </div>
          </div>

          <div v-if="selectedVersion?.comment_images" class="images-section">
            <h4><i class="fas fa-images"></i> 意见图片</h4>
            <div class="comment-images">
              <img v-for="(img, idx) in parseImages(selectedVersion.comment_images)"
                   :key="idx"
                   :src="getImageUrl(img)"
                   @click="previewImage(img)"
                   class="comment-img" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片预览 -->
    <div v-if="previewUrl" class="modal-overlay" @click="previewUrl = null">
      <img :src="previewUrl" class="preview-image" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api, API_BASE } from '@/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const drawingId = ref(route.params.id)
const versionInfo = ref(null)
const loading = ref(false)
const showCommentsModal = ref(false)
const selectedVersion = ref(null)
const previewUrl = ref(null)

async function loadVersions() {
  loading.value = true
  try {
    versionInfo.value = await api.get(`/api/drawings/${drawingId.value}/versions`)
  } catch (e) {
    authStore.toast('加载版本历史失败', 'error')
    console.error(e)
  } finally {
    loading.value = false
  }
}

function downloadVersion(v) {
  window.open(`${API_BASE}${v.file_url}`, '_blank')
}

function viewComments(v) {
  selectedVersion.value = v
  showCommentsModal.value = true
}

function previewImage(img) {
  previewUrl.value = getImageUrl(img)
}

function getImageUrl(path) {
  return `${API_BASE}${path}`
}

function parseImages(images) {
  if (!images) return []
  try {
    return JSON.parse(images)
  } catch {
    return images.split(',').filter(Boolean)
  }
}

function formatTime(time) {
  if (!time) return '-'
  const d = new Date(time)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadVersions()
})
</script>

<style scoped>
.versions-page {
  width: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.btn-back {
  padding: 8px 16px;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #e9ecef;
}

.btn-back i {
  margin-right: 6px;
}

/* 版本信息卡片 */
.version-info-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 24px;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.info-header .file-icon {
  font-size: 32px;
  opacity: 0.9;
}

.info-text h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
}

.subtitle {
  margin: 0;
  opacity: 0.85;
  font-size: 14px;
}

.info-stats {
  display: flex;
  gap: 32px;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

/* 加载状态 */
.loading {
  text-align: center;
  padding: 60px;
  color: #999;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px;
  color: #999;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
}

/* 版本时间线 */
.versions-timeline {
  display: flex;
  flex-direction: column;
}

.version-item {
  display: flex;
  gap: 16px;
  padding-bottom: 24px;
}

.version-item.is-latest .version-content {
  background: #fff;
  border-color: #667eea;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.15);
}

.timeline-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
}

.timeline-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #ddd;
  border: 3px solid #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  flex-shrink: 0;
  z-index: 1;
}

.timeline-dot.latest {
  background: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.timeline-line {
  width: 2px;
  flex: 1;
  background: #e0e0e0;
  margin-top: 4px;
}

.version-content {
  flex: 1;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 16px 20px;
  transition: all 0.2s;
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.version-badge-large {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-num {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
}

.latest-tag {
  background: #28a745;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.version-meta {
  display: flex;
  gap: 16px;
  color: #666;
  font-size: 13px;
}

.version-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.version-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.has-comments {
  background: #fff3cd;
  color: #856404;
}

.status-tag.ok {
  background: #d4edda;
  color: #155724;
}

.version-actions {
  display: flex;
  gap: 8px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-outline {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-outline:hover {
  background: #f8f9fa;
  border-color: #667eea;
  color: #667eea;
}

.comments-preview {
  background: #f8f9fa;
  padding: 12px 16px;
  border-radius: 8px;
  color: #666;
  font-size: 13px;
  line-height: 1.5;
  cursor: pointer;
  transition: background 0.2s;
}

.comments-preview:hover {
  background: #e9ecef;
}

.comments-preview i {
  color: #999;
  margin-right: 8px;
}

.expand-hint {
  color: #667eea;
  margin-left: 8px;
  font-size: 12px;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.comment-section h4,
.images-section h4 {
  color: #333;
  margin-bottom: 12px;
  font-size: 14px;
}

.comment-section h4 i,
.images-section h4 i {
  margin-right: 6px;
  color: #667eea;
}

.comment-text {
  background: #fff3cd;
  padding: 16px;
  border-radius: 8px;
  color: #856404;
  line-height: 1.6;
  white-space: pre-wrap;
}

.no-comment {
  text-align: center;
  padding: 20px;
  color: #28a745;
}

.no-comment i {
  display: block;
  font-size: 24px;
  margin-bottom: 8px;
}

.images-section {
  margin-top: 20px;
}

.comment-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.comment-img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.comment-img:hover {
  transform: scale(1.05);
}

.preview-image {
  max-width: 90%;
  max-height: 90vh;
  object-fit: contain;
}
</style>
