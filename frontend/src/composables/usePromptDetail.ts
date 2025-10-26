import { ref, watch, computed, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getPrompt, type HttpError } from '../api/prompt'
import type { Prompt } from '../types/prompt'
import { MediaType } from '../types/prompt'
import { useAttachmentManagement } from './useAttachmentManagement'

interface UsePromptDetailResult {
  prompt: Ref<Prompt | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  refresh: () => Promise<void>
  
  // 附件管理相关
  attachmentManager: ReturnType<typeof useAttachmentManagement>
  isMediaTypeWithAttachments: Ref<boolean>
  canUploadAttachments: Ref<boolean>
}

function extractErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'status' in error) {
    const httpError = error as HttpError
    if (httpError.status === 404) {
      return '未找到对应的 Prompt 记录'
    }
  }
  if (error instanceof Error) {
    return error.message || '获取 Prompt 详情失败'
  }
  return '获取 Prompt 详情失败'
}

export function usePromptDetail(promptId: Ref<number | null>): UsePromptDetailResult {
  const prompt = ref<Prompt | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  let requestToken = 0

  // 初始化附件管理
  const attachmentManager = useAttachmentManagement()

  // 计算属性：判断当前媒体类型是否支持附件
  const isMediaTypeWithAttachments = computed(() => {
    const mediaType = prompt.value?.media_type
    return mediaType !== undefined && mediaType !== MediaType.TEXT
  })

  // 计算属性：判断是否可以上传附件
  const canUploadAttachments = computed(() => {
    return prompt.value !== null && isMediaTypeWithAttachments.value
  })

  async function refresh() {
    const id = promptId.value
    const currentToken = ++requestToken

    if (!id || id <= 0) {
      prompt.value = null
      error.value = '无效的 Prompt 标识'
      return
    }

    loading.value = true
    error.value = null
    try {
      const detail = await getPrompt(id)
      if (currentToken === requestToken) {
        prompt.value = detail
        
        // 同步加载附件信息
        if (detail && isMediaTypeWithAttachments.value) {
          await attachmentManager.loadAttachments(detail.id)
        }
      }
    } catch (err) {
      if (currentToken === requestToken) {
        const message = extractErrorMessage(err)
        error.value = message
        ElMessage.error(message)
        prompt.value = null
      }
    } finally {
      if (currentToken === requestToken) {
        loading.value = false
      }
    }
  }

  // 监听 promptId 变化
  watch(
    promptId,
    () => {
      void refresh()
    },
    { immediate: true }
  )

  // 监听媒体类型变化，重新加载附件
  watch(
    () => prompt.value?.media_type,
    async (newMediaType: MediaType | undefined, oldMediaType: MediaType | undefined) => {
      if (newMediaType !== oldMediaType && prompt.value) {
        if (isMediaTypeWithAttachments.value) {
          await attachmentManager.loadAttachments(prompt.value.id)
        } else {
          // 如果切换到文本类型，清空附件列表
          attachmentManager.attachments.value = []
        }
      }
    }
  )

  return {
    prompt,
    loading,
    error,
    refresh,
    
    // 附件管理相关
    attachmentManager,
    isMediaTypeWithAttachments,
    canUploadAttachments
  }
}
