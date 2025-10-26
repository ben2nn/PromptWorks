<template>
  <div class="file-uploader">
    <el-upload
      ref="uploadRef"
      :action="uploadAction"
      :http-request="handleCustomUpload"
      :before-upload="beforeUpload"
      :on-success="handleSuccess"
      :on-error="handleError"
      :on-progress="handleProgress"
      :file-list="fileList"
      :accept="acceptedTypes"
      :multiple="allowMultiple"
      :disabled="disabled || isUploading"
      :show-file-list="showFileList"
      :auto-upload="true"
      drag
      class="upload-dragger"
    >
      <div class="upload-content">
        <el-icon class="upload-icon" :class="{ 'is-uploading': isUploading }">
          <UploadFilled v-if="!isUploading" />
          <Loading v-else />
        </el-icon>
        <div class="upload-text">
          <div class="primary-text">
            {{ isUploading ? '正在上传...' : '拖拽文件到此处或点击上传' }}
          </div>
          <div class="secondary-text">
            支持 {{ acceptedTypesText }}，单个文件不超过 {{ maxSizeText }}
          </div>
        </div>
      </div>
      
      <!-- 上传进度 -->
      <div v-if="isUploading && uploadProgress > 0" class="upload-progress">
        <el-progress 
          :percentage="uploadProgress" 
          :stroke-width="6"
          :show-text="false"
        />
        <span class="progress-text">{{ uploadProgress }}%</span>
      </div>
    </el-upload>

    <!-- 文件列表 -->
    <div v-if="showFileList && fileList.length > 0" class="file-list">
      <div class="file-list-header">
        <span>已选择文件 ({{ fileList.length }})</span>
        <el-button 
          v-if="!isUploading" 
          size="small" 
          type="danger" 
          text 
          @click="clearFiles"
        >
          清空
        </el-button>
      </div>
      <div class="file-items">
        <div 
          v-for="(file, index) in fileList" 
          :key="index" 
          class="file-item"
        >
          <div class="file-info">
            <el-icon class="file-icon">
              <Document />
            </el-icon>
            <div class="file-details">
              <div class="file-name">{{ file.name }}</div>
              <div class="file-size">{{ formatFileSize(file.size || 0) }}</div>
            </div>
          </div>
          <el-button 
            v-if="!isUploading"
            size="small" 
            type="danger" 
            text 
            @click="removeFile(index)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElUpload, ElIcon, ElButton, ElProgress, ElMessage } from 'element-plus'
import { 
  UploadFilled, 
  Loading, 
  Document, 
  Close 
} from '@element-plus/icons-vue'
import type { UploadFile, UploadFiles, UploadProgressEvent } from 'element-plus'
import { MediaType } from '../types/prompt'
import { attachmentApi } from '../api/attachment'

// 组件属性
interface Props {
  promptId?: number
  mediaType?: MediaType
  maxSize?: number // 最大文件大小，单位字节
  allowMultiple?: boolean
  disabled?: boolean
  showFileList?: boolean
  deferUpload?: boolean // 延迟上传模式，先暂存文件不立即上传
}

// 组件事件
interface Emits {
  (e: 'upload-success', file: any): void
  (e: 'upload-error', error: Error): void
  (e: 'files-change', files: UploadFiles): void
  (e: 'files-ready', files: File[]): void // 文件准备就绪（延迟上传模式）
}

const props = withDefaults(defineProps<Props>(), {
  maxSize: 10 * 1024 * 1024, // 默认10MB
  allowMultiple: false,
  disabled: false,
  showFileList: true,
  deferUpload: false
})

const emit = defineEmits<Emits>()

// 响应式数据
const uploadRef = ref<InstanceType<typeof ElUpload>>()
const fileList = ref<UploadFiles>([])
const pendingFiles = ref<File[]>([]) // 暂存的文件对象（延迟上传模式）
const uploadedAttachmentIds = ref<number[]>([]) // 已上传的临时附件 ID
const isUploading = ref(false)
const uploadProgress = ref(0)

// 上传地址（这里是占位符，实际上传通过自定义方法处理）
const uploadAction = computed(() => '#')

// 根据媒体类型确定接受的文件类型
const acceptedTypes = computed(() => {
  switch (props.mediaType) {
    case MediaType.IMAGE:
      return '.jpg,.jpeg,.png,.gif,.webp'
    case MediaType.DOCUMENT:
      return '.pdf,.doc,.docx,.txt,.md'
    case MediaType.AUDIO:
      return '.mp3,.wav,.ogg,.m4a'
    case MediaType.VIDEO:
      return '.mp4,.avi,.mov,.wmv'
    default:
      return '*'
  }
})

