<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>快速测试</h2>
        <p class="page-desc">针对单个 Prompt 快速发起临时调用，验证模型输出效果。</p>
      </div>
    </section>

    <div class="test-layout">
      <el-card class="model-card">
        <template #header>
          <div class="card-header">
            <span>模型与参数</span>
          </div>
        </template>
        <el-form label-position="top" class="model-form">
          <el-form-item label="模型选择">
            <el-cascader
              v-model="selectedModelPath"
              :options="modelOptions"
              :props="cascaderProps"
              :show-all-levels="false"
              clearable
              filterable
              placeholder="先选择厂商，再选择模型"
              :disabled="isModelLoading"
            />
          </el-form-item>
          <el-form-item label="温度">
            <div class="temperature-box">
              <el-slider
                v-model="temperature"
                :min="0"
                :max="2"
                :step="0.01"
              />
              <el-input-number
                v-model="temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="2"
              />
            </div>
          </el-form-item>
          <el-form-item label="额外参数" :error="extraParamsError">
            <el-input
              v-model="extraParams"
              type="textarea"
              :autosize="{ minRows: 6, maxRows: 10 }"
              placeholder="请输入 JSON 格式的模型附加参数"
            />
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="chat-card">
        <template #header>
          <div class="card-header">
            <span>对话调试</span>
          </div>
        </template>
        <div class="chat-panel">
          <div class="chat-messages" ref="chatScrollRef">
            <template v-if="!messages.length">
              <el-empty description="发送首条消息以查看模型响应" />
            </template>
            <template v-else>
              <div
                v-for="message in messages"
                :key="message.id"
                :class="['chat-message', `chat-message--${message.role}`]"
              >
                <el-avatar :size="36" class="chat-message__avatar">
                  <template v-if="message.role === 'assistant'">
                    <img v-if="message.avatarUrl" :src="message.avatarUrl" :alt="message.avatarAlt" />
                    <span v-else>{{ message.avatarEmoji ?? message.avatarFallback }}</span>
                  </template>
                  <template v-else>
                    <img v-if="userAvatar" :src="userAvatar" alt="用户" />
                    <span v-else>我</span>
                  </template>
                </el-avatar>
                <div class="chat-message__bubble">
                  <p class="chat-message__name">{{ message.displayName }}</p>
                  <div class="chat-message__content">
                    <el-skeleton v-if="message.isStreaming && !message.content" animated :rows="2" />
                    <span v-else v-text="message.content" />
                  </div>
                </div>
              </div>
            </template>
          </div>
          <div class="chat-input">
            <el-input
              v-model="chatInput"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 6 }"
              placeholder="在此输入测试内容，支持多行输入"
              :disabled="isSending"
            />
            <div class="chat-input__footer">
              <el-cascader
                v-model="selectedPromptPath"
                :options="promptOptions"
                :props="promptCascaderProps"
                :show-all-levels="false"
                class="prompt-selector"
                clearable
                filterable
                placeholder="选择历史 Prompt 与版本"
                :disabled="isPromptLoading"
              />
              <div class="chat-input__actions">
                <el-button plain @click="handleSaveAsPrompt" :disabled="!chatInput.trim()">保存为 Prompt</el-button>
                <el-button type="primary" @click="handleSend" :loading="isSending">发送</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listLLMProviders, type LLMProvider } from '../api/llmProvider'
import { listPrompts } from '../api/prompt'
import type { Prompt } from '../types/prompt'

interface CascaderOptionNode {
  value: number | string
  label: string
  children?: CascaderOptionNode[]
  disabled?: boolean
}

interface QuickTestMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  displayName: string
  avatarUrl?: string | null
  avatarEmoji?: string | null
  avatarFallback?: string
  avatarAlt?: string
  isStreaming?: boolean
}

const cascaderProps = reactive({
  expandTrigger: 'hover' as const,
  emitPath: true
})

const promptCascaderProps = reactive({
  expandTrigger: 'hover' as const,
  emitPath: true
})

const PROMPT_FETCH_LIMIT = 200

