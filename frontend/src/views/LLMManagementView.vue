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
      <el-row :gutter="0" class="provider-grid">
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
                  <p>{{ card.description }}</p>
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
              </div>
            </div>

            <transition name="fade">
              <div v-show="!card.collapsed" class="provider-card__body">
                <el-form label-position="top" class="provider-card__form">
                  <el-form-item label="API Key">
                    <el-input
                      class="provider-card__input"
                      :type="card.revealApiKey ? 'text' : 'password'"
                      v-model="card.apiKey"
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
                    <el-table-column label="操作" width="90" align="center">
                      <template #default="{ row }">
                        <el-button
                          type="danger"
                          text
                          size="small"
                          :icon="Delete"
                          @click="removeModel(card.id, row.id)"
                        >删除</el-button>
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
          <el-select v-model="llmForm.provider_name" placeholder="请选择提供方" @change="handleProviderChange">
            <el-option
              v-for="item in providerOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
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
        <el-form-item label="模型名称">
          <el-input v-model="llmForm.model_name" placeholder="如 gpt-4o-mini" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="llmForm.api_key" placeholder="请输入访问凭证" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Delete, Expand, Fold, Hide, Plus, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface ProviderOption {
  label: string
  value: string
}

interface ProviderModel {
  id: string
  name: string
  capability: string
  quota: string
}

interface ProviderCard {
  id: string
  providerName: string
  logo: string
  description: string
  apiKey: string
  baseUrl: string
  isCustom: boolean
  models: ProviderModel[]
  collapsed: boolean
  revealApiKey: boolean
}

const providerCards = ref<ProviderCard[]>([
  {
    id: 'openai',
    providerName: 'OpenAI',
    logo: '🧠',
    description: '客服机器人与编程助手的主力模型接入渠道。',
    apiKey: 'sk-openai-demo-************',
    baseUrl: 'https://api.openai.com/v1',
    isCustom: false,
    models: [
      {
        id: 'gpt-4o-mini',
        name: 'gpt-4o-mini',
        capability: '对话 / 代码',
        quota: '团队共享 200k tokens/日'
      },
      {
        id: 'gpt-4o',
        name: 'gpt-4o',
        capability: '推理 / 多模态',
        quota: '项目 A 独享 80k tokens/日'
      }
    ],
    collapsed: false,
    revealApiKey: false
  },
  {
    id: 'anthropic',
    providerName: 'Anthropic',
    logo: '🤖',
    description: '长文本总结与合规审阅的优选模型。',
    apiKey: 'sk-anthropic-demo-********',
    baseUrl: 'https://api.anthropic.com/v1',
    isCustom: false,
    models: [
      {
        id: 'claude-3-sonnet',
        name: 'Claude 3 Sonnet',
        capability: '长文本 / 合规',
        quota: '知识运营团队 50k tokens/日'
      }
    ],
    collapsed: false,
    revealApiKey: false
  },
  {
    id: 'internal-hub',
    providerName: '自建推理集群',
    logo: '🏢',
    description: '内网 LoRA 微调模型，支持业务特定问答。',
    apiKey: 'sk-internal-demo-********',
    baseUrl: 'https://llm.internal.company/api',
    isCustom: true,
    models: [
      {
        id: 'faq-bot-001',
        name: 'FAQ-Bot-001',
        capability: '客服 FAQ',
        quota: '客服团队 20k tokens/日'
      },
      {
        id: 'report-writer',
        name: 'Report-Writer',
        capability: '数据解读',
        quota: '数据分析组 10k tokens/日'
      }
    ],
    collapsed: false,
    revealApiKey: false
  }
])

const providerOptions: ProviderOption[] = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Azure OpenAI', value: 'azure-openai' },
  { label: 'Google', value: 'google' },
  { label: '自定义提供方', value: 'custom' }
]

const emojiOptions = ['🚀', '🧠', '✨', '🔥', '🤖', '📦', '🛰️', '🏢', '🦾', '🧩']

