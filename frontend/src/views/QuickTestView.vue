<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>快速测试</h2>
        <p class="page-desc">针对单个 Prompt 快速发起临时调用，验证模型输出效果。</p>
      </div>
      <div class="page-header__actions">
        <el-select
          class="history-select"
          :model-value="activeSessionId"
          placeholder="历史记录"
          filterable
          @change="handleSessionChange"
        >
          <el-option
            v-for="option in sessionOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
        <el-button type="primary" @click="handleNewChat" :disabled="!canCreateNewChat">
          新建对话
        </el-button>
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
                  <div v-if="message.tokens" class="chat-message__meta">
                    <span>输入 Token：{{ formatTokenValue(message.tokens.input) }}</span>
                    <span>输出 Token：{{ formatTokenValue(message.tokens.output) }}</span>
                    <span>总计：{{ formatTokenValue(message.tokens.total) }}</span>
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
              @keydown.enter="handleEnterKey"
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
import {
  streamQuickTest,
  fetchQuickTestHistory,
  type QuickTestHistoryItem
} from '../api/quickTest'
import { listPrompts } from '../api/prompt'
import type { ChatMessagePayload } from '../types/llm'
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
  tokens?: {
    input: number | null
    output: number | null
    total: number | null
  }
}

interface ChatSession {
  id: number
  title: string
  messages: QuickTestMessage[]
  createdAt: number
  updatedAt: number
  autoTitle: boolean
  isPersisted: boolean
  hasInteraction: boolean
  providerId: number | null
  providerName: string | null
  providerLogoEmoji: string | null
  providerLogoUrl: string | null
  modelId: number | null
  modelName: string | null
  promptId: number | null
  promptVersionId: number | null
}

