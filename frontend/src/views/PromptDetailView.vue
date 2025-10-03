<template>
  <div class="detail-page">
    <el-breadcrumb separator="/" class="detail-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goHome">Prompt 管理</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>{{ detail?.name ?? 'Prompt 详情' }}</el-breadcrumb-item>
    </el-breadcrumb>

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
    />

    <el-skeleton v-else-if="isLoading" animated :rows="6" />

    <el-empty v-else-if="!detail" description="未找到 Prompt 详情" />

    <template v-else>
      <el-card class="info-card">
      <template #header>
        <div class="info-header">
          <div class="info-title-group">
            <p class="info-class">所属分类 · {{ detail.prompt_class.name }}</p>
            <h2 class="info-title">{{ detail.name }}</h2>
            <p class="info-desc">{{ detail.description ?? '暂无描述' }}</p>
          </div>
          <div class="info-meta">
            <el-tag type="success" effect="light">当前版本 {{ detail.current_version?.version ?? '未启用' }}</el-tag>
            <span>更新于 {{ formatDateTime(detail.updated_at) }}</span>
          </div>
        </div>
      </template>
      <el-descriptions :column="3" border size="small" class="info-descriptions">
        <el-descriptions-item label="作者">{{ detail.author ?? '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(detail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(detail.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="分类描述" :span="3">{{ detail.prompt_class.description ?? '暂无说明' }}</el-descriptions-item>
      </el-descriptions>
      <div class="info-tags">
        <div class="info-tags__list">
          <el-tag
            v-for="tag in detail.tags"
            :key="tag.id"
            size="small"
            effect="dark"
            :style="{ backgroundColor: tag.color, borderColor: tag.color }"
          >
            {{ tag.name }}
          </el-tag>
        </div>
        <el-button type="primary" link size="small" @click="openMetaDialog">
          编辑分类与标签
        </el-button>
      </div>
      <el-dialog v-model="metaDialogVisible" title="编辑分类与标签" width="520px">
        <el-alert
          v-if="metaError"
          :title="metaError"
          type="warning"
          show-icon
          class="meta-alert"
        />
        <el-form label-width="80px" class="meta-form">
          <el-form-item label="分类">
            <el-select
              v-model="selectedClassId"
              placeholder="请选择分类"
              :loading="isMetaLoading"
              :disabled="isMetaLoading || !classOptions.length"
            >
              <el-option
                v-for="option in classOptions"
                :key="option.id"
                :label="option.name"
                :value="option.id"
              />
            </el-select>
            <span v-if="!classOptions.length && !isMetaLoading" class="meta-empty-tip">
              暂无分类，请先在“分类管理”中创建
            </span>
          </el-form-item>
          <el-form-item label="标签">
            <el-select
              v-model="selectedTagIds"
              multiple
              collapse-tags
              collapse-tags-tooltip
              placeholder="选择标签"
              :loading="isMetaLoading"
            >
              <el-option
                v-for="tag in tagOptions"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              >
                <span class="tag-option">
                  <span class="tag-dot" :style="{ backgroundColor: tag.color }" />
                  {{ tag.name }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="closeMetaDialog" :disabled="isMetaSaving">取消</el-button>
          <el-button type="primary" :loading="isMetaSaving" :disabled="!canSaveMeta" @click="handleSaveMeta">
            保存
          </el-button>
        </template>
      </el-dialog>
      </el-card>

      <el-card class="content-card">
      <template #header>
        <div class="content-header">
          <div>
            <h3 class="content-title">Prompt 内容</h3>
            <span class="content-subtitle">左侧查看完整内容，右侧切换历史版本</span>
          </div>
          <div class="content-actions">
            <el-button size="small" @click="handleCreateVersion">新增版本</el-button>
            <el-button size="small" type="primary" @click="handleViewVersionCompare">版本对比</el-button>
          </div>
        </div>
      </template>
      <div class="content-body">
        <section class="content-main">
          <header class="content-main__meta">
            <div>
              <span class="content-main__label">版本号</span>
              <strong class="content-main__value">{{ selectedVersion?.version ?? '未选择版本' }}</strong>
            </div>
            <div>
              <span class="content-main__label">更新时间</span>
              <strong class="content-main__value">{{ formatDateTime(selectedVersion?.updated_at ?? selectedVersion?.created_at) }}</strong>
            </div>
          </header>
          <div class="content-scroll">
            <template v-if="selectedVersion">
              <pre class="content-text">{{ selectedVersion.content }}</pre>
            </template>
            <el-empty v-else description="暂无版本内容" />
          </div>
        </section>
        <aside class="content-history">
          <h4 class="history-title">历史版本</h4>
          <div class="history-scroll">
            <div
              v-for="version in detail.versions"
              :key="version.id"
              :class="['history-item', { 'is-active': version.id === selectedVersionId }]"
              @click="handleSelectVersion(version.id)"
            >
              <div class="history-item__meta">
                <span class="history-version">{{ version.version }}</span>
                <span class="history-date">{{ formatDateTime(version.updated_at) }}</span>
              </div>
              <p class="history-preview">{{ summarizeContent(version.content) }}</p>
            </div>
          </div>
        </aside>
      </div>
      </el-card>

      <el-card class="test-card">
      <template #header>
        <div class="test-header">
          <div>
            <h3 class="test-title">Prompt 测试记录</h3>
            <span class="test-subtitle">记录历史测试结果，支持快速备案</span>
          </div>
          <el-button type="primary" size="small" @click="handleCreateTest">新增测试</el-button>
        </div>
      </template>
      <el-table v-if="testRecords.length" :data="testRecords" size="small" border>
        <el-table-column prop="name" label="测试名称" min-width="140" />
        <el-table-column prop="model" label="模型" min-width="120" />
        <el-table-column prop="created_at" label="发起时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status]" size="small">{{ statusLabel[row.status] }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无测试记录，点击右上角新增测试" />
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePromptDetail } from '../composables/usePromptDetail'
import { listPromptClasses, type PromptClassStats } from '../api/promptClass'
import { listPromptTags, type PromptTagStats } from '../api/promptTag'
import { updatePrompt } from '../api/prompt'
import { ElMessage } from 'element-plus'

interface PromptTestRecord {
  id: number
  prompt_id: number
  name: string
  model: string
  status: 'success' | 'failed' | 'running'
  created_at: string
}

const router = useRouter()
const route = useRoute()

const currentId = computed(() => {
  const raw = Number(route.params.id)
  return Number.isFinite(raw) && raw > 0 ? raw : null
})

const {
  prompt: detail,
  loading: isLoading,
  error: errorMessage,
  refresh: refreshDetail
} = usePromptDetail(currentId)

const mockTestRecords: PromptTestRecord[] = [
  {
    id: 1,
    prompt_id: 1,
    name: '新手客服测试',
    model: 'gpt-4o',
    status: 'success',
    created_at: '2025-09-19T10:30:00+08:00'
  },
  {
    id: 2,
    prompt_id: 1,
    name: '版本 v1.3 回归',
    model: 'claude-3.5-sonnet',
    status: 'failed',
    created_at: '2025-09-15T16:20:00+08:00'
  },
  {
    id: 3,
    prompt_id: 2,
    name: '英文邮件场景验证',
    model: 'gpt-4.1-mini',
    status: 'running',
    created_at: '2025-09-22T09:05:00+08:00'
  }
]

const selectedVersionId = ref<number | null>(null)
const promptClasses = ref<PromptClassStats[]>([])
const promptTags = ref<PromptTagStats[]>([])
const metaError = ref<string | null>(null)
const isMetaLoading = ref(false)
const isMetaSaving = ref(false)
const selectedClassId = ref<number | null>(null)
const selectedTagIds = ref<number[]>([])
const metaDialogVisible = ref(false)

const classOptions = computed(() =>
  promptClasses.value
    .map((item) => ({ id: item.id, name: item.name }))
    .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
)

const tagOptions = computed(() =>
  promptTags.value
    .map((tag) => ({ id: tag.id, name: tag.name, color: tag.color }))
    .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
)

watch(
  () => detail.value,
  (value) => {
    if (!value) {
      selectedVersionId.value = null
      selectedClassId.value = null
      selectedTagIds.value = []
      return
    }
    selectedVersionId.value = value.current_version?.id ?? value.versions[0]?.id ?? null
    selectedClassId.value = value.prompt_class.id
    selectedTagIds.value = value.tags.map((tag) => tag.id)
  },
  { immediate: true }
)

const selectedVersion = computed(() => {
  const prompt = detail.value
  if (!prompt) {
    return null
  }
  const match = prompt.versions.find((item) => item.id === selectedVersionId.value)
  return match ?? prompt.current_version ?? null
})

const testRecords = computed(() => {
  if (!currentId.value) return []
  return mockTestRecords.filter((item) => item.prompt_id === currentId.value)
})

watch(classOptions, (options) => {
  if (!options.length) {
    selectedClassId.value = null
    return
  }
  if (selectedClassId.value === null) {
    selectedClassId.value = options[0].id
    return
  }
  const exists = options.some((item) => item.id === selectedClassId.value)
  if (!exists) {
    selectedClassId.value = options[0].id
  }
})

watch(tagOptions, (options) => {
  if (!options.length) {
    selectedTagIds.value = []
    return
  }
  const available = new Set(options.map((item) => item.id))
  selectedTagIds.value = selectedTagIds.value.filter((id) => available.has(id))
})

onMounted(() => {
  void fetchMeta()
})

const statusTagType = {
  success: 'success',
  failed: 'danger',
  running: 'warning'
} as const

const statusLabel = {
  success: '成功',
  failed: '失败',
  running: '进行中'
} as const

const canSaveMeta = computed(() => {
  const prompt = detail.value
  if (!prompt) {
    return false
  }
  if (selectedClassId.value === null) {
    return false
  }
  const originalClassId = prompt.prompt_class.id
  const originalTags = prompt.tags.map((tag) => tag.id).sort((a, b) => a - b)
  const currentTags = [...selectedTagIds.value].sort((a, b) => a - b)
  const tagsChanged =
    originalTags.length !== currentTags.length ||
    originalTags.some((value, index) => value !== currentTags[index])
  return selectedClassId.value !== originalClassId || tagsChanged
})

function extractMetaError(error: unknown): string {
  if (error && typeof error === 'object' && 'payload' in error) {
    const httpError = error as { status?: number; payload?: unknown }
    const payload = httpError.payload
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const detail = (payload as Record<string, unknown>).detail
      if (typeof detail === 'string' && detail.trim()) {
        return detail
      }
    }
    if (httpError.status === 404) {
      return '分类或标签数据未找到'
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return '加载分类或标签数据失败'
}

async function fetchMeta() {
  isMetaLoading.value = true
  metaError.value = null
  try {
    const [classes, tagResponse] = await Promise.all([
      listPromptClasses(),
      listPromptTags()
    ])
    promptClasses.value = classes
    promptTags.value = tagResponse.items
  } catch (error) {
    metaError.value = extractMetaError(error)
  } finally {
    isMetaLoading.value = false
  }
}

function resetMetaSelections() {
  const prompt = detail.value
  if (!prompt) {
    selectedClassId.value = null
    selectedTagIds.value = []
    return
  }
  selectedClassId.value = prompt.prompt_class.id
  selectedTagIds.value = prompt.tags.map((tag) => tag.id)
}

async function handleSaveMeta() {
  const prompt = detail.value
  if (!prompt) {
    return
  }
  if (selectedClassId.value === null) {
    ElMessage.warning('请选择分类')
    return
  }
  if (!canSaveMeta.value) {
    ElMessage.info('分类与标签未发生变化')
    return
  }
  isMetaSaving.value = true
  try {
    await updatePrompt(prompt.id, {
      class_id: selectedClassId.value,
      tag_ids: selectedTagIds.value
    })
    ElMessage.success('分类与标签已更新')
    await refreshDetail()
    await fetchMeta()
  } catch (error) {
    ElMessage.error(extractMetaError(error))
  } finally {
    isMetaSaving.value = false
  }
}

function openMetaDialog() {
  metaDialogVisible.value = true
  resetMetaSelections()
}

function closeMetaDialog() {
  metaDialogVisible.value = false
}

const dateTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit'
})

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return '--'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return dateTimeFormatter.format(date)
}

function summarizeContent(content: string) {
  const normalized = content.replace(/\s+/g, ' ').trim()
  if (!normalized) {
    return '暂无内容摘要'
  }
  return normalized.length > 80 ? `${normalized.slice(0, 80)}…` : normalized
}

function handleSelectVersion(id: number) {
  selectedVersionId.value = id
}

function handleViewVersionCompare() {
  if (!currentId.value) return
  router.push({ name: 'prompt-version-compare', params: { id: currentId.value } })
}

function handleCreateVersion() {
  if (!currentId.value) return
  router.push({ name: 'prompt-version-create', params: { id: currentId.value } })
}

function handleCreateTest() {
  if (!currentId.value) return
  router.push({ name: 'prompt-test-create', params: { id: currentId.value } })
}

function goHome() {
  router.push({ name: 'prompt-management' })
}
</script>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-breadcrumb {
  font-size: 13px;
}

.breadcrumb-link {
  cursor: pointer;
  color: inherit;
}

.info-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.info-title-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-class {
  margin: 0;
  font-size: 13px;
  color: var(--text-weak-color);
}

.info-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.info-desc {
  margin: 0;
  color: var(--text-weak-color);
  line-height: 1.6;
}

.info-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  font-size: 13px;
  color: var(--text-weak-color);
}