const dialogVisible = ref(false)
const emojiPopoverVisible = ref(false)
const llmForm = reactive({
  provider_name: providerOptions[0]?.value ?? '',
  base_url: '',
  model_name: '',
  api_key: '',
  logo_emoji: ''
})

const isCustomProvider = computed(() => llmForm.provider_name === 'custom')

function resetForm() {
  llmForm.provider_name = providerOptions[0]?.value ?? ''
  llmForm.base_url = ''
  llmForm.model_name = ''
  llmForm.api_key = ''
  llmForm.logo_emoji = ''
  emojiPopoverVisible.value = false
}

function openDialog() {
  resetForm()
  dialogVisible.value = true
}

function handleProviderChange(value: string) {
  if (value !== 'custom') {
    llmForm.base_url = ''
    llmForm.logo_emoji = ''
    emojiPopoverVisible.value = false
  }
}

function selectEmoji(emoji: string) {
  llmForm.logo_emoji = emoji
  emojiPopoverVisible.value = false
}

function toggleCollapse(id: string) {
  const target = providerCards.value.find((item) => item.id === id)
  if (target) {
    target.collapsed = !target.collapsed
  }
}

function toggleApiVisible(id: string) {
  const target = providerCards.value.find((item) => item.id === id)
  if (target) {
    target.revealApiKey = !target.revealApiKey
  }
}

async function removeModel(providerId: string, modelId: string) {
  const provider = providerCards.value.find((item) => item.id === providerId)
  if (!provider) return
  try {
    await ElMessageBox.confirm('确认删除该模型接入配置吗？删除后可在后续重新添加。', '提示', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    provider.models = provider.models.filter((model) => model.id !== modelId)
    ElMessage.success('模型已从当前提供方移除')
  } catch (error) {
    // 用户取消操作无需额外提示
  }
}

function handleAddModel(providerId: string) {
  const provider = providerCards.value.find((item) => item.id === providerId)
  if (!provider) return
  ElMessage.info(`暂未接入后端接口，先模拟向 ${provider.providerName} 添加模型的流程。`)
}

function handleCreate() {
  if (!llmForm.provider_name) {
    ElMessage.warning('请选择提供方')
    return
  }
  if (!llmForm.model_name.trim() || !llmForm.api_key.trim()) {
    ElMessage.warning('请填写模型名称和 API Key')
    return
  }
  if (isCustomProvider.value) {
    if (!llmForm.base_url.trim()) {
      ElMessage.warning('请输入自定义提供方的接口地址')
      return
    }
    if (!llmForm.logo_emoji.trim()) {
      ElMessage.warning('请选择一个 Logo Emoji')
      return
    }
  }

  const newProviderId = `${llmForm.provider_name}-${Date.now()}`
  providerCards.value.unshift({
    id: newProviderId,
    providerName: llmForm.provider_name === 'custom' ? '自定义提供方' : providerOptions.find((opt) => opt.value === llmForm.provider_name)?.label ?? '未命名提供方',
    logo: isCustomProvider.value ? llmForm.logo_emoji : '✨',
    description: '新接入的模型暂未补充描述，可后续在配置中心完善。',
    apiKey: llmForm.api_key,
    baseUrl: isCustomProvider.value ? llmForm.base_url : inferBaseUrl(llmForm.provider_name),
    isCustom: isCustomProvider.value,
    models: [
      {
        id: llmForm.model_name,
        name: llmForm.model_name,
        capability: '待标注',
        quota: '待配置'
      }
    ],
    collapsed: false,
    revealApiKey: false
  })

  ElMessage.success('已模拟新增提供方配置，真实保存需接入后端接口')
  dialogVisible.value = false
}

function inferBaseUrl(providerName: string): string {
  switch (providerName) {
    case 'openai':
      return 'https://api.openai.com/v1'
    case 'anthropic':
      return 'https://api.anthropic.com/v1'
    case 'azure-openai':
      return 'https://{your-resource-name}.openai.azure.com'
    case 'google':
      return 'https://generativelanguage.googleapis.com'
    default:
      return ''
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

