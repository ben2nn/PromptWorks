import { request, API_BASE_URL } from './http'
import type { AttachmentInfo, BatchOperationResult } from '../types/prompt'
import type { 
  AttachmentQueryParams, 
  AttachmentStats, 
  FileProcessingOptions,
  AttachmentErrorDetail 
} from '../types/attachment'

export interface UploadResponse {
  attachment: AttachmentInfo
}

export interface UploadProgressCallback {
  (progress: number): void
}

export interface BatchUploadResult extends BatchOperationResult<AttachmentInfo> {
  attachments: AttachmentInfo[]
}

export interface AttachmentListResponse {
  attachments: AttachmentInfo[]
  total: number
  limit: number
  offset: number
}

export interface AttachmentValidationResult {
  valid: boolean
  errors: AttachmentErrorDetail[]
  warnings: string[]
}

export const attachmentApi = {
  // 上传附件（支持进度回调）
  // promptId=0 表示临时上传
  async upload(
    promptId: number, 
    file: File, 
    onProgress?: UploadProgressCallback
  ): Promise<AttachmentInfo> {
    const formData = new FormData()
    formData.append('file', file)
    
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      
      // 监听上传进度
      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100)
            onProgress(progress)
          }
        })
      }
      
      // 监听请求完成
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result = JSON.parse(xhr.responseText)
            resolve(result.attachment)
          } catch (error) {
            reject(new Error('响应解析失败'))
          }
        } else {
          reject(new Error(`文件上传失败: ${xhr.status} ${xhr.statusText}`))
        }
      })
      
      // 监听请求错误
      xhr.addEventListener('error', () => {
        reject(new Error('网络错误'))
      })
      
      // 监听请求中止
      xhr.addEventListener('abort', () => {
        reject(new Error('上传已取消'))
      })
      
      // 发送请求
      xhr.open('POST', `${API_BASE_URL}/prompts/${promptId}/attachments`)
      xhr.send(formData)
    })
  },

  // 批量上传附件
  async uploadMultiple(
    promptId: number,
    files: File[],
    onProgress?: (fileIndex: number, progress: number) => void
  ): Promise<AttachmentInfo[]> {
    const results: AttachmentInfo[] = []
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const progressCallback = onProgress 
        ? (progress: number) => onProgress(i, progress)
        : undefined
      
      try {
        const attachment = await this.upload(promptId, file, progressCallback)
        results.push(attachment)
      } catch (error) {
        // 继续上传其他文件，但记录错误
        console.error(`文件 ${file.name} 上传失败:`, error)
        throw error
      }
    }
    
    return results
  },

  // 获取附件列表
  async list(promptId: number): Promise<AttachmentInfo[]> {
    return request<AttachmentInfo[]>(`/prompts/${promptId}/attachments`)
  },

  // 获取单个附件信息
  async get(attachmentId: number): Promise<AttachmentInfo> {
    return request<AttachmentInfo>(`/attachments/${attachmentId}`)
  },

  // 删除附件
  async delete(attachmentId: number): Promise<void> {
    return request<void>(`/attachments/${attachmentId}`, {
      method: 'DELETE'
    })
  },

  // 批量删除附件
  async deleteMultiple(attachmentIds: number[]): Promise<void> {
    await Promise.all(attachmentIds.map(id => this.delete(id)))
  },

  // 获取下载链接
  getDownloadUrl(attachmentId: number): string {
    return `${API_BASE_URL}/attachments/${attachmentId}/download`
  },

  // 获取缩略图链接
  getThumbnailUrl(attachmentId: number): string {
    return `${API_BASE_URL}/attachments/${attachmentId}/thumbnail`
  },

  // 检查文件是否为图片类型
  isImageFile(mimeType: string): boolean {
    return mimeType.startsWith('image/')
  },

  // 格式化文件大小
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B'
    
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  // 获取文件类型图标
  getFileTypeIcon(mimeType: string): string {
    if (mimeType.startsWith('image/')) return 'Picture'
    if (mimeType.startsWith('video/')) return 'VideoPlay'
    if (mimeType.startsWith('audio/')) return 'Headphone'
    if (mimeType.includes('pdf')) return 'Document'
    if (mimeType.includes('word') || mimeType.includes('document')) return 'Document'
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return 'Grid'
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return 'Present'
    return 'Document'
  },

  // 验证文件
  async validateFile(file: File, options?: FileProcessingOptions): Promise<AttachmentValidationResult> {
    const formData = new FormData()
    formData.append('file', file)
    if (options) {
      formData.append('options', JSON.stringify(options))
    }
    
    return request<AttachmentValidationResult>('/attachments/validate', {
      method: 'POST',
      body: formData
    })
  },

  // 获取附件统计信息
  async getStats(promptId?: number): Promise<AttachmentStats> {
    const params = promptId ? `?prompt_id=${promptId}` : ''
    return request<AttachmentStats>(`/attachments/stats${params}`)
  },

  // 搜索附件
  async search(params: AttachmentQueryParams): Promise<AttachmentListResponse> {
    const searchParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.set(key, String(value))
      }
    })
    
    const query = searchParams.toString()
    return request<AttachmentListResponse>(`/attachments/search${query ? `?${query}` : ''}`)
  },

  // 更新附件信息
  async update(attachmentId: number, data: Partial<AttachmentInfo>): Promise<AttachmentInfo> {
    return request<AttachmentInfo>(`/attachments/${attachmentId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  },

  // 复制附件到另一个提示词
  async copy(attachmentId: number, targetPromptId: number): Promise<AttachmentInfo> {
    return request<AttachmentInfo>(`/attachments/${attachmentId}/copy`, {
      method: 'POST',
      body: JSON.stringify({ target_prompt_id: targetPromptId })
    })
  },

  // 移动附件到另一个提示词
  async move(attachmentId: number, targetPromptId: number): Promise<AttachmentInfo> {
    return request<AttachmentInfo>(`/attachments/${attachmentId}/move`, {
      method: 'PUT',
      body: JSON.stringify({ target_prompt_id: targetPromptId })
    })
  },

  // 批量更新附件关联
  async batchUpdatePrompt(attachmentIds: number[], promptId: number): Promise<AttachmentInfo[]> {
    return request<AttachmentInfo[]>(`/prompts/${promptId}/attachments/batch-update`, {
      method: 'PUT',
      body: JSON.stringify(attachmentIds)
    })
  }
}