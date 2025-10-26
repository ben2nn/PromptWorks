/**
 * 媒体类型和附件功能前端集成测试
 * 
 * 测试完整的前端工作流程，包括：
 * - 完整的文件上传流程
 * - 附件管理功能
 * - 媒体类型切换
 * - 组件间的交互
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { MediaType, AttachmentInfo, PromptInfo } from '../../types/prompt'
import { createMockFile, createMockAttachment, setupGlobalMocks, cleanupMocks } from '../test-utils'

// 模拟 API
vi.mock('../../api/attachment', () => ({
  attachmentApi: {
    upload: vi.fn(),
    list: vi.fn(),
    delete: vi.fn(),
    getDownloadUrl: vi.fn(),
    getThumbnailUrl: vi.fn()
  }
}))

vi.mock('../../api/prompt', () => ({
  promptApi: {
    get: vi.fn(),
    update: vi.fn(),
    list: vi.fn()
  }
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn()
    }
  }
})

// 导入组件
import PromptEditor from '../../components/PromptEditor.vue'
import FileUploader from '../../components/FileUploader.vue'
import AttachmentPreview from '../../components/AttachmentPreview.vue'
import MediaTypeSelector from '../../components/MediaTypeSelector.vue'

describe('媒体类型和附件功能集成测试', () => {
  let mockAttachmentApi: any
  let mockPromptApi: any
  let mockElMessage: any
  let mockElMessageBox: any

  beforeEach(async () => {
    setupGlobalMocks()
    vi.clearAllMocks()
    
    // 获取模拟的模块
    const { attachmentApi } = await import('../../api/attachment')
    const { promptApi } = await import('../../api/prompt')
    const { ElMessage, ElMessageBox } = await import('element-plus')
    
    mockAttachmentApi = attachmentApi
    mockPromptApi = promptApi
    mockElMessage = ElMessage
    mockElMessageBox = ElMessageBox
  })

  afterEach(() => {
    cleanupMocks()
  })

  const createPromptEditorWrapper = (props = {}) => {
    return mount(PromptEditor, {
      props: {
        promptId: 1,
        ...props
      },
      global: {
        stubs: {
          'el-form': {
            template: '<form class="el-form"><slot /></form>',
            props: ['model', 'labelWidth']
          },
          'el-form-item': {
            template: '<div class="el-form-item"><label><slot name="label" /></label><slot /></div>',
            props: ['label', 'required']
          },
          'el-input': {
            template: '<input class="el-input" v-model="modelValue" />',
            props: ['modelValue', 'type', 'rows', 'placeholder'],
            emits: ['update:modelValue']
          },
          'el-button': {
            template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>',
            props: ['type', 'loading', 'disabled']
          },
          'MediaTypeSelector': {
            template: '<div class="media-type-selector" @change="$emit(\'change\', $event)"></div>',
            props: ['modelValue'],
            emits: ['change', 'update:modelValue']
          },
          'FileUploader': {
            template: '<div class="file-uploader" @upload-success="$emit(\'upload-success\', $event)"></div>',
            props: ['promptId', 'mediaType'],
            emits: ['upload-success']
          },
          'AttachmentPreview': {
            template: '<div class="attachment-preview" @delete="$emit(\'delete\', $event)"></div>',
            props: ['attachment'],
            emits: ['delete']
          }
        }
      }
    })
  }

  describe('完整的文件上传流程测试', () => {
    it('应该完成从选择媒体类型到上传文件的完整流程', async () => {
      // 模拟 API 响应
      const mockPrompt: PromptInfo = {
        id: 1,
        name: '测试提示词',
        description: '测试描述',
        content: '初始内容',
        media_type: MediaType.TEXT,
        class_id: 1,
        attachments: [],
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      }

      const mockAttachment: AttachmentInfo = createMockAttachment({
        id: 1,
        prompt_id: 1,
        filename: 'uploaded-image.jpg',
        original_filename: 'test-image.jpg',
        mime_type: 'image/jpeg'
      })

      mockPromptApi.get.mockResolvedValue(mockPrompt)
      mockPromptApi.update.mockResolvedValue({ ...mockPrompt, media_type: MediaType.IMAGE })
      mockAttachmentApi.upload.mockResolvedValue(mockAttachment)
      mockAttachmentApi.list.mockResolvedValue([mockAttachment])

      const wrapper = createPromptEditorWrapper()
      await nextTick()

      // 步骤 1: 验证初始状态（文本类型）
      expect(wrapper.vm.form.media_type).toBe(MediaType.TEXT)
      expect(wrapper.find('.file-uploader').exists()).toBe(false)

      // 步骤 2: 切换到图片类型
      const mediaTypeSelector = wrapper.findComponent({ name: 'MediaTypeSelector' })
      await mediaTypeSelector.vm.$emit('change', MediaType.IMAGE)
      await nextTick()

      expect(wrapper.vm.form.media_type).toBe(MediaType.IMAGE)
      expect(wrapper.find('.file-uploader').exists()).toBe(true)

      // 步骤 3: 模拟文件上传
      const fileUploader = wrapper.findComponent({ name: 'FileUploader' })
      await fileUploader.vm.$emit('upload-success', mockAttachment)
      await nextTick()

      // 步骤 4: 验证附件列表更新
      expect(wrapper.vm.attachments).toContain(mockAttachment)
      expect(mockElMessage.success).toHaveBeenCalledWith('文件上传成功')

      // 步骤 5: 验证保存提示词
      const saveButton = wrapper.find('.el-button')
      await saveButton.trigger('click')
      await nextTick()

      expect(mockPromptApi.update).toHaveBeenCalledWith(1, expect.objectContaining({
        media_type: MediaType.IMAGE
      }))
    })

    it('应该处理上传过程中的错误', async () => {
      const mockPrompt: PromptInfo = {
        id: 1,
        name: '测试提示词',
        description: '测试描述',
        content: '',
        media_type: MediaType.IMAGE,
        class_id: 1,
        attachments: [],
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      }

      mockPromptApi.get.mockResolvedValue(mockPrompt)
      mockAttachmentApi.upload.mockRejectedValue(new Error('上传失败'))

      const wrapper = createPromptEditorWrapper()
      await nextTick()

      // 模拟上传错误
      const fileUploader = wrapper.findComponent({ name: 'FileUploader' })
      await fileUploader.vm.$emit('upload-error', new Error('上传失败'))
      await nextTick()

      expect(mockElMessage.error).toHaveBeenCalledWith('文件上传失败：上传失败')
    })
  })

  describe('附件管理功能测试', () => {
    it('应该完成附件的增删改查操作', async () => {
      const mockAttachments: AttachmentInfo[] = [
        createMockAttachment({ id: 1, filename: 'image1.jpg' }),
        createMockAttachment({ id: 2, filename: 'image2.png' }),
        createMockAttachment({ id: 3, filename: 'document.pdf', mime_type: 'application/pdf' })
      ]

      const mockPrompt: PromptInfo = {
        id: 1,
        name: '测试提示词',
        description: '测试描述',
        content: '',
        media_type: MediaType.IMAGE,
        class_id: 1,
        attachments: mockAttachments,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      }

      mockPromptApi.get.mockResolvedValue(mockPrompt)
      mockAttachmentApi.list.mockResolvedValue(mockAttachments)
      mockAttachmentApi.delete.mockResolvedValue(undefined)

      const wrapper = createPromptEditorWrapper()
      await nextTick()

      // 步骤 1: 验证附件列表显示
      expect(wrapper.vm.attachments).toHaveLength(3)
      const attachmentPreviews = wrapper.findAllComponents({ name: 'AttachmentPreview' })
      expect(attachmentPreviews).toHaveLength(3)

      // 步骤 2: 删除附件
      mockElMessageBox.confirm.mockResolvedValue('confirm')
      
      const firstAttachment = attachmentPreviews[0]
      await firstAttachment.vm.$emit('delete', 1)
      await nextTick()

      expect(mockAttachmentApi.delete).toHaveBeenCalledWith(1)
      expect(wrapper.vm.attachments).toHaveLength(2)
      expect(mockElMessage.success).toHaveBeenCalledWith('附件删除成功')

      // 步骤 3: 添加新附件
      const newAttachment = createMockAttachment({ id: 4, filename: 'new-image.jpg' })
      mockAttachmentApi.upload.mockResolvedValue(newAttachment)

      const fileUploader = wrapper.findComponent({ name: 'FileUploader' })
      await fileUploader.vm.$emit('upload-success', newAttachment)
      await nextTick()

      expect(wrapper.vm.attachments).toHaveLength(3)
      expect(wrapper.vm.attachments).toContain(newAttachment)
    })
  })

  describe('媒体类型切换测试', () => {
    it('应该正确处理不同媒体类型之间的切换', async () => {
      const mockPrompt: PromptInfo = {
        id: 1,
        name: '测试提示词',
        description: '测试描述',
        content: '原始文本内容',
        media_type: MediaType.TEXT,
        class_id: 1,
        attachments: [],
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      }

      mockPromptApi.get.mockResolvedValue(mockPrompt)
      mockPromptApi.update.mockImplementation((id, data) => 
        Promise.resolve({ ...mockPrompt, ...data })
      )

      const wrapper = createPromptEditorWrapper()
      await nextTick()

      // 步骤 1: 验证初始状态（文本类型）
      expect(wrapper.vm.form.media_type).toBe(MediaType.TEXT)
      expect(wrapper.find('.file-uploader').exists()).toBe(false)

      // 步骤 2: 切换到图片类型
      const mediaTypeSelector = wrapper.findComponent({ name: 'MediaTypeSelector' })
      await mediaTypeSelector.vm.$emit('change', MediaType.IMAGE)
      await nextTick()

      expect(wrapper.vm.form.media_type).toBe(MediaType.IMAGE)
      expect(wrapper.find('.file-uploader').exists()).toBe(true)

      // 步骤 3: 切换到文档类型
      await mediaTypeSelector.vm.$emit('change', MediaType.DOCUMENT)
      await nextTick()

      expect(wrapper.vm.form.media_type).toBe(MediaType.DOCUMENT)
      expect(wrapper.find('.file-uploader').exists()).toBe(true)

      // 步骤 4: 切换回文本类型
      await mediaTypeSelector.vm.$emit('change', MediaType.TEXT)
      await nextTick()

      expect(wrapper.vm.form.media_type).toBe(MediaType.TEXT)
      expect(wrapper.find('.file-uploader').exists()).toBe(false)
    })
  })

  describe('错误处理和边界情况测试', () => {
    it('应该处理 API 调用失败的情况', async () => {
      // 模拟获取提示词失败
      mockPromptApi.get.mockRejectedValue(new Error('网络错误'))

      const wrapper = createPromptEditorWrapper()
      await nextTick()

      expect(mockElMessage.error).toHaveBeenCalledWith('加载提示词失败：网络错误')
    })

    it('应该处理空数据的情况', async () => {
      const mockPrompt: PromptInfo = {
        id: 1,
        name: '',
        description: '',
        content: '',
        media_type: MediaType.TEXT,
        class_id: 1,
        attachments: [],
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      }

      mockPromptApi.get.mockResolvedValue(mockPrompt)

      const wrapper = createPromptEditorWrapper()
      await nextTick()

      expect(wrapper.vm.form.name).toBe('')
      expect(wrapper.vm.form.description).toBe('')
      expect(wrapper.vm.attachments).toHaveLength(0)
    })
  })
})