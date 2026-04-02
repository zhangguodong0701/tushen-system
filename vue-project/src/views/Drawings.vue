<template>
  <div class="drawings-page">
    <!-- 统计卡片区域 -->
    <div class="stats-bar" v-if="!loading && drawings.length > 0">
      <div class="stat-card">
        <div class="stat-icon blue">
          <i class="fas fa-file-code"></i>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ drawings.length }}</span>
          <span class="stat-label">图纸总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple">
          <i class="fas fa-folder-open"></i>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ Object.keys(groupedDrawings).length }}</span>
          <span class="stat-label">涉及项目</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon orange">
          <i class="fas fa-exclamation-circle"></i>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ drawingsWithComments }}</span>
          <span class="stat-label">待修改</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">
          <i class="fas fa-check-circle"></i>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ drawings.length - drawingsWithComments }}</span>
          <span class="stat-label">待审核</span>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar" v-if="!loading && drawings.length > 0">
      <div class="search-box">
        <i class="fas fa-search"></i>
        <input type="text" v-model="searchKeyword" placeholder="搜索图纸名称..." />
      </div>
      <div class="filter-tabs">
        <button 
          :class="['filter-tab', { active: filterStatus === 'all' }]" 
          @click="filterStatus = 'all'"
        >
          全部
        </button>
        <button 
          :class="['filter-tab', { active: filterStatus === 'pending' }]" 
          @click="filterStatus = 'pending'"
        >
          <i class="fas fa-clock"></i> 待审核
        </button>
        <button 
          :class="['filter-tab', { active: filterStatus === 'comments' }]" 
          @click="filterStatus = 'comments'"
        >
          <i class="fas fa-comment"></i> 有意见
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    
    <!-- 空状态 -->
    <div v-else-if="filteredDrawings.length === 0" class="empty-state">
      <div class="empty-icon">
        <i class="fas fa-drafting-compass"></i>
      </div>
      <h3>暂无图纸记录</h3>
      <p>您还没有上传任何图纸文件</p>
      <button v-if="authStore.isBuyer" class="btn btn-primary" @click="router.push('/demands')">
        去发布需求
      </button>
    </div>

    <!-- 按项目分组展示 -->
    <div v-else class="projects-container">
      <div v-for="(drawings, orderId) in filteredGroupedDrawings" :key="orderId" class="project-group">
        <!-- 项目卡片头部 -->
        <div class="project-header" @click="toggleProject(orderId)">
          <div class="project-left">
            <div class="folder-icon" :class="{ closed: !expandedProjects[orderId] }">
              <i :class="expandedProjects[orderId] ? 'fas fa-folder-open' : 'fas fa-folder'"></i>
            </div>
            <div class="project-meta">
              <h3 class="project-name">{{ drawings[0].order_title || `订单 #${orderId}` }}</h3>
              <span class="project-stats">
                <span class="stat-item">
                  <i class="fas fa-file-alt"></i>
                  {{ drawings.length }} 个文件
                </span>
                <span class="stat-item" v-if="getCommentsCount(drawings) > 0">
                  <i class="fas fa-comment-alt"></i>
                  {{ getCommentsCount(drawings) }} 待修改
                </span>
              </span>
            </div>
          </div>
          <div class="project-right">
            <div class="expand-btn">
              <i class="fas fa-chevron-down" :class="{ rotated: expandedProjects[orderId] }"></i>
            </div>
          </div>
        </div>
        
        <!-- 图纸列表 -->
        <div class="project-body" v-show="expandedProjects[orderId]">
          <div class="drawings-grid">
            <div 
              v-for="d in drawings" 
              :key="d.id" 
              class="drawing-card"
              @click="viewDrawingDetail(d)"
            >
              <!-- 文件类型图标/预览 -->
              <div class="drawing-preview">
                <div class="file-icon-large">
                  <i class="fas fa-file-pdf"></i>
                </div>
                <div class="preview-overlay">
                  <i class="fas fa-eye"></i>
                </div>
              </div>
              
              <!-- 文件信息 -->
              <div class="drawing-info">
                <h4 class="drawing-name" :title="d.name">{{ d.name }}</h4>
                <div class="drawing-meta">
                  <span class="version-tag">V{{ d.version || 1 }}</span>
                  <span class="uploader">{{ d.uploader_name || '未知' }}</span>
                </div>
              </div>
              
              <!-- 状态标签 -->
              <div class="drawing-status">
                <span v-if="d.comments" class="status-badge warning">
                  <i class="fas fa-comment-alt"></i> 待修改
                </span>
                <span v-else class="status-badge success">
                  <i class="fas fa-check"></i> 待审核
                </span>
              </div>
              
              <!-- 操作按钮 -->
              <div class="drawing-actions" @click.stop>
                <button class="action-btn" @click="downloadDrawing(d)" title="下载">
                  <i class="fas fa-download"></i>
                </button>
                <button class="action-btn" @click="viewVersions(d)" title="版本历史">
                  <i class="fas fa-history"></i>
                </button>
                <button v-if="d.comments" class="action-btn primary" @click="viewComments(d)" title="查看意见">
                  <i class="fas fa-comment-dots"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 意见查看模态框 -->
    <Teleport to="body">
      <div v-if="showCommentsModal" class="modal-overlay" @click.self="showCommentsModal = false">
        <div class="comments-modal">
          <div class="modal-header-gradient">
            <div class="modal-title-section">
              <div class="modal-icon">
                <i class="fas fa-comment-dots"></i>
              </div>
              <div class="modal-titles">
                <h3>图纸审核意见</h3>
                <span class="drawing-path">{{ selectedDrawing?.name }}</span>
              </div>
            </div>
            <button class="modal-close" @click="showCommentsModal = false">
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div class="modal-body-modern">
            <!-- 图纸基本信息 -->
            <div class="info-cards">
              <div class="info-card">
                <span class="info-label">版本</span>
                <span class="info-value version">V{{ selectedDrawing?.version || 1 }}</span>
              </div>
              <div class="info-card">
                <span class="info-label">上传者</span>
                <span class="info-value">{{ selectedDrawing?.uploader_name || '未知' }}</span>
              </div>
              <div class="info-card">
                <span class="info-label">上传时间</span>
                <span class="info-value">{{ formatTime(selectedDrawing?.created_at) }}</span>
              </div>
            </div>
            
            <!-- 审核意见 -->
            <div class="review-section">
              <div class="section-header">
                <i class="fas fa-clipboard-list"></i>
                <span>修改意见</span>
              </div>
              <div v-if="selectedDrawing?.comments" class="comments-box">
                <p>{{ selectedDrawing.comments }}</p>
              </div>
              <div v-else class="no-comments-box">
                <i class="fas fa-check-circle"></i>
                <span>暂无修改意见</span>
              </div>
            </div>
            
            <!-- 意见图片 -->
            <div v-if="selectedDrawing?.comment_images" class="images-section">
              <div class="section-header">
                <i class="fas fa-images"></i>
                <span>意见图片</span>
              </div>
              <div class="images-grid">
                <img 
                  v-for="(img, idx) in parseImages(selectedDrawing.comment_images)" 
                  :key="idx" 
                  :src="`${api.baseURL}${img}`" 
                  @click="previewImage(img)"
                  class="preview-thumb" />
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="btn btn-outline" @click="downloadDrawing(selectedDrawing)">
              <i class="fas fa-download"></i> 下载图纸
            </button>
            <button class="btn btn-primary" @click="showCommentsModal = false">
              关闭
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 图片预览 -->
    <Teleport to="body">
      <div v-if="previewUrl" class="preview-overlay-full" @click="previewUrl = null">
        <img :src="previewUrl" class="preview-image-full" />
        <button class="preview-close">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const drawings = ref([])