const isModelLoading = ref(false)
const isPromptLoading = ref(false)
const isSending = ref(false)
const modelOptions = ref<CascaderOptionNode[]>([])
const promptOptions = ref<CascaderOptionNode[]>([])
const selectedModelPath = ref<(number | string)[]>([])
const selectedPromptPath = ref<(number | string)[]>([])
const temperature = ref(0.7)
const extraParams = ref('{}')
const extraParamsError = ref<string | null>(null)
const chatInput = ref('')
const messages = ref<QuickTestMessage[]>([])
const userAvatar = ''

const providerMap = ref(new Map<number, LLMProvider>())
const promptMap = ref(new Map<number, Prompt>())

const chatScrollRef = ref<HTMLDivElement | null>(null)
let streamTimer: ReturnType<typeof setInterval> | null = null
let messageId = 0

const selectedModel = computed(() => {
  if (selectedModelPath.value.length !== 2) return null
  const [providerIdRaw, modelNameRaw] = selectedModelPath.value
  const providerId = Number(providerIdRaw)
  if (Number.isNaN(providerId)) return null
  const provider = providerMap.value.get(providerId)
  if (!provider) return null
  const model = provider.models.find((item) => item.name === String(modelNameRaw))
  if (!model) return null
  return { provider, model }
})

watch(extraParams, (value) => {
  if (!value.trim()) {
    extraParamsError.value = '请输入合法的 JSON 文本'
    return
  }
  try {
    const parsed = JSON.parse(value)
    if (parsed === null || typeof parsed !== 'object') {
      extraParamsError.value = '额外参数需为对象结构'
    } else {
      extraParamsError.value = null
    }
  } catch (error) {
    void error
    extraParamsError.value = 'JSON 格式解析失败'
  }
}, { immediate: true })

watch(messages, async () => {
  await nextTick()
  const wrapper = chatScrollRef.value
  if (!wrapper) return
  wrapper.scrollTop = wrapper.scrollHeight
})

watch(selectedPromptPath, (path) => {
  if (path.length !== 3) {
    return
  }
  const [, promptIdRaw, versionIdRaw] = path
  const promptId = Number(promptIdRaw)
  const versionId = Number(versionIdRaw)
  if (Number.isNaN(promptId) || Number.isNaN(versionId)) {
    return
  }
  const prompt = promptMap.value.get(promptId)
  const version = prompt?.versions.find((item) => item.id === versionId)
  if (!version) {
    return
  }
  chatInput.value = version.content
})

onMounted(() => {
  void fetchLLMProviders()
  void fetchPromptOptions()
})

onBeforeUnmount(() => {
  if (streamTimer) {
    clearInterval(streamTimer)
    streamTimer = null
  }
})

async function fetchLLMProviders() {
  isModelLoading.value = true
  try {
    const providers = await listLLMProviders()
    providerMap.value = new Map(providers.map((item) => [item.id, item]))
    modelOptions.value = providers.map((provider) => ({
      value: provider.id,
      label: provider.provider_name,
      children: provider.models.map((model) => ({
        value: model.name,
        label: model.name
      }))
    }))
  } catch (error) {
    ElMessage.error('加载模型列表失败，请稍后再试')
  } finally {
    isModelLoading.value = false
  }
}

async function fetchPromptOptions() {
  isPromptLoading.value = true
  try {
    const prompts = await listPrompts({ limit: PROMPT_FETCH_LIMIT })
    promptMap.value = new Map(prompts.map((prompt) => [prompt.id, prompt]))
    const grouped = new Map<number, { label: string; prompts: Prompt[] }>()
    prompts.forEach((prompt) => {
      const classId = prompt.prompt_class.id
      if (!grouped.has(classId)) {
        grouped.set(classId, { label: prompt.prompt_class.name, prompts: [] })
      }
      grouped.get(classId)?.prompts.push(prompt)
    })
    promptOptions.value = Array.from(grouped.entries()).map(([classId, meta]) => ({
      value: classId,
      label: meta.label,
      children: meta.prompts.map((prompt) => ({
        value: prompt.id,
        label: prompt.name,
        children: prompt.versions.map((version) => ({
          value: version.id,
          label: version.version
        }))
      }))
    }))
  } catch (error) {
    ElMessage.error('加载 Prompt 列表失败，请稍后再试')
  } finally {
    isPromptLoading.value = false
  }
}

