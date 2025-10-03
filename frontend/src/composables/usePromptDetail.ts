import { ref, watch, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getPrompt, type HttpError } from '../api/prompt'
import type { Prompt } from '../types/prompt'

interface UsePromptDetailResult {
  prompt: Ref<Prompt | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  refresh: () => Promise<void>
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

  watch(
    promptId,
    () => {
      void refresh()
    },
    { immediate: true }
  )

  return {
    prompt,
    loading,
    error,
    refresh
  }
}
