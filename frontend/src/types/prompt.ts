export interface PromptTag {
  id: number
  name: string
  color: string
  created_at: string
  updated_at: string
}

export interface PromptClass {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface PromptVersion {
  id: number
  prompt_id: number
  version: string
  content: string
  contentzh?: string | null
  created_at: string
  updated_at: string
}

// 媒体类型定义
export type MediaType = 'text' | 'image' | 'document' | 'audio' | 'video'

export const MediaType = {
  TEXT: 'text' as const,
  IMAGE: 'image' as const,
  DOCUMENT: 'document' as const,
  AUDIO: 'audio' as const,
  VIDEO: 'video' as const
} as const

// 媒体类型信息接口
export interface MediaTypeInfo {
  value: MediaType
  label: string
  description: string
  icon: string
  acceptedTypes: string[]
  maxFileSize: number
}

// 附件元数据接口
export interface AttachmentMetadata {
  // 图片元数据
  width?: number
  height?: number
  format?: string

  // 文档元数据
  pages?: number
  author?: string
  title?: string

  // 音频/视频元数据
  duration?: number
  bitrate?: number
  codec?: string

  // 通用元数据
  [key: string]: any
}

// 附件信息接口
export interface AttachmentInfo {
  id: number
  prompt_id: number
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  thumbnail_url?: string
  download_url: string
  metadata?: AttachmentMetadata
  created_at: string
  updated_at: string
}

// 附件创建请求接口
export interface AttachmentCreateRequest {
  prompt_id: number
  file: File
}

// 附件更新请求接口
export interface AttachmentUpdateRequest {
  filename?: string
  metadata?: AttachmentMetadata
}

// 文件上传状态定义
export type UploadStatus = 'pending' | 'uploading' | 'success' | 'error' | 'cancelled'

export const UploadStatus = {
  PENDING: 'pending' as const,
  UPLOADING: 'uploading' as const,
  SUCCESS: 'success' as const,
  ERROR: 'error' as const,
  CANCELLED: 'cancelled' as const
} as const

// 文件上传进度接口
export interface FileUploadProgress {
  file: File
  progress: number
  status: UploadStatus
  error?: string
  attachment?: AttachmentInfo
}

// 批量操作结果接口
export interface BatchOperationResult<T> {
  success: T[]
  failed: Array<{
    item: any
    error: string
  }>
  total: number
  successCount: number
  failedCount: number
}

export interface Prompt {
  id: number
  name: string
  description: string | null
  author: string | null
  prompt_class: PromptClass
  current_version: PromptVersion | null
  versions: PromptVersion[]
  tags: PromptTag[]
  media_type: MediaType
  attachments: AttachmentInfo[]
  created_at: string
  updated_at: string
}
