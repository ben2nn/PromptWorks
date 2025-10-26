import { ref, computed, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { attachmentApi, type UploadProgressCallback } from '../api/attachment'
import type { AttachmentInfo } from '../types/prompt'

export interface UploadProgress {
  fileIndex: number
  fileName: string
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

interface UseAttachmentManagementResult {
  // 状态
  attachments: Ref<AttachmentInfo[]>
  uploadProgress: Ref<UploadProgress[]>
  isUploading: Ref<boolean>
  loading: Ref<boolean>
  error: Ref<string | null>
  
  // 计算属性
  totalProgress: Ref<number>
  hasAttachments: Ref<boolean>
  imageAttachments: Ref<AttachmentInfo[]>
  documentAttachments: Ref<AttachmentInfo[]>
  
  // 方法
  loadAttachments: (promptId: number) => Promise<void>
  uploadFile: (promptId: number, file: File) => Promise<AttachmentInfo | null>
  uploadFiles: (promptId: number, files: File[]) => Promise<AttachmentInfo[]>
  deleteAttachment: (attachmentId: number) => Promise<void>
  deleteMultipleAttachments: (attachmentIds: number[]) => Promise<void>
  clearProgress: () => void
  getAttachmentById: (id: number) => AttachmentInfo | undefined
}

export function useAttachmentManagement(): UseAttachmentManagementResult {
  // 响应式状态
  const attachments = ref<AttachmentInfo[]>([])
  const uploadProgress = ref<UploadProgress[]>([])
  const isUploading = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const totalProgress = computed(() => {
    if (uploadProgress.value.length === 0) return 0
    
    const total = uploadProgress.value.reduce((sum: number, item: UploadProgress) => sum + item.progress, 0)
    return Math.round(total / uploadProgress.value.length)
  })

  const hasAttachments = computed(() => attachments.value.length > 0)

  const imageAttachments = computed(() => 
    attachments.value.filter((att: AttachmentInfo) => attachmentApi.isImageFile(att.mime_type))
  )

  const documentAttachments = computed(() => 
    attachments.value.filter((att: AttachmentInfo) => !attachmentApi.isImageFile(att.mime_type))
  )

  // 加载附件列表
  async function loadAttachments(promptId: number): Promise<void> {
    if (!promptId || promptId <= 0) {
      attachments.value = []
      return
    }

    loading.value = true
    error.value = null
    
    try {
      const result = await attachmentApi.list(promptId)
      attachments.value = result
    } catch (err) {
      const message = err instanceof Error ? err.message : '加载附件列表失败'
      error.value = message
      ElMessage.error(message)
      attachments.value = []
    } finally {
      loading.value = false
    }
  }

  // 上传单个文件
  async function uploadFile(promptId: number, file: File): Promise<AttachmentInfo | null> {
    if (!promptId || promptId <= 0) {
      ElMessage.error('无效的提示词ID')
      return null
    }

    // 初始化进度状态
    const progressItem: UploadProgress = {
      fileIndex: 0,
      fileName: file.name,
      progress: 0,
      status: 'uploading'
    }
    
    uploadProgress.value = [progressItem]
    isUploading.value = true
    error.value = null

    try {
      const onProgress: UploadProgressCallback = (progress) => {
        progressItem.progress = progress
      }

      const attachment = await attachmentApi.upload(promptId, file, onProgress)
      
      // 更新状态
      progressItem.status = 'success'
      progressItem.progress = 100
      
      // 添加到附件列表
      attachments.value.push(attachment)
      
      ElMessage.success(`文件 ${file.name} 上传成功`)
      return attachment
      
    } catch (err) {
      const message = err instanceof Error ? err.message : '文件上传失败'
      progressItem.status = 'error'
      progressItem.error = message
      error.value = message
      ElMessage.error(`文件 ${file.name} 上传失败: ${message}`)
      return null
      
    } finally {
      isUploading.value = false
    }
  }

  // 批量上传文件
  async function uploadFiles(promptId: number, files: File[]): Promise<AttachmentInfo[]> {
    if (!promptId || promptId <= 0) {
      ElMessage.error('无效的提示词ID')
      return []
    }

    if (files.length === 0) {
      return []
    }

    // 初始化进度状态
    uploadProgress.value = files.map((file, index) => ({
      fileIndex: index,
      fileName: file.name,
      progress: 0,
      status: 'pending' as const
    }))
    
    isUploading.value = true
    error.value = null
    const results: AttachmentInfo[] = []

    try {
      // 逐个上传文件
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const progressItem = uploadProgress.value[i]
        
        try {
          progressItem.status = 'uploading'
          
          const onProgress: UploadProgressCallback = (progress) => {
            progressItem.progress = progress
          }

          const attachment = await attachmentApi.upload(promptId, file, onProgress)
          
          progressItem.status = 'success'
          progressItem.progress = 100
          results.push(attachment)
          
          // 添加到附件列表
          attachments.value.push(attachment)
          
        } catch (err) {
          const message = err instanceof Error ? err.message : '上传失败'
          progressItem.status = 'error'
          progressItem.error = message
          ElMessage.error(`文件 ${file.name} 上传失败: ${message}`)
        }
      }

      const successCount = results.length
      const totalCount = files.length
      
      if (successCount === totalCount) {
        ElMessage.success(`所有文件上传成功 (${successCount}/${totalCount})`)
      } else if (successCount > 0) {
        ElMessage.warning(`部分文件上传成功 (${successCount}/${totalCount})`)
      } else {
        ElMessage.error('所有文件上传失败')
      }

      return results
      
    } finally {
      isUploading.value = false
    }
  }

  // 删除附件
  async function deleteAttachment(attachmentId: number): Promise<void> {
    try {
      await attachmentApi.delete(attachmentId)
      
      // 从列表中移除
      const index = attachments.value.findIndex((att: AttachmentInfo) => att.id === attachmentId)
      if (index !== -1) {
        const attachment = attachments.value[index]
        attachments.value.splice(index, 1)
        ElMessage.success(`附件 ${attachment.original_filename} 删除成功`)
      }
      
    } catch (err) {
      const message = err instanceof Error ? err.message : '删除附件失败'
      error.value = message
      ElMessage.error(message)
    }
  }

  // 批量删除附件
  async function deleteMultipleAttachments(attachmentIds: number[]): Promise<void> {
    if (attachmentIds.length === 0) return

    try {
      await attachmentApi.deleteMultiple(attachmentIds)
      
      // 从列表中移除
      attachments.value = attachments.value.filter((att: AttachmentInfo) => !attachmentIds.includes(att.id))
      
      ElMessage.success(`成功删除 ${attachmentIds.length} 个附件`)
      
    } catch (err) {
      const message = err instanceof Error ? err.message : '批量删除附件失败'
      error.value = message
      ElMessage.error(message)
    }
  }

  // 清除上传进度
  function clearProgress(): void {
    uploadProgress.value = []
    isUploading.value = false
  }

  // 根据ID获取附件
  function getAttachmentById(id: number): AttachmentInfo | undefined {
    return attachments.value.find((att: AttachmentInfo) => att.id === id)
  }

  return {
    // 状态
    attachments,
    uploadProgress,
    isUploading,
    loading,
    error,
    
    // 计算属性
    totalProgress,
    hasAttachments,
    imageAttachments,
    documentAttachments,
    
    // 方法
    loadAttachments,
    uploadFile,
    uploadFiles,
    deleteAttachment,
    deleteMultipleAttachments,
    clearProgress,
    getAttachmentById
  }
}