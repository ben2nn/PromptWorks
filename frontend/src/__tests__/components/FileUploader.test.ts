import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FileUploader from '../../components/FileUploader.vue'
import { MediaType } from '../../types/prompt'
import { createMockFile } from '../test-utils'

vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    }
  }
})

vi.mock('../../api/attachment', () => ({
  attachmentApi: {
    upload: vi.fn(),
    delete: vi.fn(),
    getDownloadUrl: vi.fn(),
    getThumbnailUrl: vi.fn()
  }
}))

describe('FileUploader', () => {
  let mockElMessage: any
  let mockAttachmentApi: any

  beforeEach(async () => {
    vi.clearAllMocks()
    
    // 获取模拟的模块
    const { ElMessage } = await import('element-plus')
    const { attachmentApi } = await import('../../api/attachment')
    
    mockElMessage = ElMessage
    mockAttachmentApi = attachmentApi
  })

  const createWrapper = (props = {}) => {
    return mount(FileUploader, {
      props: {
        promptId: 1,
        mediaType: MediaType.IMAGE,
        ...props
      },
      global: {
        stubs: {
          'el-upload': {
            template: '<div class="el-upload"><slot /></div>',
            props: ['action', 'beforeUpload', 'onSuccess', 'onError', 'fileList', 'accept', 'multiple', 'disabled'],
            methods: {
              clearFiles: vi.fn()
            }
          },
          'el-icon': {
            template: '<div class="el-icon"><slot /></div>'
          },
          'el-button': {
            template: '<button class="el-button"><slot /></button>',
            props: ['size', 'type', 'text']
          },
          'el-progress': {
            template: '<div class="el-progress"></div>',
            props: ['percentage', 'strokeWidth', 'showText']
          }
        }
      }
    })
  }

  it('应该正确渲染文件上传组件', () => {
    const wrapper = createWrapper()

    expect(wrapper.find('.file-uploader').exists()).toBe(true)
    expect(wrapper.find('.upload-dragger').exists()).toBe(true)
    expect(wrapper.find('.upload-content').exists()).toBe(true)
  })

  it('应该根据媒体类型显示正确的接受文件类型', () => {
    const wrapper = createWrapper({
      mediaType: MediaType.IMAGE
    })

    const component = wrapper.vm as any
    expect(component.acceptedTypes).toBe('.jpg,.jpeg,.png,.gif,.webp')
    expect(component.acceptedTypesText).toBe('JPG、PNG、GIF、WebP 格式图片')
  })

  it('应该为不同媒体类型配置正确的文件类型', () => {
    // 测试图片类型
    const imageWrapper = createWrapper({ mediaType: MediaType.IMAGE })
    expect((imageWrapper.vm as any).acceptedTypes).toBe('.jpg,.jpeg,.png,.gif,.webp')

    // 测试文档类型
    const docWrapper = createWrapper({ mediaType: MediaType.DOCUMENT })
    expect((docWrapper.vm as any).acceptedTypes).toBe('.pdf,.doc,.docx,.txt,.md')

    // 测试音频类型
    const audioWrapper = createWrapper({ mediaType: MediaType.AUDIO })
    expect((audioWrapper.vm as any).acceptedTypes).toBe('.mp3,.wav,.ogg,.m4a')

    // 测试视频类型
    const videoWrapper = createWrapper({ mediaType: MediaType.VIDEO })
    expect((videoWrapper.vm as any).acceptedTypes).toBe('.mp4,.avi,.mov,.wmv')
  })

  it('应该正确格式化文件大小显示', () => {
    const wrapper = createWrapper({
      maxSize: 10 * 1024 * 1024 // 10MB
    })

    const component = wrapper.vm as any
    expect(component.maxSizeText).toBe('10MB')
  })

  it('应该验证文件大小', () => {
    const wrapper = createWrapper({
      maxSize: 1024 // 1KB
    })

    const component = wrapper.vm as any
    
    // 创建超大文件
    const largeFile = createMockFile('large.jpg', 2048, 'image/jpeg')
    const result = component.beforeUpload(largeFile)

    expect(result).toBe(false)
    expect(mockElMessage.error).toHaveBeenCalledWith('文件大小不能超过 1KB')
  })

  it('应该验证文件类型', () => {
    const wrapper = createWrapper({
      mediaType: MediaType.IMAGE
    })

    const component = wrapper.vm as any
    
    // 测试正确的图片文件
    const validFile = createMockFile('test.jpg', 1024, 'image/jpeg')
    expect(component.beforeUpload(validFile)).toBe(true)

    // 测试错误的文件类型
    const invalidFile = createMockFile('test.txt', 1024, 'text/plain')
    expect(component.beforeUpload(invalidFile)).toBe(false)
    expect(mockElMessage.error).toHaveBeenCalledWith('请选择正确的文件类型：JPG、PNG、GIF、WebP 格式图片')
  })

  it('应该正确验证不同媒体类型的文件', () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any

    // 测试图片文件验证
    expect(component.validateFileType(createMockFile('test.jpg', 1024, 'image/jpeg'), MediaType.IMAGE)).toBe(true)
    expect(component.validateFileType(createMockFile('test.png', 1024, 'image/png'), MediaType.IMAGE)).toBe(true)
    expect(component.validateFileType(createMockFile('test.txt', 1024, 'text/plain'), MediaType.IMAGE)).toBe(false)

    // 测试文档文件验证
    expect(component.validateFileType(createMockFile('test.pdf', 1024, 'application/pdf'), MediaType.DOCUMENT)).toBe(true)
    expect(component.validateFileType(createMockFile('test.doc', 1024, 'application/msword'), MediaType.DOCUMENT)).toBe(true)
    expect(component.validateFileType(createMockFile('test.jpg', 1024, 'image/jpeg'), MediaType.DOCUMENT)).toBe(false)

    // 测试音频文件验证
    expect(component.validateFileType(createMockFile('test.mp3', 1024, 'audio/mpeg'), MediaType.AUDIO)).toBe(true)
    expect(component.validateFileType(createMockFile('test.wav', 1024, 'audio/wav'), MediaType.AUDIO)).toBe(true)
    expect(component.validateFileType(createMockFile('test.jpg', 1024, 'image/jpeg'), MediaType.AUDIO)).toBe(false)

    // 测试视频文件验证
    expect(component.validateFileType(createMockFile('test.mp4', 1024, 'video/mp4'), MediaType.VIDEO)).toBe(true)
    expect(component.validateFileType(createMockFile('test.avi', 1024, 'video/avi'), MediaType.VIDEO)).toBe(true)
    expect(component.validateFileType(createMockFile('test.jpg', 1024, 'image/jpeg'), MediaType.VIDEO)).toBe(false)
  })

  it('应该正确格式化文件大小', () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any

    expect(component.formatFileSize(0)).toBe('0 B')
    expect(component.formatFileSize(512)).toBe('512 B')
    expect(component.formatFileSize(1024)).toBe('1 KB')
    expect(component.formatFileSize(1536)).toBe('1.5 KB')
    expect(component.formatFileSize(1024 * 1024)).toBe('1 MB')
    expect(component.formatFileSize(1.5 * 1024 * 1024)).toBe('1.5 MB')
    expect(component.formatFileSize(1024 * 1024 * 1024)).toBe('1 GB')
  })

  it('应该处理上传成功', async () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any
    const mockResponse = { id: 1, filename: 'test.jpg' }
    const mockFile = { name: 'test.jpg', size: 1024 }

    await component.handleSuccess(mockResponse, mockFile)

    expect(component.isUploading).toBe(false)
    expect(component.uploadProgress).toBe(0)
    expect(mockElMessage.success).toHaveBeenCalledWith('文件上传成功')
    expect(wrapper.emitted('upload-success')).toBeTruthy()
    expect(wrapper.emitted('upload-success')?.[0]).toEqual([mockResponse])
  })

  it('应该处理上传错误', async () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any
    const mockError = new Error('上传失败')

    await component.handleError(mockError)

    expect(component.isUploading).toBe(false)
    expect(component.uploadProgress).toBe(0)
    expect(mockElMessage.error).toHaveBeenCalledWith('文件上传失败：上传失败')
    expect(wrapper.emitted('upload-error')).toBeTruthy()
    expect(wrapper.emitted('upload-error')?.[0]).toEqual([mockError])
  })

  it('应该处理上传进度', async () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any
    const mockEvent = { percent: 50 }

    await component.handleProgress(mockEvent)

    expect(component.isUploading).toBe(true)
    expect(component.uploadProgress).toBe(50)
  })

  it('应该支持清空文件列表', async () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any
    
    // 添加一些文件到列表
    component.fileList = [
      { name: 'file1.jpg', size: 1024 },
      { name: 'file2.jpg', size: 2048 }
    ]

    await component.clearFiles()

    expect(component.fileList).toHaveLength(0)
    expect(wrapper.emitted('files-change')).toBeTruthy()
  })

  it('应该支持移除单个文件', async () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any
    
    // 添加一些文件到列表
    component.fileList = [
      { name: 'file1.jpg', size: 1024 },
      { name: 'file2.jpg', size: 2048 }
    ]

    await component.removeFile(0)

    expect(component.fileList).toHaveLength(1)
    expect(component.fileList[0].name).toBe('file2.jpg')
    expect(wrapper.emitted('files-change')).toBeTruthy()
  })

  it('应该支持自定义上传方法', async () => {
    mockAttachmentApi.upload.mockResolvedValue({ id: 1, filename: 'test.jpg' })

    const wrapper = createWrapper()
    const component = wrapper.vm as any
    const mockFile = createMockFile('test.jpg', 1024, 'image/jpeg')

    const result = await component.customUpload(mockFile)

    expect(mockAttachmentApi.upload).toHaveBeenCalledWith(1, mockFile)
    expect(result).toEqual({ id: 1, filename: 'test.jpg' })
  })

  it('应该在缺少 promptId 时抛出错误', async () => {
    const wrapper = createWrapper({
      promptId: undefined
    })

    const component = wrapper.vm as any
    const mockFile = createMockFile('test.jpg', 1024, 'image/jpeg')

    await expect(component.customUpload(mockFile)).rejects.toThrow('缺少 promptId 参数')
  })
})