interface HistoryMatchCriteria {
  requestSignature?: string
  responseText?: string | null
  providerId?: number
  modelName?: string | null
  draftId?: number
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
const chatSessions = ref<ChatSession[]>([])
const activeSessionId = ref<number | null>(null)
let sessionSeed = 0
const messages = ref<QuickTestMessage[]>([])
const userAvatar = ''

const providerMap = ref(new Map<number, LLMProvider>())
const promptMap = ref(new Map<number, Prompt>())

const sessionOptions = computed(() =>
  [...chatSessions.value]
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .map((session) => ({
      value: session.id,
      label: formatSessionOptionLabel(session)
    }))
)

const canCreateNewChat = computed(() =>
  !chatSessions.value.some(
    (session) => !session.isPersisted && !session.hasInteraction && session.messages.length === 0
  )
)

const chatScrollRef = ref<HTMLDivElement | null>(null)
let activeStreamController: AbortController | null = null
let messageId = 0

const HISTORY_LIMIT = 30

function nextMessageId(): number {
  messageId += 1
  return messageId
}

function normalizeMessageContent(content: unknown): string {
  if (typeof content === 'string') {
    return content
  }
  if (content == null) {
    return ''
  }
  try {
    return JSON.stringify(content)
  } catch (error) {
    void error
    return String(content)
  }
}

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

watch(messages, () => {
  void scrollToBottom()
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
  void refreshHistory().then(() => {
    if (!chatSessions.value.length) {
      const session = createChatSession()
      messages.value = session.messages
      selectedModelPath.value = []
    }
  })
})

onBeforeUnmount(() => {
  cancelActiveStream()
})

function cancelActiveStream() {
  if (activeStreamController) {
    activeStreamController.abort()
    activeStreamController = null
  }
}

async function scrollToBottom() {
  await nextTick()
  const wrapper = chatScrollRef.value
  if (!wrapper) {
    return
  }
  wrapper.scrollTop = wrapper.scrollHeight
}

function handleSessionChange(value: number | null) {
  if (value === null || value === activeSessionId.value) {
    return
  }
  const session = chatSessions.value.find((item) => item.id === value)
  if (!session) {
    return
  }
  cancelActiveStream()
  isSending.value = false
  activeSessionId.value = session.id
  messages.value = session.messages
  chatInput.value = ''
  if (
    session.providerId != null &&
    session.modelName &&
    providerMap.value.has(session.providerId)
  ) {
    selectedModelPath.value = [session.providerId, session.modelName]
  }
  void scrollToBottom()
  syncActiveSessionSelection()
}

function handleNewChat() {
  if (!canCreateNewChat.value) {
    ElMessage.info('当前新建对话尚未使用，请先发送消息')
    return
  }
  cancelActiveStream()
  isSending.value = false
  chatInput.value = ''
  selectedPromptPath.value = []
  const session = createChatSession()
  messages.value = session.messages
  selectedModelPath.value = []
  void scrollToBottom()
}

function getActiveSession(): ChatSession | undefined {
  if (activeSessionId.value === null) {
    return undefined
  }
  return chatSessions.value.find((session) => session.id === activeSessionId.value)
}

function ensureActiveSession(): ChatSession {
  const existing = getActiveSession()
  if (existing) {
    return existing
  }
  return createChatSession()
}

function createChatSession(title?: string): ChatSession {
  const now = Date.now()
  const sessionMessages = reactive<QuickTestMessage[]>([]) as QuickTestMessage[]
  sessionSeed -= 1
  const identifier = Math.abs(sessionSeed)
  const session: ChatSession = {
    id: sessionSeed,
    title: title && title.trim() ? title : `新的对话 ${identifier}`,
    messages: sessionMessages,
    createdAt: now,
    updatedAt: now,
    autoTitle: !(title && title.trim()),
    isPersisted: false,
    hasInteraction: false,
    providerId: null,
    providerName: null,
    providerLogoEmoji: null,
    providerLogoUrl: null,
    modelId: null,
    modelName: null,
    promptId: null,
    promptVersionId: null
  }
  chatSessions.value.push(session)
  activeSessionId.value = session.id
  messages.value = session.messages
  return session
}

function generateSessionTitle(content: string, fallback: string): string {
  const trimmed = content.trim()
  if (!trimmed) {
    return fallback
  }
  const snippet = trimmed.slice(0, 18)
  return trimmed.length > 18 ? `${snippet}…` : snippet
}

function updateActiveSessionTimestamp() {
  const session = getActiveSession()
  if (session) {
    session.updatedAt = Date.now()
  }
}

function formatSessionOptionLabel(session: ChatSession): string {
  const timestamp = formatSessionTime(session.updatedAt)
  const prefix = session.isPersisted ? '' : '草稿·'
  return `${prefix}${session.title}（${timestamp}）`
}

function formatSessionTime(timestamp: number): string {
  const date = new Date(timestamp)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

function syncActiveSessionSelection() {
  const session = getActiveSession()
  if (
    session &&
    session.providerId != null &&
    session.modelName &&
    providerMap.value.has(session.providerId)
  ) {
    selectedModelPath.value = [session.providerId, session.modelName]
  }
}

function deriveHistoryTitle(log: QuickTestHistoryItem): string {
  if (Array.isArray(log.messages)) {
    const firstUser = log.messages.find((item) => item.role === 'user')
    if (firstUser) {
      const snippet = normalizeMessageContent(firstUser.content).trim()
      if (snippet) {
        return snippet.length > 18 ? `${snippet.slice(0, 18)}…` : snippet
      }
    }
  }
  if (log.provider_name) {
    return `${log.provider_name}-${log.model_name}`
  }
  return `历史对话 ${log.id}`
}

function convertHistoryLogToSession(log: QuickTestHistoryItem): ChatSession {
  const sessionMessages = reactive<QuickTestMessage[]>([]) as QuickTestMessage[]
  const providerName = log.provider_name
  const providerEmoji = log.provider_logo_emoji
  const providerLogoUrl = log.provider_logo_url

  const historyMessages = Array.isArray(log.messages) ? log.messages : []
  for (const entry of historyMessages) {
    const role = typeof entry.role === 'string' ? entry.role : 'user'
    const normalizedRole = role === 'assistant' || role === 'system' ? 'assistant' : 'user'
    const displayName =
      role === 'assistant' ? providerName ?? '助手' : role === 'system' ? '系统' : '我'
    sessionMessages.push({
      id: nextMessageId(),
      role: normalizedRole,
      content: normalizeMessageContent(entry.content),
      displayName,
      avatarUrl: normalizedRole === 'assistant' ? providerLogoUrl ?? undefined : userAvatar,
      avatarEmoji: normalizedRole === 'assistant' ? providerEmoji ?? undefined : undefined,
      avatarFallback:
        normalizedRole === 'assistant'
          ? (providerName ?? '助手').slice(0, 1).toUpperCase()
          : undefined,
      avatarAlt: normalizedRole === 'assistant' ? providerName ?? '助手' : '我',
      isStreaming: false,
      tokens: undefined,
    })
  }

  if (log.response_text) {
    const assistantMessage: QuickTestMessage = {
      id: nextMessageId(),
      role: 'assistant',
      content: normalizeMessageContent(log.response_text),
      displayName: providerName ?? '助手',
      avatarUrl: providerLogoUrl ?? undefined,
      avatarEmoji: providerEmoji ?? undefined,
      avatarFallback: (providerName ?? '助手').slice(0, 1).toUpperCase(),
      avatarAlt: providerName ?? '助手',
      isStreaming: false,
      tokens: undefined,
    }
    applyUsageToMessage(assistantMessage, {
      prompt_tokens: log.prompt_tokens ?? undefined,
      completion_tokens: log.completion_tokens ?? undefined,
      total_tokens: log.total_tokens ?? undefined,
    })
    sessionMessages.push(assistantMessage)
  }

  const createdAt = Date.parse(log.created_at)
  const timestamp = Number.isNaN(createdAt) ? Date.now() : createdAt

  return {
    id: log.id,
    title: deriveHistoryTitle(log),
    messages: sessionMessages,
    createdAt: timestamp,
    updatedAt: timestamp,
    autoTitle: false,
    isPersisted: true,
    hasInteraction: true,
    providerId: log.provider_id,
    providerName,
    providerLogoEmoji: providerEmoji,
    providerLogoUrl,
    modelId: log.model_id,
    modelName: log.model_name,
    promptId: log.prompt_id,
    promptVersionId: log.prompt_version_id,
  }
}

async function refreshHistory(match?: HistoryMatchCriteria): Promise<void> {
  try {
    const logs = await fetchQuickTestHistory({ limit: HISTORY_LIMIT })
    const persistedSessions = logs.map(convertHistoryLogToSession)
    const drafts = chatSessions.value.filter((session) => !session.isPersisted)

    let remainingDrafts = drafts
    let matchedId: number | null = null

    if (match) {
      const matchedLog = logs.find((log) => {
        const providerOk =
          match.providerId === undefined || log.provider_id === match.providerId
        const modelOk =
          match.modelName === undefined || log.model_name === match.modelName
        const responseOk =
          match.responseText === undefined || log.response_text === match.responseText
        const requestOk =
          match.requestSignature === undefined
            ? true
            : JSON.stringify(log.messages ?? []) === match.requestSignature
        return providerOk && modelOk && responseOk && requestOk
      })
      if (matchedLog) {
        matchedId = matchedLog.id
        if (match.draftId !== undefined) {
          remainingDrafts = drafts.filter((session) => session.id !== match.draftId)
        }
      }
    }

    chatSessions.value = [...persistedSessions, ...remainingDrafts]

    if (matchedId !== null) {
      const matchedSession = chatSessions.value.find((session) => session.id === matchedId)
      if (matchedSession) {
        activeSessionId.value = matchedSession.id
        messages.value = matchedSession.messages
        if (
          matchedSession.providerId != null &&
          matchedSession.modelName &&
          providerMap.value.has(matchedSession.providerId)
        ) {
          selectedModelPath.value = [matchedSession.providerId, matchedSession.modelName]
        }
        chatInput.value = ''
        void scrollToBottom()
        syncActiveSessionSelection()
      }
      return
    }

    if (activeSessionId.value !== null) {
      const active = chatSessions.value.find((session) => session.id === activeSessionId.value)
      if (active) {
        messages.value = active.messages
        syncActiveSessionSelection()
        return
      }
    }

    if (chatSessions.value.length > 0) {
      const session = chatSessions.value[0]
      activeSessionId.value = session.id
      messages.value = session.messages
      if (
        session.providerId != null &&
        session.modelName &&
        providerMap.value.has(session.providerId)
      ) {
        selectedModelPath.value = [session.providerId, session.modelName]
      }
      chatInput.value = ''
      void scrollToBottom()
    }
    syncActiveSessionSelection()
  } catch (error) {
    void error
    ElMessage.warning('加载历史记录失败，请稍后再试')
  }
}
function handleEnterKey(event: KeyboardEvent) {
  if (event.shiftKey) {
    return
  }
  event.preventDefault()
  if (isSending.value) {
    return
  }
  void handleSend()
}

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
    syncActiveSessionSelection()
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

function resolveSelectedPromptMeta() {
  if (selectedPromptPath.value.length !== 3) {
    return null
  }
  const [, promptIdRaw, versionIdRaw] = selectedPromptPath.value
  const promptId = Number(promptIdRaw)
  const versionId = Number(versionIdRaw)
  if (Number.isNaN(promptId) || Number.isNaN(versionId)) {
    return null
  }
  return { promptId, versionId }
}

function buildChatPayloadMessages(): ChatMessagePayload[] {
  return messages.value
    .filter((message) => !(message.role === 'assistant' && message.isStreaming))
    .map((message) => ({ role: message.role, content: message.content }))
}

function parseExtraParameters(): Record<string, unknown> {
  if (!extraParams.value.trim()) {
    return {}
  }
  try {
    const parsed = JSON.parse(extraParams.value)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (error) {
    void error
    return {}
  }
}

function applyUsageToMessage(
  message: QuickTestMessage,
  usage: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number }
) {
  if (!usage) return
  const input = usage.prompt_tokens ?? null
  const output = usage.completion_tokens ?? null
  const total = usage.total_tokens ?? (
    input !== null || output !== null
      ? (input ?? 0) + (output ?? 0)
      : null
  )
  message.tokens = { input, output, total }
}

function formatTokenValue(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '—'
  }
  return value
}

async function handleSend() {
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
  cancelActiveStream()
  const session = ensureActiveSession()
  const provider = model.provider
  const targetModel = model.model

  session.providerId = provider.id
  session.providerName = provider.provider_name
  session.providerLogoEmoji = provider.logo_emoji
  session.providerLogoUrl = provider.logo_url
  session.modelId = targetModel.id
  session.modelName = targetModel.name

  isSending.value = true
  chatInput.value = ''
  appendUserMessage(content)
  const assistantMessage = appendAssistantPlaceholder(provider)

  const messagesPayload = buildChatPayloadMessages()
  session.hasInteraction = true
  const extraParameters = parseExtraParameters()
  const promptMeta = resolveSelectedPromptMeta()
  session.promptId = promptMeta?.promptId ?? null
  session.promptVersionId = promptMeta?.versionId ?? null

  const controller = new AbortController()
  activeStreamController = controller

  const payload = {
    providerId: provider.id,
    modelId: targetModel.id,
    modelName: targetModel.name,
    messages: messagesPayload,
    temperature: temperature.value,
    parameters: extraParameters,
    promptId: promptMeta?.promptId ?? null,
    promptVersionId: promptMeta?.versionId ?? null
  }

  let shouldScrollAfterStream = false
  let shouldRefreshHistory = false
  const matchCriteria: HistoryMatchCriteria = {
    requestSignature: JSON.stringify(messagesPayload),
    providerId: provider.id,
    modelName: targetModel.name,
    draftId: session.isPersisted ? undefined : session.id
  }
  try {
    for await (const event of streamQuickTest(payload, { signal: controller.signal })) {
      const data = event.data
      if (data === '[DONE]') {
        break
      }
      let parsed: any
      try {
        parsed = JSON.parse(data)
      } catch (error) {
        void error
        continue
      }

      if (parsed?.usage) {
        applyUsageToMessage(assistantMessage, parsed.usage)
        updateActiveSessionTimestamp()
      }

      const choices = Array.isArray(parsed?.choices) ? parsed.choices : []
      for (const choice of choices) {
        const delta = choice?.delta
        if (delta && typeof delta.content === 'string') {
          assistantMessage.content += delta.content
          shouldScrollAfterStream = true
          updateActiveSessionTimestamp()
          continue
        }
        const message = choice?.message
        if (message && typeof message.content === 'string') {
          assistantMessage.content += message.content
          shouldScrollAfterStream = true
          updateActiveSessionTimestamp()
        }
      }
    }
    shouldRefreshHistory = true
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      if (!assistantMessage.content) {
        assistantMessage.content = '本次请求已取消'
      }
      assistantMessage.tokens = undefined
      shouldScrollAfterStream = true
      updateActiveSessionTimestamp()
      return
    }
    let message = '调用模型失败，请稍后再试'
    const detail = error?.payload ?? error?.detail
    if (typeof detail === 'string') {
      message = detail
    } else if (detail && typeof detail === 'object') {
      message = detail.message ?? detail.detail ?? message
    } else if (error?.message) {
      message = error.message
    }
    assistantMessage.content = message
    assistantMessage.tokens = undefined
    ElMessage.error(message)
    shouldScrollAfterStream = true
    updateActiveSessionTimestamp()
  } finally {
    assistantMessage.isStreaming = false
    isSending.value = false
    if (activeStreamController === controller) {
      activeStreamController = null
    }
    if (assistantMessage.content) {
      shouldScrollAfterStream = true
    }
    session.updatedAt = Date.now()
    if (shouldScrollAfterStream) {
      void scrollToBottom()
    }
    if (shouldRefreshHistory) {
      matchCriteria.responseText = assistantMessage.content
      await refreshHistory(matchCriteria)
    }
  }
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
    id: nextMessageId(),
    role: 'user',
    content,
    displayName: '我'
  })
  const session = getActiveSession()
  if (session) {
    session.hasInteraction = true
    if (session.autoTitle) {
      session.title = generateSessionTitle(content, session.title)
      if (content.trim()) {
        session.autoTitle = false
      }
    }
    session.updatedAt = Date.now()
  }
  void scrollToBottom()
}