const loading = ref(false)
const expandedProjects = ref({})
const showCommentsModal = ref(false)
const selectedDrawing = ref(null)
const previewUrl = ref(null)
const searchKeyword = ref('')
const filterStatus = ref('all')

// 按订单分组
const groupedDrawings = computed(() => {
  const groups = {}
  drawings.value.forEach(d => {
    const orderId = d.order_id || 'unknown'
    if (!groups[orderId]) {
      groups[orderId] = []
    }
    groups[orderId].push(d)
  })
  return groups
})

// 过滤后的分组
const filteredDrawings = computed(() => {
  if (filterStatus.value === 'all' && !searchKeyword.value) {
    return drawings.value
  }
  return drawings.value.filter(d => {
    const matchSearch = !searchKeyword.value || d.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
    const matchFilter = filterStatus.value === 'all' || 
      (filterStatus.value === 'comments' && d.comments) ||
      (filterStatus.value === 'pending' && !d.comments)
    return matchSearch && matchFilter
  })
})

const filteredGroupedDrawings = computed(() => {
  const groups = {}
  filteredDrawings.value.forEach(d => {
    const orderId = d.order_id || 'unknown'
    if (!groups[orderId]) {
      groups[orderId] = []
    }
    groups[orderId].push(d)
  })
  return groups
})

// 统计：有意见的图纸数
const drawingsWithComments = computed(() => {
  return drawings.value.filter(d => d.comments).length
})

function getCommentsCount(drawings) {
  return drawings.filter(d => d.comments).length
}

async function loadDrawings() {
  loading.value = true
  try {
    drawings.value = await api.get('/api/drawings')
    // 默认展开所有项目
    Object.keys(groupedDrawings.value).forEach(orderId => {
      expandedProjects.value[orderId] = true
    })
  } catch (e) {
    authStore.toast('加载图纸列表失败', 'error')
  } finally {
    loading.value = false
  }
}

