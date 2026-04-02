<template>
  <div class="drawings-page">
    <div class="page-header">
      <h2>图纸管理</h2>
    </div>

    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i> 加载中...
    </div>
    
    <div v-else-if="Object.keys(groupedDrawings).length === 0" class="empty-state">
      <i class="fas fa-drafting-compass"></i>
      <p>暂无图纸记录</p>
    </div>

    <!-- 按项目分组展示 -->
    <div v-else class="projects-list">
      <div v-for="(drawings, orderId) in groupedDrawings" :key="orderId" class="project-card">
        <div class="project-header" @click="toggleProject(orderId)">
          <div class="project-info">
            <i class="fas fa-folder-open" :class="{ 'fa-folder': !expandedProjects[orderId] }"></i>
            <span class="project-title">{{ drawings[0].order_title || `订单 #${orderId}` }}</span>
            <span class="project-count">{{ drawings.length }} 个文件</span>
          </div>
          <i class="fas fa-chevron-down toggle-icon" :class="{ rotated: expandedProjects[orderId] }"></i>
        </div>
        
        <div class="project-drawings" v-show="expandedProjects[orderId]">
          <table class="drawings-table">
            <thead>
              <tr>
                <th>图纸名称</th>
                <th>版本</th>
                <th>上传者</th>
                <th>上传时间</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in drawings" :key="d.id">
                <td>
                  <i class="fas fa-file-alt file-icon"></i>
                  {{ d.name }}
                </td>
                <td><span class="version-badge">{{ d.version || 'V1' }}</span></td>
                <td>{{ d.uploader_name || '未知' }}</td>
                <td>{{ formatTime(d.created_at) }}</td>
                <td>
                  <span v-if="d.comments" class="status-tag has-comments">
                    <i class="fas fa-comment"></i> 有意见
                  </span>
                  <span v-else class="status-tag ok">
                    <i class="fas fa-check"></i> 待审核
                  </span>
                </td>
                <td>
                  <button class="btn btn-sm btn-outline" @click="downloadDrawing(d)" title="下载">
                    <i class="fas fa-download"></i>
                  </button>
                  <button class="btn btn-sm btn-info" @click="viewVersions(d)" title="版本历史">
                    <i class="fas fa-history"></i>
                  </button>
                  <button v-if="d.comments" class="btn btn-sm btn-link" @click="viewComments(d)" title="查看意见">
                    <i class="fas fa-eye"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 意见查看模态框 -->
    <div v-if="showCommentsModal" class="modal-overlay" @click.self="showCommentsModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>图纸意见</h3>
          <button class="close-btn" @click="showCommentsModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="drawing-info">
            <p><strong>图纸名称：</strong>{{ selectedDrawing?.name }}</p>
            <p><strong>版本：</strong>{{ selectedDrawing?.version || 'V1' }}</p>
          </div>
          <div class="comments-section">
            <h4>修改意见</h4>
            <div v-if="selectedDrawing?.comments" class="comments-content">
              <p>{{ selectedDrawing.comments }}</p>
            </div>
            <div v-else class="no-comments">
              <i class="fas fa-check-circle"></i>
              <p>暂无修改意见</p>
            </div>
          </div>
          <div v-if="selectedDrawing?.comment_images" class="images-section">
            <h4>意见图片</h4>
            <div class="comment-images">
              <img v-for="(img, idx) in parseImages(selectedDrawing.comment_images)" 
                   :key="idx" 
                   :src="`http://127.0.0.1:8001${img}`" 
                   @click="previewImage(img)"
                   class="comment-img" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片预览模态框 -->
    <div v-if="previewUrl" class="modal-overlay" @click="previewUrl = null">
      <img :src="previewUrl" class="preview-image" />
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

const drawings = ref([])
const loading = ref(false)
const expandedProjects = ref({})
const showCommentsModal = ref(false)
const selectedDrawing = ref(null)
const previewUrl = ref(null)

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

async function loadDrawings() {
  loading.value = true
  try {
    drawings.value = await api.get('/api/drawings')
    // 默认展开第一个项目
    if (drawings.value.length > 0) {
      const firstOrderId = drawings.value[0].order_id
      expandedProjects.value[firstOrderId] = true
    }
  } catch (e) {
    authStore.toast('加载图纸列表失败', 'error')
  } finally {
    loading.value = false
  }
}

function toggleProject(orderId) {
  expandedProjects.value[orderId] = !expandedProjects.value[orderId]
}

function downloadDrawing(d) {
  window.open(`http://127.0.0.1:8001${d.file_url}`, '_blank')
}

function viewVersions(d) {
  router.push(`/drawings/${d.id}/versions`)
}

function viewComments(d) {
  selectedDrawing.value = d
  showCommentsModal.value = true
}

function previewImage(img) {
  previewUrl.value = `http://127.0.0.1:8001${img}`
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

.page-header {
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

/* 项目卡片 */
.projects-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.project-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  overflow: hidden;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
}

.project-header:hover {
  background: linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%);
}

.project-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-info i {
  font-size: 20px;
}

.project-title {
  font-weight: 600;
  font-size: 16px;
}

.project-count {
  background: rgba(255,255,255,0.2);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
}

.toggle-icon {
  transition: transform 0.3s;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

/* 图纸表格 */
.project-drawings {
  padding: 0;
}

.drawings-table {
  width: 100%;
  border-collapse: collapse;
}

.drawings-table th {
  background: #f8f9fa;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #666;
  font-size: 13px;
  border-bottom: 1px solid #eee;
}

.drawings-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f5f5f5;
  color: #333;
}

.drawings-table tr:last-child td {
  border-bottom: none;
}

.drawings-table tr:hover {
  background: #f8f9fa;
}

.file-icon {
  color: #667eea;
  margin-right: 8px;
}

.version-badge {
  background: #e8eaff;
  color: #667eea;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
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

.btn-sm {
  padding: 6px 10px;
  font-size: 12px;
}

.btn-link {
  color: #667eea;
  background: none;
  border: none;
  cursor: pointer;
}

.btn-link:hover {
  color: #5a6fd6;
}

.btn-info {
  color: #667eea;
  background: #e8eaff;
  border: 1px solid #d0d0f0;
}

.btn-info:hover {
  background: #d8d8f8;
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

.drawing-info {
  background: #f8f9fa;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.drawing-info p {
  margin: 4px 0;
}

.comments-section h4,
.images-section h4 {
  color: #333;
  margin-bottom: 12px;
  font-size: 14px;
}

.comments-content {
  background: #fff3cd;
  padding: 16px;
  border-radius: 8px;
  color: #856404;
  line-height: 1.6;
}

.no-comments {
  text-align: center;
  padding: 30px;
  color: #999;
}

.no-comments i {
  font-size: 32px;
  margin-bottom: 8px;
  color: #28a745;
}

.comment-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.comment-img {
  width: 120px;
  height: 120px;
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
