<template>
  <div class="job-create-page">
    <el-breadcrumb v-if="fromPromptDetail" separator="/" class="page-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptManagement">Prompt 管理</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptDetail">
          {{ currentPromptName }}
        </span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>新建测试任务</el-breadcrumb-item>
    </el-breadcrumb>
    <el-breadcrumb v-else separator="/" class="page-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goTestManagement">测试任务</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>新建测试任务</el-breadcrumb-item>
    </el-breadcrumb>

    <el-alert
      v-if="promptError"
      :title="promptError"
      type="error"
      show-icon
    />

    <el-card>
      <template #header>
        <div class="card-header">
          <div>
            <h3>配置测试模式</h3>
            <p class="card-subtitle">根据实际需求选择合适的测试策略，后续可挂接真实任务编排</p>
          </div>
          <el-radio-group v-model="currentMode" size="small" class="mode-selector">
            <el-radio-button
              v-for="mode in modeOptions"
              :key="mode.value"
              :label="mode.value"
            >
              {{ mode.label }}
            </el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <section class="mode-summary">
        <el-icon class="mode-summary__icon"><Memo /></el-icon>
        <div>
          <h4 class="mode-summary__title">{{ currentModeInfo.label }}</h4>
          <p class="mode-summary__desc">{{ currentModeInfo.description }}</p>
        </div>
      </section>

      <el-form label-width="120px" class="test-form">
        <el-form-item label="测试名称">
          <el-input
            v-model="baseForm.name"
            placeholder="例如：v1.4.2 回归测试"
            maxlength="60"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="测试说明">
          <el-input
            v-model="baseForm.description"
            type="textarea"
            :rows="3"
            placeholder="补充测试目标、覆盖场景与评估指标"
          />
        </el-form-item>
        <el-form-item label="关联 Prompt">
          <el-select
            v-model="selectedPromptId"
            filterable
            :loading="promptListLoading"
            placeholder="请选择或搜索 Prompt"
            :disabled="promptListLoading"
            @change="handlePromptChange"
          >
            <el-option
              v-for="prompt in promptOptions"
              :key="prompt.id"
              :label="prompt.name"
              :value="prompt.id"
            />
          </el-select>
        </el-form-item>

        <el-alert
          v-if="detailError"
          :title="detailError"
          type="warning"
          show-icon
          class="form-alert"
        />

        <el-skeleton v-else-if="detailLoading" animated :rows="4" />

        <template v-else>
          <el-alert
            v-if="llmError"
            :title="llmError"
            type="warning"
            show-icon
            class="form-alert"
          />

          <template v-if="currentMode === 'same-model-different-version'">
            <el-form-item label="对比模型">
              <el-select
                v-model="sameModelForm.modelKey"
                placeholder="请选择测试模型"
                :loading="llmLoading"
                :disabled="llmLoading || !hasModelOptions"
                filterable
              >
                <el-option-group
                  v-for="group in modelOptionGroups"
                  :key="group.providerId"
                  :label="group.label"
                >
                  <el-option
                    v-for="option in group.options"
                    :key="option.key"
                    :label="option.label"
                    :value="option.key"
                  />
                </el-option-group>
              </el-select>
              <p v-if="!llmLoading && !hasModelOptions" class="form-tip">
                暂无可用模型，请先在“LLMs 配置”中添加模型。
              </p>
            </el-form-item>
            <el-form-item label="测试次数">
              <el-input-number
                v-model="sameModelForm.testCount"
                :min="1"
                :max="20"
                :step="1"
                :controls="false"
              />
              <p class="form-tip">每个版本会按照设定次数重复请求，用于平滑随机波动。</p>
            </el-form-item>
            <el-form-item label="温度">
              <div class="temperature-group">
                <el-slider
                  v-model="sameModelParams.temperature"
                  :min="0"
                  :max="2"
                  :step="0.01"
                  class="temperature-slider"
                />
                <el-input-number
                  v-model="sameModelParams.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  :precision="2"
                />
              </div>
            </el-form-item>
            <el-form-item label="额外参数" :error="extraParamsError">
              <el-input
                v-model="sameModelParams.extraParams"
                type="textarea"
                :autosize="{ minRows: 4, maxRows: 8 }"
                placeholder="请输入 JSON 格式的模型附加参数，例如 { &quot;top_p&quot;: 0.8 }"
              />
            </el-form-item>
            <el-form-item label="选择版本">
              <el-select
                v-model="sameModelForm.versionIds"
                multiple
                collapse-tags
                placeholder="请选择待对比的 Prompt 版本"
                :disabled="!versionOptions.length"
              >
                <el-option
                  v-for="version in versionOptions"
                  :key="version.id"
                  :label="renderVersionLabel(version)"
                  :value="version.id"
                />
              </el-select>
              <p v-if="!versionOptions.length" class="form-tip">当前 Prompt 暂无历史版本，可前往 Prompt 详情补充</p>
            </el-form-item>
          </template>

          <template v-else-if="currentMode === 'same-version-different-model'">
            <el-form-item label="对比版本">
              <el-select
                v-model="sameVersionForm.versionId"
                placeholder="请选择基准版本"
                :disabled="!versionOptions.length"
              >
                <el-option
                  v-for="version in versionOptions"
                  :key="version.id"
                  :label="renderVersionLabel(version)"
                  :value="version.id"
                />
              </el-select>
              <p v-if="!versionOptions.length" class="form-tip">暂无可用版本，请先创建 Prompt 版本</p>
            </el-form-item>
            <el-form-item label="选择模型">
              <el-select
                v-model="sameVersionForm.modelKeys"
                multiple
                collapse-tags
                placeholder="请选择参与对比的模型"
                :loading="llmLoading"
                :disabled="llmLoading || !hasModelOptions"
                filterable
              >
                <el-option-group
                  v-for="group in modelOptionGroups"
                  :key="group.providerId"
                  :label="group.label"
                >
                  <el-option
                    v-for="option in group.options"
                    :key="option.key"
                    :label="option.label"
                    :value="option.key"
                  />
                </el-option-group>
              </el-select>
              <p v-if="!llmLoading && !hasModelOptions" class="form-tip">
                暂无可用模型，请先在“LLMs 配置”中添加模型。
              </p>
            </el-form-item>
          </template>

          <template v-else>
            <el-form-item label="固定版本">
              <el-select
                v-model="multiTurnForm.versionId"
                placeholder="请选择执行版本"
                :disabled="!versionOptions.length"
              >
                <el-option
                  v-for="version in versionOptions"
                  :key="version.id"
                  :label="renderVersionLabel(version)"
                  :value="version.id"
                />
              </el-select>
              <p v-if="!versionOptions.length" class="form-tip">暂无版本信息，无法配置多轮测试</p>
            </el-form-item>
            <el-form-item label="执行模型">
              <el-select
                v-model="multiTurnForm.modelKey"
                placeholder="请选择用于多轮对话的模型"
                :loading="llmLoading"
                :disabled="llmLoading || !hasModelOptions"
                filterable
              >
                <el-option-group
                  v-for="group in modelOptionGroups"
                  :key="group.providerId"
                  :label="group.label"
                >
                  <el-option
                    v-for="option in group.options"
                    :key="option.key"
                    :label="option.label"
                    :value="option.key"
                  />
                </el-option-group>
              </el-select>
              <p v-if="!llmLoading && !hasModelOptions" class="form-tip">
                暂无可用模型，请先在“LLMs 配置”中添加模型。
              </p>
            </el-form-item>
            <el-form-item label="多轮对话">
              <div class="conversation-editor">
                <div
                  v-for="(round, index) in multiTurnRounds"
                  :key="round.id"
                  class="conversation-item"
                >
                  <div class="conversation-item__header">
                    <el-tag size="small" effect="light">轮次 {{ index + 1 }}</el-tag>
                    <el-button
                      v-if="multiTurnRounds.length > 1"
                      type="primary"
                      link
                      size="small"
                      @click="removeConversationRound(round.id)"
                    >删除</el-button>
                  </div>
                  <el-select v-model="round.role" class="conversation-item__role" size="small">
                    <el-option label="系统" value="system" />
                    <el-option label="用户" value="user" />
                    <el-option label="助手" value="assistant" />
                  </el-select>
                  <el-input
                    v-model="round.content"
                    type="textarea"
                    :rows="3"
                    placeholder="填写当前轮次的消息内容"
                  />
                </div>
                <el-button plain size="small" @click="addConversationRound">新增轮次</el-button>
              </div>
            </el-form-item>
          </template>
        </template>

        <el-form-item>
          <el-space>
            <el-button
              type="primary"
              :loading="isSubmitting"
              :disabled="isSubmitting"
              @click="handleSubmit"
            >
              创建测试任务
            </el-button>
            <el-button :disabled="isSubmitting" @click="handleCancel">返回</el-button>
          </el-space>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Memo } from '@element-plus/icons-vue'
