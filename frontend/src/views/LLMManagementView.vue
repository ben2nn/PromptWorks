<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>LLMs 管理</h2>
        <p class="page-desc">统一维护各大模型服务的凭证与接入配置，支撑跨团队的调用治理。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openDialog">新增提供方</el-button>
    </section>

    <template v-if="providerCards.length">
      <el-row :gutter="0" class="provider-grid" v-loading="loadingProviders">
        <el-col
          v-for="card in providerCards"
          :key="card.id"
          :span="24"
        >
          <el-card
            shadow="hover"
            class="provider-card"
            :class="{ 'provider-card--collapsed': card.collapsed }"
          >
            <div class="provider-card__header">
              <div class="provider-card__identity">
                <el-avatar :size="48" class="provider-card__avatar">
                  {{ card.logo }}
                </el-avatar>
                <div class="provider-card__text">
                  <h3>{{ card.providerName }}</h3>
                </div>
              </div>
              <div class="provider-card__actions">
                <el-tooltip :content="card.collapsed ? '展开查看详情' : '收起卡片'" placement="top">
                  <el-button
                    class="collapse-button"
                    text
                    size="small"
                    :icon="card.collapsed ? Expand : Fold"
                    @click="toggleCollapse(card.id)"
                  />
                </el-tooltip>
                <el-tooltip content="更新 API Key" placement="top">
                  <el-button
                    class="collapse-button"
                    text
                    size="small"
                    :icon="Edit"
                    @click="handleUpdateApiKey(card)"
                  />
                </el-tooltip>
                <el-tooltip content="删除提供方" placement="top">
                  <el-button
                    class="collapse-button"
                    text
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click="handleDeleteProvider(card)"
                  />
                </el-tooltip>
              </div>
            </div>

            <transition name="fade">
              <div v-show="!card.collapsed" class="provider-card__body">
                <el-form label-position="top" class="provider-card__form">
                  <el-form-item label="API Key（仅展示脱敏信息）">
                    <el-input
                      class="provider-card__input"
                      :type="card.revealApiKey ? 'text' : 'password'"
                      :model-value="card.maskedApiKey"
                      readonly
                    >
                      <template #suffix>
                        <el-icon class="icon-button" @click.stop="toggleApiVisible(card.id)">
                          <component :is="card.revealApiKey ? Hide : View" />
                        </el-icon>
                      </template>
                    </el-input>
                  </el-form-item>
                  <el-form-item label="访问地址">
                    <el-input
                      class="provider-card__input"
                      v-model="card.baseUrl"
                      :readonly="!card.isCustom"
                      :placeholder="card.isCustom ? '请输入自定义 API 域名' : '官方默认地址自动读取'"
                      @change="(value) => handleBaseUrlChange(card, value)"
                    />
                  </el-form-item>
                </el-form>

                <div class="provider-card__models">
                  <div class="provider-card__models-header">
                    <span>已接入模型</span>
                    <el-button
                      type="primary"
                      text
                      size="small"
                      :icon="Plus"
                      @click="handleAddModel(card.id)"
                    >添加模型</el-button>
                  </div>
                  <el-table
                    :data="card.models"
                    size="small"
                    border
                    empty-text="暂未配置模型"
                  >
                    <el-table-column prop="name" label="模型名称" min-width="140" />
                    <el-table-column prop="capability" label="能力标签" min-width="120" />
                    <el-table-column prop="quota" label="配额策略" min-width="140" />
                    <el-table-column label="操作" width="160" align="center">
                      <template #default="{ row }">
                        <div class="provider-card__model-actions">
                          <el-button
                            type="primary"
                            text
                            size="small"
                            :icon="CircleCheck"
                            :loading="checkingModelId === row.id"
                            :disabled="checkingModelId !== null && checkingModelId !== row.id"
                            @click="checkModel(card.id, row)">
                            检测
                          </el-button>
                          <el-button
                            type="danger"
                            text
                            size="small"
                            :icon="Delete"
                            @click="removeModel(card.id, row.id)"
                          >删除</el-button>
                        </div>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </transition>
          </el-card>
        </el-col>
      </el-row>
    </template>
    <el-empty v-else description="暂未接入任何大模型提供方" />

    <el-dialog v-model="dialogVisible" title="新增模型提供方" width="620px">
      <el-form :model="llmForm" label-width="120px" class="dialog-form">
        <el-form-item label="提供方">
          <el-select v-model="llmForm.provider_key" placeholder="请选择提供方" @change="handleProviderChange">
            <el-option
              v-for="item in providerOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="展示名称">
          <el-input v-model="llmForm.provider_name" placeholder="请输入提供方名称" />
        </el-form-item>
        <el-form-item v-if="isCustomProvider" label="接口地址">
          <el-input v-model="llmForm.base_url" placeholder="请输入自定义提供方 API 地址" />
        </el-form-item>
        <el-form-item v-if="isCustomProvider" label="Logo Emoji">
          <el-popover placement="bottom-start" width="260" trigger="click" v-model:visible="emojiPopoverVisible">
            <div class="emoji-grid">
              <span
                v-for="emoji in emojiOptions"
                :key="emoji"
                class="emoji-option"
                @click="selectEmoji(emoji)"
              >
                {{ emoji }}
              </span>
            </div>
            <template #reference>
              <el-input v-model="llmForm.logo_emoji" placeholder="请选择喜欢的 Emoji" />
            </template>
          </el-popover>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="llmForm.api_key" placeholder="请输入访问凭证" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="modelDialogVisible" title="添加模型" width="560px">
      <el-form :model="modelForm" label-width="120px" class="dialog-form">
        <el-form-item label="模型名称">
          <el-input v-model="modelForm.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="能力标签">
          <el-input v-model="modelForm.capability" placeholder="如 对话 / 推理（可选）" />
        </el-form-item>
        <el-form-item label="配额策略">
          <el-input v-model="modelForm.quota" placeholder="如 团队共享 100k tokens/日（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="modelSubmitLoading" @click="submitModel">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { CircleCheck, Delete, Edit, Expand, Fold, Hide, Plus, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createLLMModel,
  createLLMProvider,
  deleteLLMModel,
  deleteLLMProvider,
  listCommonLLMProviders,
  listLLMProviders,
  updateLLMProvider,
  invokeLLMProvider,
  RequestTimeoutError
} from '../api/llmProvider'
import type { KnownLLMProvider, LLMProvider } from '../types/llm'

