<template>
  <div class="attachment-preview" :class="{ 'is-grid-view': isGridView }">
    <!-- 图片预览 -->
    <div v-if="isImage" class="image-preview">
      <div class="image-container">
        <img
          v-if="!imageError"
          :src="attachment.thumbnail_url || attachment.download_url"
          :alt="attachment.original_filename"
          class="preview-image"
          @click="previewImage"
          @error="handleImageError"
        />
        <div v-else class="image-error">
          <el-icon><Picture /></el-icon>
          <span>图片加载失败</span>
        </div>
        
        <!-- 图片信息覆盖层 -->
        <div class="image-overlay">
          <div class="image-info">
            <span v-if="attachment.metadata?.width && attachment.metadata?.height">
              {{ attachment.metadata.width }}×{{ attachment.metadata.height }}
            </span>
            <span>{{ formatFileSize(attachment.file_size) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 非图片文件预览 -->
    <div v-else class="file-preview">
      <div class="file-icon-container">
        <el-icon class="file-icon" :color="getFileIconColor(attachment.mime_type)">
          <component :is="getFileIcon(attachment.mime_type)" />
        </el-icon>
      </div>
      
      <div class="file-info">
        <div class="filename" :title="attachment.original_filename">
          {{ attachment.original_filename }}
        </div>
        <div class="file-meta">
          <span class="file-size">{{ formatFileSize(attachment.file_size) }}</span>
          <span class="file-type">{{ getFileTypeText(attachment.mime_type) }}</span>
          <span class="upload-time">{{ formatDate(attachment.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="attachment-actions" :class="{ 'overlay-actions': isImage }">
      <el-button-group>
        <el-button 
          size="small" 
          @click="downloadFile"
          :loading="isDownloading"
        >
          <el-icon><Download /></el-icon>
          <span v-if="!isGridView">下载</span>
        </el-button>
        
        <el-button 
          v-if="canPreview"
          size="small" 
          @click="previewFile"
        >
          <el-icon><View /></el-icon>
          <span v-if="!isGridView">预览</span>
        </el-button>
        
        <el-button 
          size="small" 
          type="danger" 
          @click="confirmDelete"
          :loading="isDeleting"
        >
          <el-icon><Delete /></el-icon>
          <span v-if="!isGridView">删除</span>
        </el-button>
      </el-button-group>
    </div>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="showImagePreview"
      :title="attachment.original_filename"
      :width="dialogWidth"
      top="5vh"
      append-to-body
      class="image-preview-dialog-wrapper"
      destroy-on-close
    >
      <div class="image-preview-dialog">
        <img
          :src="attachment.download_url"
          :alt="attachment.original_filename"
          class="preview-dialog-image"
          @load="handleImageLoad"
        />
      </div>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="showDeleteDialog"
      title="确认删除"
      width="400px"
      :before-close="handleDeleteDialogClose"
    >
      <p>确定要删除附件 "{{ attachment.original_filename }}" 吗？</p>
      <p class="delete-warning">此操作不可撤销。</p>
      
      <template #footer>
        <el-button @click="showDeleteDialog = false">取消</el-button>
        <el-button 
          type="danger" 
          @click="deleteAttachment"
          :loading="isDeleting"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  ElImage, 
  ElIcon, 
  ElButton, 
  ElButtonGroup, 
  ElDialog,
  ElMessage,
  ElMessageBox
} from 'element-plus'
import {
  Picture,
  Document,
  VideoPlay,
  Headset,
  Download,
  Delete,
  View,
  Files
} from '@element-plus/icons-vue'
import type { AttachmentInfo } from '../types/prompt'
import { attachmentApi } from '../api/attachment'

// 组件属性
interface Props {
  attachment: AttachmentInfo
  isGridView?: boolean
  showActions?: boolean
}

// 组件事件
interface Emits {
  (e: 'delete', attachmentId: number): void
  (e: 'preview', attachment: AttachmentInfo): void
  (e: 'download', attachment: AttachmentInfo): void
}

const props = withDefaults(defineProps<Props>(), {
  isGridView: false,
  showActions: true
})

const emit = defineEmits<Emits>()

// 响应式数据
const isDownloading = ref(false)
const isDeleting = ref(false)
const showDeleteDialog = ref(false)
const imageError = ref(false)
const showImagePreview = ref(false)
const dialogWidth = ref('90%')

// 计算属性
const isImage = computed(() => {
  return props.attachment.mime_type.startsWith('image/')
})

const canPreview = computed(() => {
  const mimeType = props.attachment.mime_type
  return mimeType.startsWith('image/') || 
         mimeType.startsWith('video/') ||
         mimeType.startsWith('audio/') ||
         mimeType === 'application/pdf' ||
         mimeType.startsWith('text/')
})

// 获取文件图标
const getFileIcon = (mimeType: string) => {
  if (mimeType.startsWith('image/')) return Picture
  if (mimeType.startsWith('video/')) return VideoPlay
  if (mimeType.startsWith('audio/')) return Headset
  if (mimeType.includes('pdf') || mimeType.includes('document')) return Document
  return Files
}

// 获取文件图标颜色
const getFileIconColor = (mimeType: string) => {
  if (mimeType.startsWith('image/')) return '#67C23A'
  if (mimeType.startsWith('video/')) return '#909399'
  if (mimeType.startsWith('audio/')) return '#F56C6C'
  if (mimeType.includes('pdf')) return '#E6A23C'
  if (mimeType.includes('document')) return '#409EFF'
  return '#909399'
}

// 获取文件类型文本
const getFileTypeText = (mimeType: string) => {
  if (mimeType.startsWith('image/')) return '图片'
  if (mimeType.startsWith('video/')) return '视频'
  if (mimeType.startsWith('audio/')) return '音频'
  if (mimeType.includes('pdf')) return 'PDF'
  if (mimeType.includes('document')) return '文档'
  if (mimeType.startsWith('text/')) return '文本'
  return '文件'
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return '今天 ' + date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 下载文件
const downloadFile = async () => {
  try {
    isDownloading.value = true
    const url = attachmentApi.getDownloadUrl(props.attachment.id)
    
    // 创建隐藏的下载链接
    const link = document.createElement('a')
    link.href = url
    link.download = props.attachment.original_filename
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    emit('download', props.attachment)
    ElMessage.success('开始下载文件')
  } catch (error) {
    ElMessage.error('下载失败：' + (error as Error).message)
  } finally {
    isDownloading.value = false
  }
}

// 预览图片
const previewImage = () => {
  if (isImage.value) {
    // 根据图片元数据计算对话框宽度
    calculateDialogWidth()
    showImagePreview.value = true
    emit('preview', props.attachment)
  }
}

// 处理图片加载错误
const handleImageError = () => {
  imageError.value = true
}

// 处理预览图片加载完成
const handleImageLoad = (event: Event) => {
  const img = event.target as HTMLImageElement
  const imgWidth = img.naturalWidth
  const imgHeight = img.naturalHeight
  
  // 根据图片实际尺寸调整对话框宽度
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const maxDialogWidth = viewportWidth * 0.9
  const maxDialogHeight = viewportHeight * 0.85
  
  // 计算合适的对话框宽度
  let targetWidth = imgWidth + 48 // 加上对话框的内边距
  
  // 如果图片高度超过最大高度，按比例缩放宽度
  if (imgHeight > maxDialogHeight) {
    const scale = maxDialogHeight / imgHeight
    targetWidth = imgWidth * scale + 48
  }
  
  // 限制在最小和最大宽度之间
  targetWidth = Math.max(400, Math.min(targetWidth, maxDialogWidth))
  
  dialogWidth.value = `${targetWidth}px`
}

// 计算对话框初始宽度
const calculateDialogWidth = () => {
  // 如果有图片元数据，使用元数据计算
  if (props.attachment.metadata?.width && props.attachment.metadata?.height) {
    const imgWidth = props.attachment.metadata.width
    const imgHeight = props.attachment.metadata.height
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const maxDialogWidth = viewportWidth * 0.9
    const maxDialogHeight = viewportHeight * 0.85
    
    let targetWidth = imgWidth + 48
    
    if (imgHeight > maxDialogHeight) {
      const scale = maxDialogHeight / imgHeight
      targetWidth = imgWidth * scale + 48
    }
    
    targetWidth = Math.max(400, Math.min(targetWidth, maxDialogWidth))
    dialogWidth.value = `${targetWidth}px`
  } else {
    // 没有元数据时使用默认宽度
    dialogWidth.value = '90%'
  }
}

// 预览文件
const previewFile = () => {
  if (isImage.value) {
    previewImage()
    return
  }
  
  // 其他类型文件在新窗口打开
  const url = attachmentApi.getDownloadUrl(props.attachment.id)
  window.open(url, '_blank')
  emit('preview', props.attachment)
}

// 确认删除
const confirmDelete = () => {
  showDeleteDialog.value = true
}

// 删除附件
const deleteAttachment = async () => {
  try {
    isDeleting.value = true
    await attachmentApi.delete(props.attachment.id)
    showDeleteDialog.value = false
    emit('delete', props.attachment.id)
    ElMessage.success('附件删除成功')
  } catch (error) {
    ElMessage.error('删除失败：' + (error as Error).message)
  } finally {
    isDeleting.value = false
  }
}

// 处理删除对话框关闭
const handleDeleteDialogClose = (done: () => void) => {
  if (!isDeleting.value) {
    done()
  }
}
</script>

<style scoped>
.attachment-preview {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--el-bg-color);
  transition: all 0.3s;
  position: relative;
}

.attachment-preview:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

/* 网格视图样式 */
.attachment-preview.is-grid-view {
  aspect-ratio: 1;
}

.attachment-preview.is-grid-view .file-preview {
  padding: 16px;
  text-align: center;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.attachment-preview.is-grid-view .filename {
  font-size: 12px;
  line-height: 1.4;
  max-height: 2.8em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.attachment-preview.is-grid-view .file-meta {
  font-size: 11px;
  margin-top: 4px;
}

.attachment-preview.is-grid-view .file-meta span {
  display: block;
  margin: 2px 0;
}

/* 图片预览样式 */
.image-preview {
  width: 100%;
  height: 100%;
  position: relative;
}

.image-container {
  position: relative;
  width: 100%;
  height: 200px;
  overflow: hidden;
  background-color: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-preview.is-grid-view .image-container {
  height: 100%;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-secondary);
  background-color: var(--el-fill-color-light);
}

.image-error .el-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  padding: 16px 12px 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-container:hover .image-overlay {
  opacity: 1;
}

.image-info {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: white;
}

/* 文件预览样式 */
.file-preview {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 12px;
}

.file-icon-container {
  flex-shrink: 0;
}

.file-icon {
  font-size: 32px;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.filename {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.file-meta span {
  position: relative;
}

.file-meta span:not(:last-child)::after {
  content: '•';
  margin-left: 8px;
  color: var(--el-border-color);
}

/* 操作按钮样式 */
.attachment-actions {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  background-color: var(--el-fill-color-blank);
}

.attachment-actions.overlay-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 0;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 6px;
  opacity: 0;
  transition: opacity 0.3s;
}

.attachment-preview:hover .overlay-actions {
  opacity: 1;
}

.overlay-actions .el-button-group {
  display: flex;
}

.overlay-actions .el-button {
  background: transparent;
  border-color: transparent;
  color: white;
}

.overlay-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 删除确认对话框样式 */
.delete-warning {
  color: var(--el-color-warning);
  font-size: 14px;
  margin-top: 8px;
}

/* 图片预览对话框样式 */
.image-preview-dialog-wrapper :deep(.el-dialog) {
  max-width: 1400px;
  margin: 0 auto;
}

.image-preview-dialog-wrapper :deep(.el-dialog__body) {
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-fill-color-light);
}

.image-preview-dialog {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 400px;
  max-height: 85vh;
  overflow: auto;
}

.preview-dialog-image {
  max-width: 100%;
  max-height: 85vh;
  width: auto;
  height: auto;
  object-fit: contain;
  display: block;
  margin: 0 auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .file-preview {
    padding: 12px;
  }
  
  .attachment-actions {
    padding: 8px 12px;
  }
  
  .file-meta {
    flex-direction: column;
    gap: 2px;
  }
  
  .file-meta span::after {
    display: none;
  }
}
</style>