import { listPrompts, getPrompt } from '../api/prompt'
import { createTestRun } from '../api/testRun'
import type { Prompt, PromptVersion } from '../types/prompt'
import { listLLMProviders } from '../api/llmProvider'
import type { LLMProvider } from '../types/llm'

type TestMode =
  | 'same-model-different-version'
  | 'same-version-different-model'
  | 'multi-turn-same-model'

interface ModeOption {
  value: TestMode
  label: string
  description: string
}

interface ConversationRound {
  id: number
  role: 'system' | 'user' | 'assistant'
  content: string
}

interface ModelOptionInfo {
  key: string
  label: string
  providerId: number
  providerName: string
  modelId: number
  modelName: string
}

interface ModelOptionGroup {
  providerId: number
  label: string
  options: ModelOptionInfo[]
}

const MODE_OPTIONS: ModeOption[] = [
  {
    value: 'same-model-different-version',
    label: '同模型不同版本',
    description: '固定模型，对比同一 Prompt 的多个版本，评估版本升级效果。'
  },
  {
    value: 'same-version-different-model',
    label: '同版本不同模型',
    description: '固定 Prompt 版本，通过多模型对比评估成本与质量差异。'
  },
  {
    value: 'multi-turn-same-model',
    label: '同版本同模型多轮测试',
    description: '按多轮会话脚本执行稳定性验证，适合客服、助理类场景。'
  }
]