interface ProviderOption {
  label: string
  value: string
}

interface ProviderCardModel {
  id: number
  name: string
  capability: string | null
  quota: string | null
}

interface ProviderCard {
  id: number
  providerKey?: string | null
  providerName: string
  logo: string
  maskedApiKey: string
  baseUrl: string
  isCustom: boolean
  models: ProviderCardModel[]
  collapsed: boolean
  revealApiKey: boolean
}

const loadingProviders = ref(false)
const providerCards = ref<ProviderCard[]>([])
const checkingModelId = ref<number | null>(null)

const commonProviders = ref<KnownLLMProvider[]>([])
const commonProviderMap = computed(() => {
  const map = new Map<string, KnownLLMProvider>()
  for (const item of commonProviders.value) {
    map.set(item.key, item)
  }
  return map
})

const providerOptions = computed<ProviderOption[]>(() => {
  const options = commonProviders.value.map((item) => ({
    label: item.name,
    value: item.key
  }))
  options.push({ label: '自定义提供方', value: 'custom' })
  return options
})

const emojiOptions = ['🚀', '🧠', '✨', '🔥', '🤖', '📦', '🛰️', '🏢', '🦾', '🧩']

const dialogVisible = ref(false)
const createLoading = ref(false)
const emojiPopoverVisible = ref(false)
const llmForm = reactive({
  provider_key: '',
  provider_name: '',
  base_url: '',
  api_key: '',
  logo_emoji: '',
  is_custom: false
})

const isCustomProvider = computed(() => llmForm.provider_key === 'custom')

function resetForm() {
  const firstOption = providerOptions.value[0]
  if (firstOption && firstOption.value !== 'custom') {
    applyCommonProvider(firstOption.value)
  } else {
    llmForm.provider_key = 'custom'
    llmForm.provider_name = ''
    llmForm.base_url = ''
    llmForm.logo_emoji = ''
    llmForm.is_custom = true
  }
  llmForm.api_key = ''
  emojiPopoverVisible.value = false
}

function applyCommonProvider(key: string) {
  const provider = commonProviderMap.value.get(key)
  llmForm.provider_key = key
  llmForm.is_custom = false
  if (provider) {
    llmForm.provider_name = provider.name
    llmForm.base_url = provider.base_url ?? ''
    llmForm.logo_emoji = provider.logo_emoji ?? '✨'
  } else {
    llmForm.provider_name = key
    llmForm.base_url = ''
    llmForm.logo_emoji = '✨'
  }
}

function openDialog() {
  resetForm()
  dialogVisible.value = true
}

function handleProviderChange(value: string) {
  if (value === 'custom') {
    llmForm.provider_key = 'custom'
    llmForm.provider_name = ''
    llmForm.base_url = ''
    llmForm.logo_emoji = ''
    llmForm.is_custom = true
    emojiPopoverVisible.value = false
    return
  }
  applyCommonProvider(value)
  emojiPopoverVisible.value = false
}

function selectEmoji(emoji: string) {
  llmForm.logo_emoji = emoji
  emojiPopoverVisible.value = false
}

function toggleCollapse(id: number) {
  const target = providerCards.value.find((item) => item.id === id)
  if (target) {
    target.collapsed = !target.collapsed
  }
}