// 接受的文件类型文本描述
const acceptedTypesText = computed(() => {
  switch (props.mediaType) {
    case MediaType.IMAGE:
      return 'JPG、PNG、GIF、WebP 格式图片'
    case MediaType.DOCUMENT:
      return 'PDF、Word、文本文档'
    case MediaType.AUDIO:
      return 'MP3、WAV、OGG 音频文件'
    case MediaType.VIDEO:
      return 'MP4、AVI、MOV 视频文件'
    default:
      return '所有文件类型'
  }
})

// 最大文件大小文本描述
const maxSizeText = computed(() => {
  const size = props.maxSize
  if (size >= 1024 * 1024) {
    return `${Math.round(size / (1024 * 1024))}MB`
  } else if (size >= 1024) {
    return `${Math.round(size / 1024)}KB`
  } else {
    return `${size}B`
  }
})

// 文件上传前的验证
const beforeUpload = (file: File): boolean => {
  // 检查文件大小
  if (file.size > props.maxSize) {
    ElMessage.error(`文件大小不能超过 ${maxSizeText.value}`)
    return false
  }

  // 检查文件类型
  if (props.mediaType && props.mediaType !== MediaType.TEXT) {
    const isValidType = validateFileType(file, props.mediaType)
    if (!isValidType) {
      ElMessage.error(`请选择正确的文件类型：${acceptedTypesText.value}`)
      return false
    }
  }

  return true
}

// 验证文件类型
const validateFileType = (file: File, mediaType: MediaType): boolean => {
  const fileName = file.name.toLowerCase()
  const fileType = file.type.toLowerCase()

  switch (mediaType) {
    case MediaType.IMAGE:
      return fileType.startsWith('image/') || 
             /\.(jpg|jpeg|png|gif|webp)$/.test(fileName)
    case MediaType.DOCUMENT:
      return fileType.includes('pdf') || 
             fileType.includes('document') || 
             fileType.includes('text') ||
             /\.(pdf|doc|docx|txt|md)$/.test(fileName)
    case MediaType.AUDIO:
      return fileType.startsWith('audio/') || 
             /\.(mp3|wav|ogg|m4a)$/.test(fileName)
    case MediaType.VIDEO:
      return fileType.startsWith('video/') || 
             /\.(mp4|avi|mov|wmv)$/.test(fileName)
    default:
      return true
  }
}

// 处理上传成功（由 Element Plus 自动调用）
const handleSuccess = (response: any, file: UploadFile) => {
  // 不需要处理，已经在 handleCustomUpload 中处理了
  // 这里只是为了兼容 Element Plus 的回调
}

// 处理上传错误
const handleError = (error: Error) => {
  isUploading.value = false
  uploadProgress.value = 0
  ElMessage.error('文件上传失败：' + error.message)
  emit('upload-error', error)
}

// 处理上传进度
const handleProgress = (event: UploadProgressEvent) => {
  isUploading.value = true
  uploadProgress.value = Math.round(event.percent || 0)
}

// Element Plus 自定义上传处理器
const handleCustomUpload = async (options: any) => {
  const { file, onProgress, onSuccess, onError } = options
  
  try {
    isUploading.value = true
    
    // 使用 promptId=0 表示临时上传，否则正常上传
    const uploadPromptId = (props.deferUpload || !props.promptId) ? 0 : props.promptId
    
    const result = await attachmentApi.upload(
      uploadPromptId,
      file,
      (progress) => {
        uploadProgress.value = progress
        onProgress({ percent: progress })
      }
    )
    
    isUploading.value = false
    uploadProgress.value = 0
    
    // 如果是临时上传，保存附件 ID
    if (uploadPromptId === 0) {
      pendingFiles.value.push(file)
      uploadedAttachmentIds.value.push(result.id)
      ElMessage.success('文件已上传，将在保存时关联')
      emit('files-ready', pendingFiles.value)
    } else {
      ElMessage.success('文件上传成功')
    }
    
    // 发出上传成功事件，用于显示预览
    emit('upload-success', result)
    onSuccess(result)
  } catch (error) {
    isUploading.value = false
    uploadProgress.value = 0
    onError(error)
    ElMessage.error('文件上传失败：' + (error as Error).message)
    emit('upload-error', error as Error)
  }
}