const router = useRouter()
const route = useRoute()

const currentMode = ref<TestMode>('same-model-different-version')
const baseForm = reactive({
  name: '',
  description: ''
})

const sameModelForm = reactive({
  modelKey: '',
  versionIds: [] as number[],
  testCount: 3
})

const sameModelParams = reactive({
  temperature: 0.7,
  extraParams: '{"top_p":0.9}'
})

const extraParamsError = ref<string | null>(null)

const sameVersionForm = reactive({
  versionId: null as number | null,
  modelKeys: [] as string[]
})

const multiTurnForm = reactive({
  versionId: null as number | null,
  modelKey: ''
})

const multiTurnRounds = ref<ConversationRound[]>([
  { id: Date.now(), role: 'system', content: '' },
  { id: Date.now() + 1, role: 'user', content: '' }
])

const promptOptions = ref<Array<{ id: number; name: string }>>([])
const promptListLoading = ref(false)
const promptError = ref<string | null>(null)

const selectedPromptId = ref<number | null>(extractPromptId(route.params.id ?? route.query.promptId))
const promptDetail = ref<Prompt | null>(null)
const detailLoading = ref(false)
const detailError = ref<string | null>(null)
const isSubmitting = ref(false)

const llmProviders = ref<LLMProvider[]>([])
const llmLoading = ref(false)
const llmError = ref<string | null>(null)

const modeOptions = MODE_OPTIONS

const modelOptionGroups = computed<ModelOptionGroup[]>(() =>
  llmProviders.value
    .filter((provider) => provider.models && provider.models.length)
    .map((provider) => ({
      providerId: provider.id,
      label: provider.provider_name,
      options: provider.models.map((model) => ({
        key: `${provider.id}:${model.id}`,
        label: model.name,
        providerId: provider.id,
        providerName: provider.provider_name,
        modelId: model.id,
        modelName: model.name
      }))
    }))
)

const modelOptionMap = computed(() => {
  const map = new Map<string, ModelOptionInfo>()
  for (const group of modelOptionGroups.value) {
    for (const option of group.options) {
      map.set(option.key, option)
    }
  }
  return map
})

const hasModelOptions = computed(() => modelOptionMap.value.size > 0)

const fromPromptDetail = computed(() => route.name === 'prompt-test-create')

const currentModeInfo = computed(() =>
  modeOptions.find((item) => item.value === currentMode.value) ?? modeOptions[0]
)

const versionOptions = computed(() =>
  (promptDetail.value?.versions ?? []).slice().sort((a, b) =>
    b.updated_at.localeCompare(a.updated_at)
  )
)

const currentPromptName = computed(() => promptDetail.value?.name ?? 'Prompt 详情')