function toggleApiVisible(id: number) {
  const target = providerCards.value.find((item) => item.id === id)
  if (target) {
    target.revealApiKey = !target.revealApiKey
  }
}

async function fetchProviders() {
  loadingProviders.value = true
  try {
    const existingCollapsed = new Map(providerCards.value.map((card) => [card.id, card.collapsed]))
    const existingReveal = new Map(providerCards.value.map((card) => [card.id, card.revealApiKey]))

    const providers = await listLLMProviders()
    providerCards.value = providers.map((provider) => mapProviderToCard(provider, existingCollapsed, existingReveal))
  } catch (error) {
    console.error(error)
    ElMessage.error('加载提供方信息失败，请稍后重试')
  } finally {
    loadingProviders.value = false
  }
}

function extractErrorMessage(error: unknown): string {
  if (error instanceof RequestTimeoutError) {
    return '检测超时，请稍后重试'
  }
  if (!error) {
    return '检测失败，请稍后重试'
  }
  const maybeError = error as any
  const detail = maybeError?.payload?.detail ?? maybeError?.detail
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  if (detail && typeof detail === 'object') {
    try {
      return JSON.stringify(detail)
    } catch (jsonError) {
      console.error('序列化错误详情失败', jsonError)
    }
  }
  if (typeof maybeError?.message === 'string' && maybeError.message.trim()) {
    return maybeError.message
  }
  return '检测失败，请稍后重试'
}

function mapProviderToCard(
  provider: LLMProvider,
  collapsedState: Map<number, boolean>,
  revealState: Map<number, boolean>
): ProviderCard {
  return {
    id: provider.id,
    providerKey: provider.provider_key,
    providerName: provider.provider_name,
    logo: provider.logo_emoji ?? '✨',
    maskedApiKey: provider.masked_api_key,
    baseUrl: provider.base_url ?? '',
    isCustom: provider.is_custom,
    models: provider.models.map((model) => ({
      id: model.id,
      name: model.name,
      capability: model.capability,
      quota: model.quota
    })),
    collapsed: collapsedState.get(provider.id) ?? false,
    revealApiKey: revealState.get(provider.id) ?? false
  }
}

async function fetchCommonOptions() {
  try {
    commonProviders.value = await listCommonLLMProviders()
  } catch (error) {
    console.error(error)
    ElMessage.warning('加载常用提供方配置失败，仅提供自定义选项')
    commonProviders.value = []
  }
}

async function initialize() {
  await fetchCommonOptions()
  await fetchProviders()
}

onMounted(() => {
  initialize()
})

async function handleCreate() {
  if (!llmForm.provider_name.trim()) {
    ElMessage.warning('请填写提供方名称')
    return
  }
  if (!llmForm.api_key.trim()) {
    ElMessage.warning('请填写 API Key')
    return
  }
  if (isCustomProvider.value) {
    if (!llmForm.base_url.trim()) {
      ElMessage.warning('请输入自定义提供方的接口地址')
      return
    }
  }

  createLoading.value = true
  try {
    const payload = {
      provider_name: llmForm.provider_name.trim(),
      api_key: llmForm.api_key.trim(),
      base_url: llmForm.base_url.trim() || undefined,
      logo_emoji: llmForm.logo_emoji.trim() || undefined,
      is_custom: isCustomProvider.value ? true : undefined,
      provider_key: !isCustomProvider.value ? llmForm.provider_key : undefined
    }
    await createLLMProvider(payload)
    ElMessage.success('提供方创建成功')
    dialogVisible.value = false
    await fetchProviders()
  } catch (error: any) {
    console.error(error)
    const message = error?.payload?.detail ?? '创建提供方失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    createLoading.value = false
  }
}