// 自定义上传方法（供外部调用）
const customUpload = async (file: File) => {
  const uploadPromptId = props.promptId || 0

  try {
    isUploading.value = true
    const result = await attachmentApi.upload(uploadPromptId, file, (progress) => {
      uploadProgress.value = progress
    })
    isUploading.value = false
    uploadProgress.value = 0
    
    if (uploadPromptId === 0) {
      uploadedAttachmentIds.value.push(result.id)
      ElMessage.success('文件已上传，将在保存时关联')
    } else {
      ElMessage.success('文件上传成功')
      emit('upload-success', result)
    }
    
    return result
  } catch (error) {
    isUploading.value = false
    uploadProgress.value = 0
    ElMessage.error('文件上传失败：' + (error as Error).message)
    emit('upload-error', error as Error)
    throw error
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 清空文件列表
const clearFiles = () => {
  fileList.value = []
  pendingFiles.value = []
  uploadedAttachmentIds.value = []
  uploadRef.value?.clearFiles()
  emit('files-change', [])
  emit('files-ready', [])
}

// 移除单个文件
const removeFile = async (index: number) => {
  fileList.value.splice(index, 1)
  
  // 如果是临时上传的文件，需要删除服务器上的文件
  if (index < uploadedAttachmentIds.value.length) {
    const attachmentId = uploadedAttachmentIds.value[index]
    try {
      await attachmentApi.delete(attachmentId)
    } catch (error) {
      console.error('删除临时附件失败:', error)
    }
    uploadedAttachmentIds.value.splice(index, 1)
  }
  
  if (index < pendingFiles.value.length) {
    pendingFiles.value.splice(index, 1)
    emit('files-ready', pendingFiles.value)
  }
  
  emit('files-change', fileList.value)
}

// 关联临时附件到提示词（供外部调用）
const attachToPrompt = async (promptId: number): Promise<AttachmentInfo[]> => {
  if (uploadedAttachmentIds.value.length === 0) {
    return []
  }

  try {
    // 调用批量更新 API
    const results = await attachmentApi.batchUpdatePrompt(
      uploadedAttachmentIds.value,
      promptId
    )

    ElMessage.success(`成功关联 ${results.length} 个附件`)

    // 清空临时数据
    pendingFiles.value = []
    uploadedAttachmentIds.value = []
    clearFiles()
    
    return results
  } catch (error) {
    console.error('关联附件失败:', error)
    ElMessage.error('关联附件失败：' + (error as Error).message)
    throw error
  }
}

// 兼容旧方法名
const uploadPendingFiles = attachToPrompt

// 监听文件列表变化
watch(fileList, (newFiles) => {
  emit('files-change', newFiles)
}, { deep: true })

// 暴露给父组件的方法
defineExpose({
  clearFiles,
  customUpload,
  uploadPendingFiles,
  attachToPrompt,
  getPendingFiles: () => pendingFiles.value,
  getUploadedAttachmentIds: () => uploadedAttachmentIds.value
})
</script>

<style scoped>
.file-uploader {
  width: 100%;
}

.upload-dragger {
  width: 100%;
}

.upload-content {
  padding: 40px 20px;
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  color: var(--el-color-primary);
  margin-bottom: 16px;
  transition: all 0.3s;
}

.upload-icon.is-uploading {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.upload-text {
  color: var(--el-text-color-regular);
}

.primary-text {
  font-size: 16px;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.secondary-text {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.upload-progress {
  margin-top: 16px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-text {
  font-size: 14px;
  color: var(--el-color-primary);
  min-width: 40px;
}

.file-list {
  margin-top: 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  overflow: hidden;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
  font-size: 14px;
  font-weight: 500;
}

.file-items {
  max-height: 200px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  font-size: 20px;
  color: var(--el-color-primary);
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  word-break: break-all;
}

.file-size {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* 拖拽悬停效果 */
:deep(.el-upload-dragger:hover) {
  border-color: var(--el-color-primary);
}

:deep(.el-upload-dragger.is-dragover) {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .upload-content {
    padding: 30px 16px;
  }

  .upload-icon {
    font-size: 40px;
    margin-bottom: 12px;
  }

  .primary-text {
    font-size: 15px;
    margin-bottom: 6px;
  }

  .secondary-text {
    font-size: 13px;
  }

  .upload-progress {
    padding: 0 16px;
    gap: 8px;
  }

  .progress-text {
    font-size: 13px;
    min-width: 35px;
  }

  .file-list-header {
    padding: 10px 12px;
    font-size: 13px;
  }

  .file-item {
    padding: 10px 12px;
  }

  .file-info {
    gap: 8px;
  }

  .file-icon {
    font-size: 18px;
  }

  .file-name {
    font-size: 13px;
    margin-bottom: 2px;
  }

  .file-size {
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .upload-content {
    padding: 24px 12px;
  }

  .upload-icon {
    font-size: 36px;
    margin-bottom: 10px;
  }

  .primary-text {
    font-size: 14px;
    margin-bottom: 4px;
  }

  .secondary-text {
    font-size: 12px;
    line-height: 1.4;
  }

  .upload-progress {
    flex-direction: column;
    gap: 6px;
    align-items: stretch;
  }

  .progress-text {
    text-align: center;
    min-width: unset;
  }

  .file-list-header {
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
  }

  .file-item {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .file-info {
    justify-content: flex-start;
  }

  .file-details {
    flex: unset;
  }
}
</style>