watch(
  () => route.params.id,
  (value) => {
    const id = extractPromptId(value)
    if (id) {
      selectedPromptId.value = id
    }
  }
)

watch(
  () => route.query.promptId,
  (value) => {
    const id = extractPromptId(value)
    if (id) {
      selectedPromptId.value = id
    }
  }
)

watch(selectedPromptId, () => {
  sameModelForm.versionIds = []
  sameVersionForm.versionId = null
  multiTurnForm.versionId = null
})

watch(versionOptions, (versions) => {
  const availableIds = new Set(versions.map((item) => item.id))
  sameModelForm.versionIds = sameModelForm.versionIds.filter((id) => availableIds.has(id))

  if (sameVersionForm.versionId && !availableIds.has(sameVersionForm.versionId)) {
    sameVersionForm.versionId = versions[0]?.id ?? null
  }

  if (multiTurnForm.versionId && !availableIds.has(multiTurnForm.versionId)) {
    multiTurnForm.versionId = versions[0]?.id ?? null
  }
})

watch(
  () => promptDetail.value?.name,
  (name) => {
    if (name && !baseForm.name) {
      baseForm.name = `${name} 测试任务`
    }
  }
)

watch(
  modelOptionMap,
  (map) => {
    if (!map.size) {
      sameModelForm.modelKey = ''
      sameVersionForm.modelKeys = []
      multiTurnForm.modelKey = ''
      return
    }
    const firstKey = map.keys().next().value as string | undefined
    if (!sameModelForm.modelKey || !map.has(sameModelForm.modelKey)) {
      sameModelForm.modelKey = firstKey ?? ''
    }
    sameVersionForm.modelKeys = sameVersionForm.modelKeys.filter((key) => map.has(key))
    if (!multiTurnForm.modelKey || !map.has(multiTurnForm.modelKey)) {
      multiTurnForm.modelKey = firstKey ?? ''
    }
  },
  { immediate: true }
)

async function fetchPromptOptions() {
  promptListLoading.value = true
  promptError.value = null
  try {
    const prompts = await listPrompts({ limit: 200 })
    promptOptions.value = prompts.map((prompt) => ({ id: prompt.id, name: prompt.name }))
    if (!selectedPromptId.value && prompts.length) {
      selectedPromptId.value = prompts[0].id
    }
  } catch (error) {
    promptError.value = extractErrorMessage(error, '加载 Prompt 列表失败')
  } finally {
    promptListLoading.value = false
  }
}

async function fetchLLMProviders() {
  llmLoading.value = true
  llmError.value = null
  try {
    llmProviders.value = await listLLMProviders()
  } catch (error) {
    llmError.value = extractErrorMessage(error, '加载模型配置失败')
    llmProviders.value = []
  } finally {
    llmLoading.value = false
  }
}

async function fetchPromptDetail() {
  const id = selectedPromptId.value
  if (!id) {
    promptDetail.value = null
    detailError.value = null
    return
  }
  detailLoading.value = true
  detailError.value = null
  try {
    promptDetail.value = await getPrompt(id)
    const exists = promptOptions.value.some((item) => item.id === id)
    if (!exists && promptDetail.value) {
      promptOptions.value = [
        ...promptOptions.value,
        { id, name: promptDetail.value.name }
      ]
    }
  } catch (error) {
    detailError.value = extractErrorMessage(error, '获取 Prompt 详情失败')
    promptDetail.value = null
  } finally {
    detailLoading.value = false
  }
}

watch(selectedPromptId, () => {
  void fetchPromptDetail()
})

onMounted(() => {
  void fetchPromptOptions()
  void fetchPromptDetail()
  void fetchLLMProviders()
})

watch(
  () => sameModelParams.extraParams,
  (value) => {
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
  },
  { immediate: true }
)

function handlePromptChange() {
  // 交互上已经通过 watch 触发详情刷新，此处仅用于保留钩子以便后续扩展
}