.info-descriptions :deep(.el-descriptions__body) {
  font-size: 13px;
}

.info-tags {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
}

.info-tags__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.info-tags :deep(.el-button.is-link) {
  padding: 0;
}

.meta-form {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-alert {
  margin-bottom: 12px;
}

.meta-empty-tip {
  margin-left: 12px;
  font-size: 12px;
  color: var(--text-weak-color);
}

.meta-actions {
  display: flex;
  gap: 8px;
}

.tag-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #909399;
}

.content-card {
  display: flex;
  flex-direction: column;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.content-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.content-subtitle {
  font-size: 13px;
  color: var(--text-weak-color);
}

.content-actions {
  display: flex;
  gap: 8px;
}

.content-body {
  flex: 1;
  display: flex;
  gap: 20px;
  align-items: stretch;
  min-height: 320px;
}

.content-main {
  flex: 2;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.content-main__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--text-weak-color);
}

.content-main__label {
  margin-right: 8px;
}

.content-main__value {
  font-size: 14px;
  color: var(--header-text-color);
}

.content-scroll {
  flex: 1;
  border: 1px solid var(--side-border-color);
  border-radius: 8px;
  background: var(--content-bg-color);
  padding: 16px;
  overflow-y: auto;
  max-height: 460px;
}

.content-text {
  margin: 0;
  white-space: pre-wrap;
  font-family: 'JetBrains Mono', 'Fira Mono', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
}

.content-history {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.history-scroll {
  flex: 1;
  border: 1px solid var(--side-border-color);
  border-radius: 8px;
  background: var(--content-bg-color);
  padding: 12px;
  overflow-y: auto;
  max-height: 460px;
}

.history-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.history-item + .history-item {
  margin-top: 8px;
}

.history-item.is-active,
.history-item:hover {
  background: rgba(64, 158, 255, 0.12);
}

.history-item__meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-weak-color);
}

.history-version {
  font-weight: 600;
  color: var(--header-text-color);
}

.history-preview {
  margin: 0;
  font-size: 13px;
  color: var(--header-text-color);
  line-height: 1.5;
}

.history-date {
  font-size: 12px;
}

.test-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.test-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.test-subtitle {
  font-size: 13px;
  color: var(--text-weak-color);
}

.test-card :deep(.el-table__cell) {
  font-size: 13px;
}
</style>