function handleSend() {
  const model = selectedModel.value
  if (!model) {
    ElMessage.warning('请先选择要调用的模型')
    return
  }
  if (extraParamsError.value) {
    ElMessage.warning('额外参数格式有误，请修正后再发送')
    return
  }
  const content = chatInput.value.trim()
  if (!content) {
    ElMessage.info('请输入要测试的内容')
    return
  }
  isSending.value = true
  chatInput.value = ''
  appendUserMessage(content)
  const assistantMessage = appendAssistantPlaceholder(model.provider)
  startMockStreaming(assistantMessage, model)
}

function handleSaveAsPrompt() {
  if (!chatInput.value.trim()) {
    ElMessage.info('请输入内容后再保存为 Prompt')
    return
  }
  ElMessage.success('已临时保存到草稿区，后续将接入实际保存功能')
}

function appendUserMessage(content: string) {
  messages.value.push({
    id: ++messageId,
    role: 'user',
    content,
    displayName: '我'
  })
}

function appendAssistantPlaceholder(provider: LLMProvider) {
  if (streamTimer) {
    clearInterval(streamTimer)
    streamTimer = null
  }
  const lastStreaming = [...messages.value].reverse().find((item) => item.role === 'assistant' && item.isStreaming)
  if (lastStreaming) {
    lastStreaming.isStreaming = false
  }
  const message: QuickTestMessage = {
    id: ++messageId,
    role: 'assistant',
    content: '',
    displayName: provider.provider_name,
    avatarUrl: provider.logo_url,
    avatarEmoji: provider.logo_emoji,
    avatarFallback: provider.provider_name.slice(0, 1).toUpperCase(),
    avatarAlt: provider.provider_name,
    isStreaming: true
  }
  messages.value.push(message)
  return message
}

function startMockStreaming(target: QuickTestMessage, model: { provider: LLMProvider }) {
  const snippets = [
    '正在根据当前 Prompt 生成回复...',
    `模型 ${model.provider.provider_name} 已接收到额外参数并开始推理。`,
    '示例响应：您好，这是一个示例输出，实际对接部署后将展示真实结果。'
  ]
  let index = 0
  streamTimer = setInterval(() => {
    if (!target) return
    if (index >= snippets.length) {
      stopStreaming(target)
      return
    }
    target.content = [target.content, snippets[index]].filter(Boolean).join('\n\n')
    index += 1
  }, 600)
}

function stopStreaming(target: QuickTestMessage) {
  if (streamTimer) {
    clearInterval(streamTimer)
    streamTimer = null
  }
  target.isStreaming = false
  isSending.value = false
}
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 64px - 48px);
  min-height: 520px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-header__text h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.page-desc {
  margin: 0;
  color: var(--text-weak-color);
  font-size: 14px;
}

.test-layout {
  display: flex;
  gap: 16px;
  align-items: stretch;
  flex: 1;
}

.model-card {
  flex: 0 0 25%;
  max-width: 25%;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.model-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.card-header {
  font-size: 14px;
  font-weight: 600;
}


.model-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.temperature-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-card {
  flex: 0 0 75%;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
  flex: 1;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.chat-message--user {
  flex-direction: row-reverse;
}

.chat-message--user .chat-message__bubble {
  background: rgba(64, 158, 255, 0.12);
  align-items: flex-end;
}

.chat-message--user .chat-message__name {
  text-align: right;
}

.chat-message--assistant .chat-message__bubble {
  background: var(--content-bg-color);
  border: 1px solid var(--side-border-color);
}

.chat-message__avatar {
  flex-shrink: 0;
}

.chat-message__bubble {
  max-width: 80%;
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  line-height: 1.6;
}

.chat-message__name {
  margin: 0;
  font-size: 12px;
  color: var(--text-weak-color);
}

.chat-message__content {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
}

.chat-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: auto;
}

.chat-input__footer {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.prompt-selector {
  flex: 1;
}

.chat-input__actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 1200px) {
  .test-layout {
    flex-direction: column;
  }

  .model-card,
  .chat-card {
    flex: 1 1 auto;
    max-width: 100%;
    height: auto;
  }

  .chat-message__bubble {
    max-width: 100%;
  }
}
</style>
