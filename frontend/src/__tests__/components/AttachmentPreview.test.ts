import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AttachmentPreview from '../../components/AttachmentPreview.vue'
import { createMockAttachment } from '../test-utils'

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

describe('AttachmentPreview', () => {
  let mockElMessage: any
  let mockAttachmentApi: any

  beforeEach(async () => {
    vi.clearAllMocks()
    
    // 获取模拟的模块
    const { ElMessage } = await import('element-plus')
    const { attachmentApi } = await import('../../api/attachment')
    
    mockElMessage = ElMessage
    mockAttachmentApi = attachmentApi
    
    // 模拟 DOM 方法
    global.URL.createObjectURL = vi.fn(() => 'mock-url')
    global.URL.revokeObjectURL = vi.fn()
    
    const mockLink = {
      href: '',
      download: '',
      target: '',
      click: vi.fn(),
      remove: vi.fn()
    }
    
    document.createElement = vi.fn((tagName: string) => {
      if (tagName === 'a') {
        return mockLink as any
      }
      return {} as any
    })
    
    document.body.appendChild = vi.fn()
    document.body.removeChild = vi.fn()
    
    global.window.open = vi.fn()
  })

  const createWrapper = (props = {}) => {
    const defaultAttachment = createMockAttachment()
    return mount(AttachmentPreview, {
      props: {
        attachment: defaultAttachment,
        ...props
      },
      global: {
        stubs: {
          'el-image': {
            template: '<div class="el-image"><slot /></div>',
            props: ['src', 'previewSrcList', 'fit', 'previewTeleported']
          },
          'el-icon': {
            template: '<div class="el-icon"><slot /></div>'
          },
          'el-button': {
            template: '<button class="el-button"><slot /></button>',
            props: ['size', 'type', 'loading']
          },
          'el-button-group': {
            template: '<div class="el-button-group"><slot /></div>'
          },
          'el-dialog': {
            template: '<div class="el-dialog" v-if="modelValue"><slot /><slot name="footer" /></div>',
            props: ['modelValue', 'title', 'width', 'beforeClose']
          }
        }
      }
    })
  }

  it('应该正确渲染附件预览组件', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('.attachment-preview').exists()).toBe(true)
  })

  it('应该为图片类型显示图片预览', () => {
    const mockAttachment = createMockAttachment({
      mime_type: 'image/jpeg'
    })
    
    const wrapper = createWrapper({
      attachment: mockAttachment
    })

    const component = wrapper.vm as any
    expect(component.isImage).toBe(true)
    expect(wrapper.find('.image-preview').exists()).toBe(true)
    expect(wrapper.find('.file-preview').exists()).toBe(false)
  })

  it('应该为非图片类型显示文件预览', () => {
    const mockAttachment = createMockAttachment({
      mime_type: 'application/pdf',
      original_filename: 'document.pdf'
    })
    
    const wrapper = createWrapper({
      attachment: mockAttachment
    })

    const component = wrapper.vm as any
    expect(component.isImage).toBe(false)
    expect(wrapper.find('.file-preview').exists()).toBe(true)
    expect(wrapper.find('.image-preview').exists()).toBe(false)
  })

  it('应该正确识别可预览的文件类型', async () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any

    // 测试图片类型
    await wrapper.setProps({ 
      attachment: createMockAttachment({ mime_type: 'image/jpeg' }) 
    })
    expect(component.canPreview).toBe(true)

    // 测试视频类型
    await wrapper.setProps({ 
      attachment: createMockAttachment({ mime_type: 'video/mp4' }) 
    })
    expect(component.canPreview).toBe(true)

    // 测试音频类型
    await wrapper.setProps({ 
      attachment: createMockAttachment({ mime_type: 'audio/mp3' }) 
    })
    expect(component.canPreview).toBe(true)

    // 测试PDF类型
    await wrapper.setProps({ 
      attachment: createMockAttachment({ mime_type: 'application/pdf' }) 
    })
    expect(component.canPreview).toBe(true)

    // 测试文本类型
    await wrapper.setProps({ 
      attachment: createMockAttachment({ mime_type: 'text/plain' }) 
    })
    expect(component.canPreview).toBe(true)

    // 测试不支持预览的类型
    await wrapper.setProps({ 
      attachment: createMockAttachment({ mime_type: 'application/zip' }) 
    })
    expect(component.canPreview).toBe(false)
  })

  it('应该为不同文件类型返回正确的文本描述', () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any

    expect(component.getFileTypeText('image/jpeg')).toBe('图片')
    expect(component.getFileTypeText('video/mp4')).toBe('视频')
    expect(component.getFileTypeText('audio/mp3')).toBe('音频')
    expect(component.getFileTypeText('application/pdf')).toBe('PDF')
    expect(component.getFileTypeText('application/msword')).toBe('文档')
    expect(component.getFileTypeText('text/plain')).toBe('文本')
    expect(component.getFileTypeText('application/zip')).toBe('文件')
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

  it('应该正确格式化日期', () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any
    const now = new Date()
    
    // 测试今天的日期
    const today = now.toISOString()
    expect(component.formatDate(today)).toContain('今天')

    // 测试昨天的日期
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
    expect(component.formatDate(yesterday)).toBe('昨天')

    // 测试几天前的日期
    const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString()
    expect(component.formatDate(threeDaysAgo)).toBe('3天前')

    // 测试一周前的日期
    const oneWeekAgo = new Date(now.getTime() - 8 * 24 * 60 * 60 * 1000).toISOString()
    expect(component.formatDate(oneWeekAgo)).toMatch(/\d{4}\/\d{1,2}\/\d{1,2}/)
  })

  it('应该处理文件下载', async () => {
    mockAttachmentApi.getDownloadUrl.mockReturnValue('http://example.com/download/1')

    const mockAttachment = createMockAttachment()
    const wrapper = createWrapper({
      attachment: mockAttachment
    })

    const component = wrapper.vm as any
    await component.downloadFile()

    expect(mockAttachmentApi.getDownloadUrl).toHaveBeenCalledWith(mockAttachment.id)
    expect(wrapper.emitted('download')).toBeTruthy()
    expect(mockElMessage.success).toHaveBeenCalledWith('开始下载文件')
  })

  it('应该处理下载错误', async () => {
    mockAttachmentApi.getDownloadUrl.mockImplementation(() => {
      throw new Error('下载失败')
    })

    const wrapper = createWrapper()
    const component = wrapper.vm as any
    await component.downloadFile()

    expect(mockElMessage.error).toHaveBeenCalledWith('下载失败：下载失败')
  })

  it('应该处理文件预览', async () => {
    mockAttachmentApi.getDownloadUrl.mockReturnValue('http://example.com/download/1')

    const mockAttachment = createMockAttachment({
      mime_type: 'application/pdf'
    })
    
    const wrapper = createWrapper({
      attachment: mockAttachment
    })

    const component = wrapper.vm as any
    await component.previewFile()

    expect(global.window.open).toHaveBeenCalledWith('http://example.com/download/1', '_blank')
    expect(wrapper.emitted('preview')).toBeTruthy()
  })

  it('应该处理删除确认', async () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any
    await component.confirmDelete()

    expect(component.showDeleteDialog).toBe(true)
  })

  it('应该处理附件删除', async () => {
    mockAttachmentApi.delete.mockResolvedValue(undefined)

    const mockAttachment = createMockAttachment()
    const wrapper = createWrapper({
      attachment: mockAttachment
    })

    const component = wrapper.vm as any
    await component.deleteAttachment()

    expect(mockAttachmentApi.delete).toHaveBeenCalledWith(mockAttachment.id)
    expect(component.showDeleteDialog).toBe(false)
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')?.[0]).toEqual([mockAttachment.id])
    expect(mockElMessage.success).toHaveBeenCalledWith('附件删除成功')
  })

  it('应该处理删除错误', async () => {
    mockAttachmentApi.delete.mockRejectedValue(new Error('删除失败'))

    const wrapper = createWrapper()
    const component = wrapper.vm as any
    await component.deleteAttachment()

    expect(mockElMessage.error).toHaveBeenCalledWith('删除失败：删除失败')
  })

  it('应该支持网格视图模式', () => {
    const wrapper = createWrapper({
      isGridView: true
    })

    expect(wrapper.find('.attachment-preview.is-grid-view').exists()).toBe(true)
  })

  it('应该在删除过程中阻止对话框关闭', () => {
    const wrapper = createWrapper()
    const component = wrapper.vm as any
    const mockDone = vi.fn()

    // 测试非删除状态下可以关闭
    component.isDeleting = false
    component.handleDeleteDialogClose(mockDone)
    expect(mockDone).toHaveBeenCalled()

    // 测试删除状态下不能关闭
    mockDone.mockClear()
    component.isDeleting = true
    component.handleDeleteDialogClose(mockDone)
    expect(mockDone).not.toHaveBeenCalled()
  })

  it('应该显示图片的分辨率信息', () => {
    const mockAttachment = createMockAttachment({
      mime_type: 'image/jpeg',
      metadata: {
        width: 1920,
        height: 1080
      }
    })

    const wrapper = createWrapper({
      attachment: mockAttachment
    })

    // 验证图片信息显示
    expect(wrapper.html()).toContain('1920×1080')
  })
})