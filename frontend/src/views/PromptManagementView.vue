<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>Prompt 管理</h2>
        <p class="page-desc">集中管理提示词资产，快速检索分类、标签与作者信息。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建 Prompt</el-button>
    </section>

    <div class="page-filters">
      <el-tabs v-model="activeClassKey" type="card" class="class-tabs">
        <el-tab-pane label="全部分类" name="all" />
        <el-tab-pane
          v-for="item in classOptions"
          :key="item.id"
          :label="item.name"
          :name="String(item.id)"
        />
      </el-tabs>

      <div class="filter-row">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索标题 / 内容 / 作者"
          clearable
          class="filter-item search-input"
          :prefix-icon="Search"
        />
        <el-select
          v-model="selectedTagIds"
          multiple
          collapse-tags
          collapse-tags-tooltip
          class="filter-item tag-select"
          placeholder="选择标签筛选"
          clearable
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
        <el-select v-model="sortKey" class="filter-item sort-select" placeholder="排序方式">
          <el-option label="默认排序" value="default" />
          <el-option label="按创建时间" value="created_at" />
          <el-option label="按更新时间" value="updated_at" />
          <el-option label="按作者" value="author" />
        </el-select>
      </div>
    </div>

    <el-alert
      v-if="loadError"
      :title="loadError"
      type="error"
      show-icon
      class="data-alert"
    />

    <el-skeleton v-else-if="isLoading" animated :rows="6" />

    <template v-else>
      <div v-if="filteredPrompts.length" class="card-grid">
        <div v-for="prompt in filteredPrompts" :key="prompt.id" class="card-grid__item">
          <el-card class="prompt-card" shadow="hover" @click="goDetail(prompt.id)">
            <div class="prompt-card__header">
              <div>
                <p class="prompt-class">{{ prompt.prompt_class.name }}</p>
                <h3 class="prompt-title">{{ prompt.name }}</h3>
              </div>
              <el-tag type="success" round size="small">
                当前版本 {{ prompt.current_version?.version ?? '未启用' }}
              </el-tag>
            </div>
            <p class="prompt-desc">{{ prompt.description ?? '暂无描述' }}</p>
            <div class="prompt-meta">
              <div class="meta-item">
                <span class="meta-label">作者</span>
                <span>{{ prompt.author ?? '未设置' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">创建时间</span>
                <span>{{ formatDate(prompt.created_at) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">更新时间</span>
                <span>{{ formatDate(prompt.updated_at) }}</span>
              </div>
            </div>
            <div class="prompt-tags">
              <div class="prompt-tags__list">
                <el-tag
                  v-for="tag in prompt.tags"
                  :key="tag.id"
                  size="small"
                  effect="dark"
                  :style="{ backgroundColor: tag.color, borderColor: tag.color }"
                >
                  {{ tag.name }}
                </el-tag>
              </div>
              <el-popconfirm
                :title="`确认删除「${prompt.name}」吗？`"
                confirm-button-text="删除"
                cancel-button-text="取消"
                icon=""
                @confirm="() => handleDeletePrompt(prompt)"
              >
                <template #reference>
                  <el-button
                    type="danger"
                    text
                    size="small"
                    class="card-delete"
                    :loading="isDeleting(prompt.id)"
                    @click.stop
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </el-card>
        </div>
      </div>
      <el-empty v-else description="暂无 Prompt 数据，请点击右上角新建" />
    </template>

    <el-dialog v-model="createDialogVisible" title="新建 Prompt" width="720px">
      <el-alert
        v-if="!classOptions.length"
        title="当前还没有可用分类，请先在“分类管理”中新增分类。"
        type="warning"
        show-icon
        class="dialog-alert"
      />
      <el-form :model="promptForm" label-width="100px" class="dialog-form">
        <el-form-item label="标题">
          <el-input v-model="promptForm.name" placeholder="请输入 Prompt 标题" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="promptForm.author" placeholder="请输入作者（可选）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="promptForm.description"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="简要说明该 Prompt 的用途"
          />
        </el-form-item>
        <el-form-item label="所属分类">
          <el-select v-model="promptForm.classId" placeholder="请选择分类">
            <el-option
              v-for="item in classOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="promptForm.tagIds"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="请选择标签"
          >
            <el-option
              v-for="tag in tagOptions"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="版本号">
          <el-input v-model="promptForm.version" placeholder="如 v1.0.0" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="promptForm.content"
            type="textarea"
            :autosize="{ minRows: 6, maxRows: 12 }"
            placeholder="请输入 Prompt 文本内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="isSubmitting" @click="handleCreatePrompt">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Delete, Plus, Search } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listPrompts, createPrompt, deletePrompt, type HttpError } from '../api/prompt'
import { listPromptClasses, type PromptClassStats } from '../api/promptClass'
import { listPromptTags, type PromptTagStats } from '../api/promptTag'
import type { Prompt } from '../types/prompt'

type SortKey = 'default' | 'created_at' | 'updated_at' | 'author'

interface PromptFormState {
  name: string
  description: string
  author: string
  classId: number | null
  tagIds: number[]
  version: string
  content: string
}

const router = useRouter()
const prompts = ref<Prompt[]>([])
const promptClasses = ref<PromptClassStats[]>([])
const promptTags = ref<PromptTagStats[]>([])
const isLoading = ref(false)
const promptError = ref<string | null>(null)
const collectionError = ref<string | null>(null)
const loadError = computed(() => promptError.value ?? collectionError.value)
const isSubmitting = ref(false)
const deletingIds = ref<number[]>([])

const activeClassKey = ref('all')
const searchKeyword = ref('')
const selectedTagIds = ref<number[]>([])
const sortKey = ref<SortKey>('default')

const classOptions = computed(() => {
  return promptClasses.value
    .map((item) => ({ id: item.id, name: item.name }))
    .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
})

const tagOptions = computed(() => {
  return promptTags.value
    .map((tag) => ({ id: tag.id, name: tag.name, color: tag.color }))
    .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
})

const dateFormatter = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit'
})

function formatDate(value: string | null | undefined) {
  if (!value) return '--'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date)
}

function matchKeyword(keyword: string, prompt: Prompt) {
  if (!keyword.trim()) return true
  const target = keyword.trim().toLowerCase()
  const fields: (string | null | undefined)[] = [
    prompt.name,
    prompt.author,
    prompt.description,
    prompt.current_version?.content,
    prompt.versions.map((item) => item.content).join('\n')
  ]
  return fields.some((field) => field?.toLowerCase().includes(target))
}

function sortPrompts(list: Prompt[]) {
  const sorted = [...list]
  switch (sortKey.value) {
    case 'created_at':
      sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      break
    case 'updated_at':
      sorted.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      break
    case 'author':
      sorted.sort((a, b) => {
        const authorA = a.author ?? ''
        const authorB = b.author ?? ''
        const cmp = authorA.localeCompare(authorB, 'zh-CN')
        if (cmp !== 0) return cmp
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      })
      break
    default:
      sorted.sort((a, b) => {
        const diff = new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        if (diff !== 0) return diff
        return a.name.localeCompare(b.name, 'zh-CN')
      })
  }
  return sorted
}

const filteredPrompts = computed(() => {
  const keyword = searchKeyword.value
  const activeClass = activeClassKey.value
  const tagIds = selectedTagIds.value

  const list = prompts.value.filter((prompt) => {
    if (activeClass !== 'all' && String(prompt.prompt_class.id) !== activeClass) {
      return false
    }
    if (!matchKeyword(keyword, prompt)) {
      return false
    }
    if (tagIds.length) {
      const tagSet = new Set(prompt.tags.map((tag) => tag.id))
      if (!tagIds.every((tagId) => tagSet.has(tagId))) {
        return false
      }
    }
    return true
  })

  return sortPrompts(list)
})

const createDialogVisible = ref(false)
const promptForm = reactive<PromptFormState>({
  name: '',
  description: '',
  author: '',
  classId: null,
  tagIds: [],
  version: '',
  content: ''
})

function resetPromptForm() {
  promptForm.name = ''
  promptForm.description = ''
  promptForm.author = ''
  promptForm.classId = classOptions.value[0]?.id ?? null
  promptForm.tagIds = []
  promptForm.version = ''
  promptForm.content = ''
}

function openCreateDialog() {
  resetPromptForm()
  createDialogVisible.value = true
}

function isDeleting(id: number) {
  return deletingIds.value.includes(id)
}

function handleCreatePrompt() {
  if (!promptForm.name.trim() || !promptForm.version.trim() || !promptForm.content.trim()) {
    ElMessage.warning('请至少填写标题、版本号和内容')
    return
  }
  if (!promptForm.classId) {
    ElMessage.warning('请先选择分类')
    return
  }
  if (isSubmitting.value) {
    return
  }

  if (!promptForm.classId) {
    ElMessage.warning('请先选择分类')
    return
  }

  isSubmitting.value = true
  const payload = {
    name: promptForm.name.trim(),
    description: promptForm.description.trim() || null,
    author: promptForm.author.trim() || null,
    class_id: promptForm.classId,
    version: promptForm.version.trim(),
    content: promptForm.content,
    tag_ids: promptForm.tagIds.length ? promptForm.tagIds : []
  }

  createPrompt(payload)
    .then(async () => {
      ElMessage.success('新建 Prompt 成功')
      createDialogVisible.value = false
      await Promise.all([fetchPrompts(), fetchCollections()])
    })
    .catch((error) => {
      ElMessage.error(extractErrorMessage(error, '新建 Prompt 失败'))
    })
    .finally(() => {
      isSubmitting.value = false
    })
}

function goDetail(id: number) {
  router.push({ name: 'prompt-detail', params: { id: String(id) } })
}

async function handleDeletePrompt(target: Prompt) {
  if (isDeleting(target.id)) {
    return
  }
  deletingIds.value = [...deletingIds.value, target.id]
  try {
    await deletePrompt(target.id)
    ElMessage.success(`已删除「${target.name}」`)
    await Promise.all([fetchPrompts(), fetchCollections()])
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, '删除 Prompt 失败'))
  } finally {
    deletingIds.value = deletingIds.value.filter((item) => item !== target.id)
  }
}

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object' && 'status' in error) {
    const httpError = error as HttpError
    if (httpError.payload && typeof httpError.payload === 'object' && 'detail' in httpError.payload) {
      const detail = (httpError.payload as Record<string, unknown>).detail
      if (typeof detail === 'string' && detail.trim()) {
        return detail
      }
    }
    if (httpError.status === 404) {
      return '相关资源不存在'
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

async function fetchPrompts() {
  try {
    const data = await listPrompts({ limit: 200 })
    prompts.value = data
    promptError.value = null
  } catch (error) {
    const message = extractErrorMessage(error, '加载 Prompt 列表失败')
    promptError.value = message
    ElMessage.error(message)
    prompts.value = []
  }
}

async function fetchCollections() {
  try {
    const [classes, tagResponse] = await Promise.all([
      listPromptClasses(),
      listPromptTags()
    ])
    promptClasses.value = classes
    promptTags.value = tagResponse.items
    collectionError.value = null
  } catch (error) {
    const message = extractErrorMessage(error, '加载分类或标签数据失败')
    collectionError.value = message
    ElMessage.error(message)
    promptClasses.value = []
    promptTags.value = []
  }
}

async function bootstrap() {
  isLoading.value = true
  promptError.value = null
  collectionError.value = null
  await Promise.all([fetchPrompts(), fetchCollections()])
  isLoading.value = false
}

watch(classOptions, (options) => {
  if (activeClassKey.value !== 'all') {
    const exists = options.some((item) => String(item.id) === activeClassKey.value)
    if (!exists) {
      activeClassKey.value = 'all'
    }
  }
  if (!options.length) {
    promptForm.classId = null
    return
  }
  if (promptForm.classId === null || !options.some((item) => item.id === promptForm.classId)) {
    promptForm.classId = options[0].id
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
  void bootstrap()
})
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

.page-filters {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.class-tabs {
  --el-tabs-header-height: 40px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.filter-item {
  flex: 1;
  min-width: 200px;
}

.search-input {
  max-width: 320px;
}

.tag-select {
  max-width: 320px;
}

.sort-select {
  width: 180px;
  flex: initial;
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

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  align-items: stretch;
}

.data-alert {
  margin-bottom: 12px;
}

.card-grid__item {
  height: 100%;
}

.prompt-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border-radius: 12px;
  border: 1px solid transparent;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.prompt-card:hover {
  transform: translateY(-4px);
  border-color: #409eff33;
}

.prompt-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.prompt-class {
  margin: 0 0 4px;
  font-size: 13px;
  color: var(--text-weak-color);
}

.prompt-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.prompt-desc {
  margin: 16px 0;
  color: var(--header-text-color);
  font-size: 14px;
  line-height: 1.6;
  flex: 1;
}

.prompt-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: var(--text-weak-color);
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-label {
  font-weight: 500;
  min-width: 64px;
}

.prompt-tags {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.prompt-tags__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.card-delete {
  color: var(--el-color-danger);
  display: flex;
  align-items: center;
  padding: 4px;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dialog-alert {
  margin-bottom: 12px;
}
</style>