function renderVersionLabel(version: PromptVersion) {
  const date = new Date(version.updated_at ?? version.created_at)
  const formatted = Number.isNaN(date.getTime())
    ? version.updated_at ?? version.created_at
    : new Intl.DateTimeFormat('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date)
  return `${version.version}｜${formatted}`
}

function addConversationRound() {
  multiTurnRounds.value.push({
    id: Date.now() + multiTurnRounds.value.length,
    role: 'user',
    content: ''
  })
}

function removeConversationRound(id: number) {
  if (multiTurnRounds.value.length <= 1) {
    ElMessage.warning('至少保留一轮对话')
    return
  }
  multiTurnRounds.value = multiTurnRounds.value.filter((item) => item.id !== id)
}

function normalizeSameModelExtraParams(): {
  top_p?: number
  schema: Record<string, unknown> | null
} {
  try {
    const parsed = JSON.parse(sameModelParams.extraParams) as unknown
    if (!parsed || typeof parsed !== 'object') {
      return { schema: null }
    }
    const record = parsed as Record<string, unknown>
    const { top_p, ...rest } = record
    const topPValue = typeof top_p === 'number' ? top_p : undefined
    const schema = Object.keys(rest).length ? (rest as Record<string, unknown>) : null
    return { top_p: topPValue, schema }
  } catch (error) {
    void error
    return { schema: null }
  }
}

function resolveModelInfo(key: string): ModelOptionInfo | null {
  if (!key) {
    return null
  }
  return modelOptionMap.value.get(key) ?? null
}

function validateForm(): boolean {
  if (!baseForm.name.trim()) {
    ElMessage.warning('请填写测试名称')
    return false
  }
  if (!selectedPromptId.value) {
    ElMessage.warning('请选择关联 Prompt')
    return false
  }
  if (detailLoading.value) {
    ElMessage.info('正在加载 Prompt 详情，请稍候')
    return false
  }
  if (!promptDetail.value) {
    ElMessage.warning('未获取到有效的 Prompt 信息')
    return false
  }

  if (currentMode.value === 'same-model-different-version') {
    if (!hasModelOptions.value) {
      ElMessage.warning('暂无可用模型，请先在“LLMs 配置”中添加')
      return false
    }
    if (!sameModelForm.modelKey || !modelOptionMap.value.has(sameModelForm.modelKey)) {
      ElMessage.warning('请选择需要对比的模型')
      return false
    }
    if (sameModelForm.versionIds.length < 2) {
      ElMessage.warning('请至少选择两个 Prompt 版本进行对比')
      return false
    }
    if (sameModelForm.testCount < 1) {
      ElMessage.warning('测试次数至少为 1 次')
      return false
    }
    if (extraParamsError.value) {
      ElMessage.warning(extraParamsError.value)
      return false
    }
  } else if (currentMode.value === 'same-version-different-model') {
    if (!sameVersionForm.versionId) {
      ElMessage.warning('请选择基准版本')
      return false
    }
    if (!hasModelOptions.value) {
      ElMessage.warning('暂无可用模型，请先在“LLMs 配置”中添加')
      return false
    }
    if (sameVersionForm.modelKeys.length < 2) {
      ElMessage.warning('请至少选择两个模型参与对比')
      return false
    }
  } else if (currentMode.value === 'multi-turn-same-model') {
    if (!multiTurnForm.versionId) {
      ElMessage.warning('请选择执行版本')
      return false
    }
    if (!hasModelOptions.value) {
      ElMessage.warning('暂无可用模型，请先在“LLMs 配置”中添加')
      return false
    }
    if (!multiTurnForm.modelKey || !modelOptionMap.value.has(multiTurnForm.modelKey)) {
      ElMessage.warning('请选择执行模型')
      return false
    }
    const hasContent = multiTurnRounds.value.some((round) => round.content.trim())
    if (!hasContent) {
      ElMessage.warning('请至少填写一轮对话内容')
      return false
    }
  }
  return true
}

async function handleSubmit() {
  if (!validateForm()) {
    return
  }

  if (currentMode.value === 'same-model-different-version' && promptDetail.value) {
    if (!hasModelOptions.value) {
      ElMessage.warning('暂无可用模型，请先在“LLMs 配置”中添加模型')
      return
    }
    const modelInfo = resolveModelInfo(sameModelForm.modelKey)
    if (!modelInfo) {
      ElMessage.warning('请选择需要对比的模型')
      return
    }
    const { top_p, schema } = normalizeSameModelExtraParams()
    isSubmitting.value = true
    const createdRunIds: number[] = []
    const batchId = crypto.randomUUID()
    const jobName = baseForm.name.trim() || `${promptDetail.value.name} 对比测试`
    const notes = baseForm.description.trim() || undefined

    try {
      for (const versionId of sameModelForm.versionIds) {
        const version = versionOptions.value.find((item) => item.id === versionId)
        const schemaPayload: Record<string, unknown> = {
          ...schema,
          job_name: jobName,
          mode: currentMode.value,
          version_id: versionId,
          version_label: version?.version ?? `版本 #${versionId}`
        }
        const payload = {
          prompt_version_id: versionId,
          model_name: modelInfo.modelName,
          model_version: modelInfo.providerName,
          temperature: sameModelParams.temperature,
          repetitions: sameModelForm.testCount,
          top_p,
          schema: schemaPayload,
          notes,
          batch_id: batchId
        }
        const run = await createTestRun(payload)
        createdRunIds.push(run.id)
      }

      if (createdRunIds.length === 0) {
        ElMessage.info('未创建新的测试任务')
        return
      }

      ElMessage.success('测试任务已创建，正在跳转查看结果')
      const query: Record<string, string> = { mode: currentMode.value, runIds: createdRunIds.join(',') }
      if (createdRunIds.length > 1) {
        query.runIds = createdRunIds.join(',')
      }
      router.push({
        name: 'test-job-result',
        params: { id: createdRunIds[0] },
        query
      })
      return
    } catch (error) {
      ElMessage.error(extractErrorMessage(error, '创建测试任务失败'))
      return
    } finally {
      isSubmitting.value = false
    }
  }

  const fallbackPayload = {
    name: baseForm.name.trim(),
    description: baseForm.description.trim(),
    prompt_id: selectedPromptId.value,
    mode: currentMode.value,
    data:
      currentMode.value === 'same-version-different-model'
        ? {
            version_id: sameVersionForm.versionId,
            models: sameVersionForm.modelKeys.map((key) => resolveModelInfo(key)?.modelName ?? key)
          }
        : {
            version_id: multiTurnForm.versionId,
            model: resolveModelInfo(multiTurnForm.modelKey)?.modelName ?? multiTurnForm.modelKey,
            conversation: multiTurnRounds.value
              .filter((round) => round.content.trim())
              .map((round) => ({ role: round.role, content: round.content.trim() }))
          }
  }

  console.debug('mock create test job payload', fallbackPayload)
  ElMessage.success('已模拟创建测试任务，可在任务列表中查看（演示）')
}

function handleCancel() {
  if (fromPromptDetail.value && selectedPromptId.value) {
    router.push({ name: 'prompt-detail', params: { id: selectedPromptId.value } })
  } else {
    router.push({ name: 'test-job-management' })
  }
}

function goPromptDetail() {
  if (!selectedPromptId.value) {
    router.push({ name: 'prompt-management' })
    return
  }
  router.push({ name: 'prompt-detail', params: { id: selectedPromptId.value } })
}

function goPromptManagement() {
  router.push({ name: 'prompt-management' })
}

function goTestManagement() {
  router.push({ name: 'test-job-management' })
}

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object' && 'payload' in error) {
    const payload = (error as { payload?: unknown }).payload
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const detail = (payload as Record<string, unknown>).detail
      if (typeof detail === 'string' && detail.trim()) {
        return detail
      }
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

function extractPromptId(raw: unknown): number | null {
  if (typeof raw === 'string' || typeof raw === 'number') {
    const value = Number(raw)
    if (Number.isFinite(value) && value > 0) {
      return value
    }
  }
  return null
}
</script>

<style scoped>
.job-create-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-breadcrumb {
  font-size: 13px;
}

.breadcrumb-link {
  cursor: pointer;
  color: inherit;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-weak-color);
}

.mode-selector {
  white-space: nowrap;
}

.mode-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 20px;
  border-radius: 8px;
  background: rgba(64, 158, 255, 0.08);
}

.mode-summary__icon {
  font-size: 20px;
  color: var(--el-color-primary);
}

.mode-summary__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.mode-summary__desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-weak-color);
}

.test-form {
  max-width: 760px;
}

.form-tip {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--text-weak-color);
}

.temperature-group {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  max-width: 420px;
}

.temperature-slider {
  flex: 1;
}

.form-alert {
  margin-bottom: 12px;
}

.conversation-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.conversation-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--side-border-color);
  border-radius: 8px;
  background: var(--content-bg-color);
}

.conversation-item__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conversation-item__role {
  width: 120px;
}
</style>