async function removeModel(providerId: number, modelId: number) {
  try {
    await ElMessageBox.confirm('确认删除该模型接入配置吗？删除后可在后续重新添加。', '提示', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch (error) {
    return
  }

  try {
    await deleteLLMModel(providerId, modelId)
    ElMessage.success('模型已移除')
    await fetchProviders()
  } catch (error: any) {
    console.error(error)
    const message = error?.payload?.detail ?? '删除模型失败，请稍后重试'
    ElMessage.error(message)
  }
}

const modelDialogVisible = ref(false)
const modelSubmitLoading = ref(false)
const activeProviderId = ref<number | null>(null)
const modelForm = reactive({
  name: '',
  capability: '',
  quota: ''
})

function handleAddModel(providerId: number) {
  activeProviderId.value = providerId
  modelForm.name = ''
  modelForm.capability = ''
  modelForm.quota = ''
  modelDialogVisible.value = true
}

async function submitModel() {
  if (!modelForm.name.trim()) {
    ElMessage.warning('请填写模型名称')
    return
  }
  const providerId = activeProviderId.value
  if (!providerId) {
    ElMessage.error('未找到对应的提供方，请重新操作')
    return
  }

  modelSubmitLoading.value = true
  try {
    await createLLMModel(providerId, {
      name: modelForm.name.trim(),
      capability: modelForm.capability.trim() || undefined,
      quota: modelForm.quota.trim() || undefined
    })
    ElMessage.success('模型添加成功')
    modelDialogVisible.value = false
    await fetchProviders()
  } catch (error: any) {
    console.error(error)
    const message = error?.payload?.detail ?? '添加模型失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    modelSubmitLoading.value = false
  }
}

async function handleBaseUrlChange(card: ProviderCard, value: string) {
  if (!card.isCustom) {
    return
  }
  const trimmed = (value ?? '').trim()
  if (!trimmed) {
    ElMessage.warning('自定义提供方必须配置访问地址')
    await fetchProviders()
    return
  }
  try {
    await updateLLMProvider(card.id, { base_url: trimmed })
    ElMessage.success('访问地址已更新')
    card.baseUrl = trimmed
  } catch (error: any) {
    console.error(error)
    const message = error?.payload?.detail ?? '更新访问地址失败，请稍后重试'
    ElMessage.error(message)
    await fetchProviders()
  }
}

async function handleDeleteProvider(card: ProviderCard) {
  const modelCount = card.models.length
  const message = `确认删除提供方“${card.providerName}”吗？此操作会同时删除其下的 ${modelCount} 个模型配置，且不可恢复。`
  try {
    await ElMessageBox.confirm(message, '删除确认', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch (error) {
    return
  }

  try {
    await deleteLLMProvider(card.id)
    ElMessage.success('提供方已删除')
    await fetchProviders()
  } catch (error: any) {
    console.error(error)
    const detail = error?.payload?.detail ?? '删除提供方失败，请稍后重试'
    ElMessage.error(detail)
  }
}

async function handleUpdateApiKey(card: ProviderCard) {
  try {
    const { value } = await ElMessageBox.prompt('请输入新的 API Key', '更新 API Key', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputType: 'password',
      inputPlaceholder: 'sk-...'
    })

    const newKey = value.trim()
    if (!newKey) {
      ElMessage.warning('请输入有效的 API Key')
      return
    }

    await updateLLMProvider(card.id, { api_key: newKey })
    ElMessage.success('API Key 已更新')
    await fetchProviders()
  } catch (error: any) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    console.error(error)
    const detail = error?.payload?.detail ?? '更新 API Key 失败，请稍后重试'
    ElMessage.error(detail)
  }
}

async function checkModel(providerId: number, model: ProviderCardModel) {
  if (checkingModelId.value !== null) {
    return
  }
  checkingModelId.value = model.id
  const startedAt = performance.now()
  try {
    await invokeLLMProvider(providerId, {
      messages: [
        {
          role: 'user',
          content: 'hello'
        }
      ],
      model_id: model.id,
      parameters: {}
    })
    const elapsed = Math.round(performance.now() - startedAt)
    ElMessage.success(`检测成功，用时 ${elapsed} ms`)
  } catch (error) {
    console.error('模型检测失败', error)
    const message = extractErrorMessage(error)
    ElMessage.error(message)
  } finally {
    checkingModelId.value = null
  }
}
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.provider-grid {
  margin-top: 8px;
  /* row-gap: 24px; */
}

.provider-grid .el-col {
  flex: 1 0 100%;
  margin-bottom: 24px;
}

.provider-grid .el-col:last-child {
  margin-bottom: 0;
}

.provider-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 180px;
}

.provider-card--collapsed {
  min-height: 120px;
}

.provider-card__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.provider-card__identity {
  display: flex;
  gap: 12px;
  align-items: center;
}

.provider-card__avatar {
  font-size: 24px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.provider-card__text h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.provider-card__text p {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-weak-color);
}

.provider-card__actions {
  display: flex;
  align-items: flex-start;
}

.collapse-button {
  padding: 0 8px;
}

.provider-card__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.provider-card__form {
  display: flex;
  flex-direction: column;
  /* gap: 12px; */
  width: 100%;
  max-width: 360px;
  margin-top: 15px;
}

.provider-card__form .el-form-item {
  width: 100%;
}
.provider-card__input {
  max-width: 360px;
  width: 100%;
}


.icon-button {
  cursor: pointer;
}

.provider-card__models {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.provider-card__models-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.provider-card__model-actions {
  display: flex;
  justify-content: center;
  gap: 6px;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(32px, 1fr));
  gap: 8px;
}

.emoji-option {
  cursor: pointer;
  font-size: 20px;
  text-align: center;
  line-height: 32px;
  border-radius: 8px;
  transition: background-color 0.2s ease;
}

.emoji-option:hover {
  background: rgba(64, 158, 255, 0.2);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
