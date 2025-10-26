import { mount, VueWrapper } from '@vue/test-utils'
import { vi } from 'vitest'
import { MediaType, AttachmentInfo } from '../types/prompt'

// 创建模拟文件
export const createMockFile = (
  name: string = 'test.jpg',
  size: number = 1024,
  type: string = 'image/jpeg'
): File => {
  const file = new File([''], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

// 创建模拟附件信息
export const createMockAttachment = (overrides: Partial<AttachmentInfo> = {}): AttachmentInfo => ({
  id: 1,
  prompt_id: 1,
  filename: 'test-file.jpg',
  original_filename: 'test-file.jpg',
  file_size: 1024,
  mime_type: 'image/jpeg',
  download_url: 'http://example.com/download/1',
  thumbnail_url: 'http://example.com/thumbnail/1',
  metadata: {
    width: 800,
    height: 600
  },
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  ...overrides
})

// 等待 Vue 组件更新
export const nextTick = () => new Promise(resolve => setTimeout(resolve, 0))

// 模拟 URL.createObjectURL
export const mockCreateObjectURL = () => {
  global.URL.createObjectURL = vi.fn(() => 'mock-url')
  global.URL.revokeObjectURL = vi.fn()
}

// 模拟 document.createElement 和 appendChild
export const mockDownloadLink = () => {
  const mockLink = {
    href: '',
    download: '',
    target: '',
    click: vi.fn(),
    remove: vi.fn()
  }
  
  const originalCreateElement = document.createElement
  document.createElement = vi.fn((tagName: string) => {
    if (tagName === 'a') {
      return mockLink as any
    }
    return originalCreateElement.call(document, tagName)
  })
  
  const mockAppendChild = vi.fn()
  const mockRemoveChild = vi.fn()
  document.body.appendChild = mockAppendChild
  document.body.removeChild = mockRemoveChild
  
  return { mockLink, mockAppendChild, mockRemoveChild }
}

// 全局测试设置
export const setupGlobalMocks = () => {
  // 模拟 URL API
  mockCreateObjectURL()
}

// 模拟 Element Plus 消息组件
export const createMockElMessage = () => ({
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
  info: vi.fn()
})

// 模拟附件 API
export const createMockAttachmentApi = () => ({
  upload: vi.fn(),
  delete: vi.fn(),
  getDownloadUrl: vi.fn(),
  getThumbnailUrl: vi.fn()
})

// 清理模拟
export const cleanupMocks = () => {
  vi.clearAllMocks()
}

// 测试组件挂载的通用选项
export const getDefaultMountOptions = () => ({
  global: {
    stubs: {
      'el-icon': true,
      'el-button': true,
      'el-button-group': true,
      'el-select': true,
      'el-option': true,
      'el-upload': true,
      'el-image': true,
      'el-progress': true,
      'el-dialog': true
    }
  }
})