import { MediaType } from './prompt'

// 文件验证规则接口
export interface FileValidationRule {
  maxSize: number // 最大文件大小（字节）
  allowedTypes: string[] // 允许的 MIME 类型
  allowedExtensions: string[] // 允许的文件扩展名
}

// 媒体类型配置接口
export interface MediaTypeConfig {
  type: MediaType
  label: string
  description: string
  icon: string
  validation: FileValidationRule
  supportsThumbnail: boolean
  supportsPreview: boolean
}

// 文件上传配置接口
export interface UploadConfig {
  maxFileSize: number
  maxFiles: number
  allowedTypes: string[]
  chunkSize?: number
  timeout?: number
}

// 缩略图配置接口
export interface ThumbnailConfig {
  width: number
  height: number
  quality: number
  format: 'jpeg' | 'png' | 'webp'
}

// 附件预览配置接口
export interface PreviewConfig {
  enableImagePreview: boolean
  enableVideoPreview: boolean
  enableAudioPreview: boolean
  enableDocumentPreview: boolean
  maxPreviewSize: number
}

// 文件处理选项接口
export interface FileProcessingOptions {
  generateThumbnail: boolean
  extractMetadata: boolean
  validateContent: boolean
  thumbnailConfig?: ThumbnailConfig
}

// 附件查询参数接口
export interface AttachmentQueryParams {
  prompt_id?: number
  mime_type?: string
  file_size_min?: number
  file_size_max?: number
  created_after?: string
  created_before?: string
  limit?: number
  offset?: number
  sort_by?: 'created_at' | 'file_size' | 'filename'
  sort_order?: 'asc' | 'desc'
}

// 附件统计信息接口
export interface AttachmentStats {
  total_count: number
  total_size: number
  by_type: Record<string, {
    count: number
    size: number
  }>
  by_prompt: Record<number, {
    count: number
    size: number
  }>
}

// 存储配置接口
export interface StorageConfig {
  type: 'local' | 's3' | 'oss'
  basePath: string
  baseUrl: string
  maxStorageSize?: number
  cleanupPolicy?: {
    enabled: boolean
    maxAge: number // 天数
    maxSize: number // 字节
  }
}

// 错误类型常量
export const AttachmentError = {
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  INVALID_FILE_TYPE: 'INVALID_FILE_TYPE',
  UPLOAD_FAILED: 'UPLOAD_FAILED',
  DOWNLOAD_FAILED: 'DOWNLOAD_FAILED',
  DELETE_FAILED: 'DELETE_FAILED',
  NOT_FOUND: 'NOT_FOUND',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  STORAGE_FULL: 'STORAGE_FULL',
  NETWORK_ERROR: 'NETWORK_ERROR',
  INVALID_CONTENT: 'INVALID_CONTENT'
} as const

export type AttachmentErrorType = typeof AttachmentError[keyof typeof AttachmentError]

// 附件错误详情接口
export interface AttachmentErrorDetail {
  code: AttachmentErrorType
  message: string
  details?: Record<string, any>
  file?: string
  timestamp: string
}

// 默认媒体类型配置
export const DEFAULT_MEDIA_TYPE_CONFIGS = {
  [MediaType.TEXT]: {
    type: MediaType.TEXT,
    label: '文本',
    description: '纯文本内容',
    icon: 'Document',
    validation: {
      maxSize: 0,
      allowedTypes: [],
      allowedExtensions: []
    },
    supportsThumbnail: false,
    supportsPreview: true
  },
  [MediaType.IMAGE]: {
    type: MediaType.IMAGE,
    label: '图片',
    description: '图片文件（JPEG、PNG、GIF、WebP）',
    icon: 'Picture',
    validation: {
      maxSize: 10 * 1024 * 1024, // 10MB
      allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
      allowedExtensions: ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    },
    supportsThumbnail: true,
    supportsPreview: true
  },
  [MediaType.DOCUMENT]: {
    type: MediaType.DOCUMENT,
    label: '文档',
    description: '文档文件（PDF、Word、Excel、PowerPoint）',
    icon: 'Document',
    validation: {
      maxSize: 50 * 1024 * 1024, // 50MB
      allowedTypes: [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      ],
      allowedExtensions: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
    },
    supportsThumbnail: true,
    supportsPreview: false
  },
  [MediaType.AUDIO]: {
    type: MediaType.AUDIO,
    label: '音频',
    description: '音频文件（MP3、WAV、AAC、OGG）',
    icon: 'Headphone',
    validation: {
      maxSize: 100 * 1024 * 1024, // 100MB
      allowedTypes: ['audio/mpeg', 'audio/wav', 'audio/aac', 'audio/ogg'],
      allowedExtensions: ['.mp3', '.wav', '.aac', '.ogg']
    },
    supportsThumbnail: false,
    supportsPreview: true
  },
  [MediaType.VIDEO]: {
    type: MediaType.VIDEO,
    label: '视频',
    description: '视频文件（MP4、AVI、MOV、WebM）',
    icon: 'VideoPlay',
    validation: {
      maxSize: 500 * 1024 * 1024, // 500MB
      allowedTypes: ['video/mp4', 'video/avi', 'video/quicktime', 'video/webm'],
      allowedExtensions: ['.mp4', '.avi', '.mov', '.webm']
    },
    supportsThumbnail: true,
    supportsPreview: true
  }
} as const

// 默认上传配置
export const DEFAULT_UPLOAD_CONFIG: UploadConfig = {
  maxFileSize: 100 * 1024 * 1024, // 100MB
  maxFiles: 10,
  allowedTypes: [
    // 图片
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    // 文档
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    // 音频
    'audio/mpeg', 'audio/wav', 'audio/aac', 'audio/ogg',
    // 视频
    'video/mp4', 'video/avi', 'video/quicktime', 'video/webm'
  ],
  chunkSize: 1024 * 1024, // 1MB
  timeout: 30000 // 30秒
}

// 默认缩略图配置
export const DEFAULT_THUMBNAIL_CONFIG: ThumbnailConfig = {
  width: 200,
  height: 200,
  quality: 85,
  format: 'jpeg'
}

// 默认预览配置
export const DEFAULT_PREVIEW_CONFIG: PreviewConfig = {
  enableImagePreview: true,
  enableVideoPreview: true,
  enableAudioPreview: true,
  enableDocumentPreview: false,
  maxPreviewSize: 10 * 1024 * 1024 // 10MB
}