function appendAssistantPlaceholder(provider: LLMProvider) {
  const lastStreaming = [...messages.value].reverse().find((item) => item.role === 'assistant' && item.isStreaming)
  if (lastStreaming) {
    lastStreaming.isStreaming = false
  }
  const message: QuickTestMessage = {
    id: nextMessageId(),
    role: 'assistant',
    content: '',
    displayName: provider.provider_name,
    avatarUrl: provider.logo_url,
    avatarEmoji: provider.logo_emoji,
    avatarFallback: provider.provider_name.slice(0, 1).toUpperCase(),
    avatarAlt: provider.provider_name,
    isStreaming: true,
    tokens: undefined
  }
  messages.value.push(message)
  const session = getActiveSession()
  if (session) {
    session.providerId = provider.id
    session.providerName = provider.provider_name
    session.providerLogoEmoji = provider.logo_emoji
    session.providerLogoUrl = provider.logo_url
    session.updatedAt = Date.now()
  }
  void scrollToBottom()
  return message
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

.page-header__actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.history-select {
  width: 220px;
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
  min-height: 0;
}

.model-card {
  flex: 0 0 25%;
  max-width: 25%;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.model-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: auto;
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
  overflow: hidden;
}

.chat-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
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

.chat-message__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  font-size: 12px;
  color: var(--text-weak-color);
  margin-top: 4px;
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

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .page-header__actions {
    margin-left: 0;
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
  }

  .history-select {
    flex: 1 1 auto;
    width: 100%;
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
