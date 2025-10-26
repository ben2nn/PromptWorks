import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MediaTypeSelector from '../../components/MediaTypeSelector.vue'
import { MediaType } from '../../types/prompt'

describe('MediaTypeSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const createWrapper = (props = {}) => {
    return mount(MediaTypeSelector, {
      props: {
        modelValue: MediaType.TEXT,
        ...props
      },
      global: {
        stubs: {
          'el-select': {
            template: '<div class="el-select"><slot /></div>',
            props: ['modelValue'],
            emits: ['change']
          },
          'el-option': {
            template: '<div class="el-option"><slot /></div>',
            props: ['value', 'label']
          },
          'el-icon': {
            template: '<div class="el-icon"><slot /></div>'
          }
        }
      }
    })
  }

  it('应该正确渲染媒体类型选择器', () => {
    const wrapper = createWrapper()

    expect(wrapper.find('.media-type-selector').exists()).toBe(true)
    expect(wrapper.find('.media-type-select').exists()).toBe(true)
  })

  it('应该显示所有支持的媒体类型选项', () => {
    const wrapper = createWrapper()

    const component = wrapper.vm as any
    const mediaTypes = component.mediaTypes

    expect(mediaTypes).toHaveLength(5)
    expect(mediaTypes.map((type: any) => type.value)).toEqual([
      MediaType.TEXT,
      MediaType.IMAGE,
      MediaType.DOCUMENT,
      MediaType.AUDIO,
      MediaType.VIDEO
    ])
  })

  it('应该正确设置默认值', () => {
    const wrapper = createWrapper({
      modelValue: MediaType.IMAGE
    })

    const component = wrapper.vm as any
    expect(component.selectedType).toBe(MediaType.IMAGE)
  })

  it('应该在值变化时触发事件', async () => {
    const wrapper = createWrapper()

    const component = wrapper.vm as any
    
    // 模拟类型变更
    await component.handleTypeChange(MediaType.IMAGE)

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([MediaType.IMAGE])
    expect(wrapper.emitted('change')).toBeTruthy()
    expect(wrapper.emitted('change')?.[0]).toEqual([MediaType.IMAGE])
  })

  it('应该监听外部值变化', async () => {
    const wrapper = createWrapper()

    // 更新 props
    await wrapper.setProps({ modelValue: MediaType.VIDEO })

    const component = wrapper.vm as any
    expect(component.selectedType).toBe(MediaType.VIDEO)
  })

  it('应该正确返回当前类型信息', () => {
    const wrapper = createWrapper({
      modelValue: MediaType.IMAGE
    })

    const component = wrapper.vm as any
    const currentTypeInfo = component.getCurrentTypeInfo()

    expect(currentTypeInfo).toBeDefined()
    expect(currentTypeInfo.value).toBe(MediaType.IMAGE)
    expect(currentTypeInfo.label).toBe('图片')
    expect(currentTypeInfo.description).toBe('包含图片的多模态提示词')
  })

  it('应该为每个媒体类型配置正确的图标和颜色', () => {
    const wrapper = createWrapper()

    const component = wrapper.vm as any
    const mediaTypes = component.mediaTypes

    // 验证文本类型
    const textType = mediaTypes.find((type: any) => type.value === MediaType.TEXT)
    expect(textType.label).toBe('文本')
    expect(textType.color).toBe('#409EFF')

    // 验证图片类型
    const imageType = mediaTypes.find((type: any) => type.value === MediaType.IMAGE)
    expect(imageType.label).toBe('图片')
    expect(imageType.color).toBe('#67C23A')

    // 验证文档类型
    const documentType = mediaTypes.find((type: any) => type.value === MediaType.DOCUMENT)
    expect(documentType.label).toBe('文档')
    expect(documentType.color).toBe('#E6A23C')

    // 验证音频类型
    const audioType = mediaTypes.find((type: any) => type.value === MediaType.AUDIO)
    expect(audioType.label).toBe('音频')
    expect(audioType.color).toBe('#F56C6C')

    // 验证视频类型
    const videoType = mediaTypes.find((type: any) => type.value === MediaType.VIDEO)
    expect(videoType.label).toBe('视频')
    expect(videoType.color).toBe('#909399')
  })

  it('应该支持禁用状态', () => {
    const wrapper = createWrapper({
      disabled: true
    })

    // 验证组件接收到 disabled 属性
    expect(wrapper.props('disabled')).toBe(true)
  })

  it('应该正确处理未定义的 modelValue', () => {
    const wrapper = createWrapper({
      modelValue: undefined
    })

    const component = wrapper.vm as any
    expect(component.selectedType).toBe(MediaType.TEXT) // 默认值
  })
})