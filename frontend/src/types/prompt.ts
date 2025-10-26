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

// 媒体类型枚举
export enum MediaType {
  TEXT = 'text',
  IMAGE = 'image',
  DOCUMENT = 'document',
  AUDIO = 'audio',
  VIDEO = 'video'
}

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

// 文件上传状态枚举
export enum UploadStatus {
  PENDING = 'pending',
  UPLOADING = 'uploading',
  SUCCESS = 'success',
  ERROR = 'error',
  CANCELLED = 'cancelled'
}

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