function toggleProject(orderId) {
  expandedProjects.value[orderId] = !expandedProjects.value[orderId]
}

function viewDrawingDetail(d) {
  viewComments(d)
}

function downloadDrawing(d) {
  window.open(`${api.baseURL}${d.file_url}`, '_blank')
}

function viewVersions(d) {
  router.push(`/drawings/${d.id}/versions`)
}

function viewComments(d) {
  selectedDrawing.value = d
  showCommentsModal.value = true
}

function previewImage(img) {
  previewUrl.value = `${api.baseURL}${img}`
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
  return new Date(time).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadDrawings()
})
</script>

<style scoped>
.drawings-page {
  width: 100%;
}

/* 统计卡片 */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f0f0;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-icon.blue {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-icon.purple {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-icon.orange {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.stat-icon.green {
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  color: white;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f0f0;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f5f7fa;
  padding: 8px 16px;
  border-radius: 8px;
  width: 280px;
}

.search-box i {
  color: #999;
}

.search-box input {
  border: none;
  background: transparent;
  outline: none;
  width: 100%;
  font-size: 14px;
}

.filter-tabs {
  display: flex;
  gap: 8px;
}

.filter-tab {
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-tab:hover {
  background: #f0f0f0;
}

.filter-tab.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  color: #999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

.empty-icon i {
  font-size: 36px;
  color: #667eea;
}

.empty-state h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
}

.empty-state p {
  color: #999;
  margin-bottom: 24px;
}

/* 项目分组 */
.projects-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.project-group {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f0f0;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  transition: background 0.2s;
}

.project-header:hover {
  background: #fafafa;
}

.project-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.folder-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  transition: all 0.3s;
}

.folder-icon.closed {
  background: linear-gradient(135deg, #a8a8a8 0%, #909090 100%);
}

.project-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.project-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 13px;
  color: #888;
  display: flex;
  align-items: center;
  gap: 4px;
}

.expand-btn {
  width: 32px;
  height: 32px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.expand-btn i {
  transition: transform 0.3s;
}

.expand-btn i.rotated {
  transform: rotate(180deg);
}

/* 图纸网格 */
.project-body {
  padding: 0 20px 20px;
}

.drawings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.drawing-card {
  background: #fafafa;
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.drawing-card:hover {
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #667eea30;
  transform: translateY(-2px);
}

.drawing-preview {
  position: relative;
  height: 100px;
  background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  overflow: hidden;
}

.file-icon-large {
  font-size: 40px;
  color: #ccc;
}

.preview-overlay {
  position: absolute;
  inset: 0;
  background: rgba(102, 126, 234, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.preview-overlay i {
  font-size: 24px;
  color: white;
}

.drawing-card:hover .preview-overlay {
  opacity: 1;
}

.drawing-info {
  margin-bottom: 12px;
}

.drawing-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin: 0 0 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.drawing-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-tag {
  background: #667eea20;
  color: #667eea;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.uploader {
  font-size: 12px;
  color: #999;
}

.drawing-status {
  margin-bottom: 12px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.status-badge.success {
  background: #dcfce7;
  color: #16a34a;
}

.status-badge.warning {
  background: #fef3c7;
  color: #d97706;
}

.drawing-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid #e5e5e5;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.action-btn.primary:hover {
  transform: scale(1.05);
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.comments-modal {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 560px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title-section {
  display: flex;
  align-items: center;
  gap: 14px;
}

.modal-icon {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.modal-titles h3 {
  color: white;
  margin: 0;
  font-size: 18px;
}

.drawing-path {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

.modal-close {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.modal-body-modern {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.info-card {
  background: #f8f9fa;
  padding: 14px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #888;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.info-value.version {
  color: #667eea;
}

.review-section,
.images-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.section-header i {
  color: #667eea;
}

.comments-box {
  background: #fef3c7;
  padding: 16px;
  border-radius: 10px;
  color: #92400e;
  line-height: 1.7;
}

.no-comments-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 30px;
  background: #f0fdf4;
  border-radius: 10px;
  color: #16a34a;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.preview-thumb {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.preview-thumb:hover {
  transform: scale(1.05);
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 图片预览 */
.preview-overlay-full {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  cursor: pointer;
}

.preview-image-full {
  max-width: 90%;
  max-height: 90vh;
  object-fit: contain;
}

.preview-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

/* 按钮样式 */
.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-outline {
  background: white;
  border: 1px solid #e5e5e5;
  color: #666;
}

.btn-outline:hover {
  border-color: #667eea;
  color: #667eea;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-bar {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-bar {
    grid-template-columns: 1fr;
  }
  
  .filter-bar {
    flex-direction: column;
    gap: 12px;
  }
  
  .search-box {
    width: 100%;
  }
  
  .drawings-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}
</style>
