<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>{{ t('promptManagement.headerTitle') }}</h2>
        <p class="page-desc">{{ t('promptManagement.headerDescription') }}</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        {{ t('promptManagement.createPrompt') }}
      </el-button>
    </section>

    <div class="page-filters">
      <el-tabs v-model="activeClassKey" type="card" class="class-tabs">
        <el-tab-pane :label="t('promptManagement.allClasses')" name="all" />
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
          :placeholder="t('promptManagement.searchPlaceholder')"
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
          :placeholder="t('promptManagement.tagPlaceholder')"
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
        <el-select
          v-model="selectedMediaTypes"
          multiple
          collapse-tags
          collapse-tags-tooltip
          class="filter-item media-type-select"
          placeholder="媒体类型筛选"
          clearable
        >
          <el-option
            v-for="mediaType in mediaTypeOptions"
            :key="mediaType.value"
            :label="mediaType.label"
            :value="mediaType.value"
          >
            <div class="media-type-option">
              <el-icon :color="mediaType.color" class="media-type-icon">
                <component :is="mediaType.icon" />
              </el-icon>
              <span>{{ mediaType.label }}</span>
            </div>
          </el-option>
        </el-select>
        <el-select v-model="sortKey" class="filter-item sort-select" :placeholder="t('promptManagement.sortPlaceholder')">
          <el-option :label="t('promptManagement.sortDefault')" value="default" />
          <el-option :label="t('promptManagement.sortCreatedAt')" value="created_at" />
          <el-option :label="t('promptManagement.sortUpdatedAt')" value="updated_at" />
          <el-option :label="t('promptManagement.sortAuthor')" value="author" />
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
        <div v-for="prompt in paginatedPrompts" :key="prompt.id" class="card-grid__item">
          <el-card class="prompt-card" shadow="hover" @click="goDetail(prompt.id)">
            <div class="prompt-card__header">
              <div class="prompt-card__title-section">
                <div class="prompt-title-row">
                  <div class="media-type-indicator">
                    <el-icon 
                      :color="getMediaTypeInfo(prompt.media_type)?.color" 
                      class="media-type-card-icon"
                      :title="getMediaTypeInfo(prompt.media_type)?.label"
                    >
                      <component :is="getMediaTypeInfo(prompt.media_type)?.icon" />
                    </el-icon>
                  </div>
                  <div class="title-content">
                    <p class="prompt-class">{{ prompt.prompt_class.name }}</p>
                    <h3 class="prompt-title">{{ prompt.name }}</h3>
                  </div>
                </div>
                <div class="version-and-thumbnail">
                  <el-tag type="success" round size="small">
                    {{ t('promptManagement.currentVersion') }}
                    {{ prompt.current_version?.version ?? t('common.notEnabled') }}
                  </el-tag>
                  <!-- 图片类型显示缩略图 - 放在版本下面 -->
                  <div v-if="prompt.media_type === MediaType.IMAGE && prompt.attachments.length > 0" class="thumbnail-preview">
                    <el-image
                      v-for="attachment in prompt.attachments.slice(0, 3)"
                      :key="attachment.id"
                      :src="attachment.thumbnail_url || attachment.download_url"
                      :alt="attachment.original_filename"
                      fit="contain"
                      class="thumbnail-image"
                      :preview-src-list="[attachment.download_url]"
                    />
                    <div v-if="prompt.attachments.length > 3" class="thumbnail-more">
                      +{{ prompt.attachments.length - 3 }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <p class="prompt-desc">{{ prompt.description ?? t('common.descriptionNone') }}</p>
            <div class="prompt-meta">
              <div class="meta-item">
                <span class="meta-label">{{ t('promptManagement.author') }}</span>
                <span>{{ prompt.author ?? t('common.notSet') }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">{{ t('promptManagement.createdAt') }}</span>
                <span>{{ formatDate(prompt.created_at) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">{{ t('promptManagement.updatedAt') }}</span>
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
              <div class="card-actions">
                <el-button
                  type="primary"
                  text
                  size="small"
                  class="card-edit"
                  @click.stop="openEditDialog(prompt.id)"
                >
                  <el-icon><Edit /></el-icon>
                  <span>编辑</span>
                </el-button>
                <el-popconfirm
                  :title="t('promptManagement.confirmDelete', { name: prompt.name })"
                  :confirm-button-text="t('promptManagement.delete')"
                  :cancel-button-text="t('promptManagement.cancel')"
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
                      <span>删除</span>
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </el-card>
        </div>
      </div>
      <el-empty v-else :description="t('promptManagement.emptyDescription')" />
      
      <!-- 分页组件 -->
      <el-pagination
        v-if="filteredPrompts.length > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="filteredPrompts.length"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </template>

    <el-dialog 
      v-model="createDialogVisible" 
      :title="dialogMode === 'edit' ? '编辑提示词' : t('promptManagement.dialogTitle')" 
      width="95%"
      top="2vh"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      class="fullscreen-editor-dialog"
    >
      <el-alert
        v-if="!classOptions.length"
        :title="t('promptManagement.dialogAlert')"
        type="warning"
        show-icon
        class="dialog-alert"
      />
      
      <!-- 分类和标签选择 -->
      <div class="create-form-header">
        <el-form :model="promptForm" label-width="80px" class="header-form">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item :label="t('promptManagement.form.class')">
                <el-select v-model="promptForm.classId" :placeholder="t('promptManagement.form.classPlaceholder')" style="width: 100%">
                  <el-option
                    v-for="item in classOptions"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('promptManagement.form.tags')">
                <el-select
                  v-model="promptForm.tagIds"
                  multiple
                  collapse-tags
                  collapse-tags-tooltip
                  :placeholder="t('promptManagement.form.tagsPlaceholder')"
                  style="width: 100%"
                >
                  <el-option
                    v-for="tag in tagOptions"
                    :key="tag.id"
                    :label="tag.name"
                    :value="tag.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>

      <!-- 使用 PromptEditor 组件 -->
      <PromptEditor
        ref="promptEditorRef"
        :mode="dialogMode"
        :initial-data="editorInitialData"
        :disabled="isSubmitting"
        @submit="handleEditorSubmit"
        @cancel="handleEditorCancel"
      />
      
      <template #footer>
        <span></span> <!-- 空的 footer，让 PromptEditor 自己处理按钮 -->
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Delete, Plus, Search, Document, Picture, VideoPlay, Headset, EditPen, Edit } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listPrompts, createPrompt, updatePrompt, deletePrompt, getPrompt, type HttpError } from '../api/prompt'
import { listPromptClasses, type PromptClassStats } from '../api/promptClass'
import { listPromptTags, type PromptTagStats } from '../api/promptTag'
import type { Prompt, AttachmentInfo } from '../types/prompt'
import { MediaType } from '../types/prompt'
import { useI18n } from 'vue-i18n'
import PromptEditor from '../components/PromptEditor.vue'

type SortKey = 'default' | 'created_at' | 'updated_at' | 'author'

interface PromptFormState {
  name: string
  description: string
  author: string
  classId: number | null
  tagIds: number[]
  version: string
  content: string
  contentzh: string
  mediaType: MediaType
  attachments: AttachmentInfo[]
}

const router = useRouter()
const { t, locale } = useI18n()
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
const selectedMediaTypes = ref<MediaType[]>([])
const sortKey = ref<SortKey>('default')

// 分页相关状态
const currentPage = ref(1)
const pageSize = ref(50)

const classOptions = computed(() => {
  return promptClasses.value
    .map((item) => ({ id: item.id, name: item.name }))
    .sort((a, b) => a.name.localeCompare(b.name, locale.value))
})

const tagOptions = computed(() => {
  return promptTags.value
    .map((tag) => ({ id: tag.id, name: tag.name, color: tag.color }))
    .sort((a, b) => a.name.localeCompare(b.name, locale.value))
})

// 媒体类型选项
const mediaTypeOptions = computed(() => [
  {
    value: MediaType.TEXT,
    label: '文本',
    icon: EditPen,
    color: '#409EFF'
  },
  {
    value: MediaType.IMAGE,
    label: '图片',
    icon: Picture,
    color: '#67C23A'
  },
  {
    value: MediaType.DOCUMENT,
    label: '文档',
    icon: Document,
    color: '#E6A23C'
  },
  {
    value: MediaType.AUDIO,
    label: '音频',
    icon: Headset,
    color: '#F56C6C'
  },
  {
    value: MediaType.VIDEO,
    label: '视频',
    icon: VideoPlay,
    color: '#909399'
  }
])

// 获取媒体类型信息
function getMediaTypeInfo(mediaType: MediaType) {
  return mediaTypeOptions.value.find(option => option.value === mediaType)
}

const dateFormatter = computed(
  () =>
    new Intl.DateTimeFormat(locale.value === 'zh-CN' ? 'zh-CN' : 'en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
)

function formatDate(value: string | null | undefined) {
  if (!value) return '--'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : dateFormatter.value.format(date)
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
        const cmp = authorA.localeCompare(authorB, locale.value)
        if (cmp !== 0) return cmp
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      })
      break
    default:
      sorted.sort((a, b) => {
        const diff = new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        if (diff !== 0) return diff
        return a.name.localeCompare(b.name, locale.value)
      })
  }
  return sorted
}

const filteredPrompts = computed(() => {
  const keyword = searchKeyword.value
  const activeClass = activeClassKey.value
  const tagIds = selectedTagIds.value
  const mediaTypes = selectedMediaTypes.value

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
    if (mediaTypes.length && !mediaTypes.includes(prompt.media_type)) {
      return false
    }
    return true
  })

  return sortPrompts(list)
})

// 分页后的数据
const paginatedPrompts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredPrompts.value.slice(start, end)
})

const createDialogVisible = ref(false)
const editDialogVisible = ref(false)
const editingPromptId = ref<number | null>(null)
const dialogMode = ref<'create' | 'edit'>('create')

const promptForm = reactive<PromptFormState>({
  name: '',
  description: '',
  author: '',
  classId: null,
  tagIds: [],
  version: '',
  content: '',
  contentzh: '',
  mediaType: MediaType.TEXT,
  attachments: []
})

// PromptEditor 相关数据
const promptEditorRef = ref<InstanceType<typeof PromptEditor>>()

// 计算传递给 PromptEditor 的初始数据
const editorInitialData = computed(() => ({
  name: promptForm.name,
  description: promptForm.description,
  author: promptForm.author,
  media_type: promptForm.mediaType,
  content: promptForm.content,
  contentzh: promptForm.contentzh,
  version: promptForm.version,
  attachments: promptForm.attachments
}))

function resetPromptForm() {
  promptForm.name = ''
  promptForm.description = ''
  promptForm.author = ''
  promptForm.classId = classOptions.value[0]?.id ?? null
  promptForm.tagIds = []
  promptForm.version = ''
  promptForm.content = ''
  promptForm.contentzh = ''
  promptForm.mediaType = MediaType.TEXT
  promptForm.attachments = []
}

function openCreateDialog() {
  dialogMode.value = 'create'
  editingPromptId.value = null
  resetPromptForm()
  createDialogVisible.value = true
}

async function openEditDialog(promptId: number) {
  dialogMode.value = 'edit'
  editingPromptId.value = promptId
  
  try {
    // 获取 Prompt 详情
    const prompt = await getPrompt(promptId)
    
    // 填充表单数据
    promptForm.name = prompt.name
    promptForm.description = prompt.description || ''
    promptForm.author = prompt.author || ''
    promptForm.classId = prompt.prompt_class.id
    promptForm.tagIds = prompt.tags.map(tag => tag.id)
    promptForm.mediaType = prompt.media_type
    promptForm.attachments = prompt.attachments || []
    
    // 填充当前版本的内容
    if (prompt.current_version) {
      promptForm.version = prompt.current_version.version
      promptForm.content = prompt.current_version.content
      promptForm.contentzh = prompt.current_version.contentzh || ''
    }
    
    createDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载 Prompt 数据失败')
    console.error('Failed to load prompt:', error)
  }
}

function isDeleting(id: number) {
  return deletingIds.value.includes(id)
}

// 处理 PromptEditor 提交事件
async function handleEditorSubmit(data: {
  name: string
  description: string
  author: string
  media_type: MediaType
  content: string
  contentzh?: string
  version: string
  summary: string
  attachments: AttachmentInfo[]
  pendingFiles?: File[]
}) {
  // 验证必填字段
  if (!data.name.trim()) {
    ElMessage.warning('请输入提示词名称')
    return
  }
  if (!data.version.trim()) {
    ElMessage.warning('请输入版本号')
    return
  }
  if (!promptForm.classId) {
    ElMessage.warning(t('promptManagement.messages.selectClass'))
    return
  }
  
  // 验证内容或附件
  if (data.media_type === MediaType.TEXT) {
    if (!data.content.trim()) {
      ElMessage.warning('请输入提示词内容')
      return
    }
  } else {
    // 检查是否有附件或待上传的文件
    const hasPendingFiles = data.pendingFiles && data.pendingFiles.length > 0
    if (!data.attachments.length && !hasPendingFiles) {
      ElMessage.warning('请上传至少一个附件')
      return
    }
  }

  if (isSubmitting.value) {
    return
  }

  isSubmitting.value = true
  const payload = {
    name: data.name.trim(),
    description: data.description.trim() || null,
    author: data.author.trim() || null,
    class_id: promptForm.classId,
    version: data.version.trim(),
    content: data.content || '',
    contentzh: data.contentzh?.trim() || null,
    tag_ids: promptForm.tagIds.length ? promptForm.tagIds : [],
    media_type: data.media_type
  }

  try {
    if (dialogMode.value === 'edit' && editingPromptId.value) {
      // 编辑模式：更新 Prompt
      await updatePrompt(editingPromptId.value, payload)
      
      // 如果有待关联的文件，关联它们
      if (data.pendingFiles && data.pendingFiles.length > 0 && promptEditorRef.value) {
        try {
          await promptEditorRef.value.attachPendingFiles(editingPromptId.value)
          ElMessage.success(`提示词更新成功，已关联 ${data.pendingFiles.length} 个附件`)
        } catch (attachError) {
          console.error('关联附件失败:', attachError)
          ElMessage.warning('提示词更新成功，但部分附件关联失败')
        }
      } else {
        ElMessage.success('提示词更新成功')
      }
    } else {
      // 创建模式：创建新 Prompt
      const createdPrompt = await createPrompt(payload)
      
      // 如果有待关联的文件，关联它们
      if (data.pendingFiles && data.pendingFiles.length > 0 && promptEditorRef.value) {
        try {
          await promptEditorRef.value.attachPendingFiles(createdPrompt.id)
          ElMessage.success(`提示词创建成功，已关联 ${data.pendingFiles.length} 个附件`)
        } catch (attachError) {
          console.error('关联附件失败:', attachError)
          ElMessage.warning('提示词创建成功，但部分附件关联失败')
        }
      } else {
        ElMessage.success(t('promptManagement.messages.createSuccess'))
      }
    }
    
    createDialogVisible.value = false
    resetPromptForm()
    editingPromptId.value = null
    await Promise.all([fetchPrompts(), fetchCollections()])
  } catch (error) {
    const errorMsg = dialogMode.value === 'edit' 
      ? '更新提示词失败' 
      : t('promptManagement.messages.createFailed')
    ElMessage.error(extractErrorMessage(error, errorMsg))
  } finally {
    isSubmitting.value = false
  }
}

// 处理 PromptEditor 取消事件
function handleEditorCancel() {
  createDialogVisible.value = false
  resetPromptForm()
}

function handleCreatePrompt() {
  if (!promptForm.name.trim() || !promptForm.version.trim() || !promptForm.content.trim()) {
    ElMessage.warning(t('promptManagement.messages.missingRequired'))
    return
  }
  if (!promptForm.classId) {
    ElMessage.warning(t('promptManagement.messages.selectClass'))
    return
  }
  if (isSubmitting.value) {
    return
  }

  if (!promptForm.classId) {
    ElMessage.warning(t('promptManagement.messages.selectClass'))
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
    tag_ids: promptForm.tagIds.length ? promptForm.tagIds : [],
    media_type: promptForm.mediaType
  }

  createPrompt(payload)
    .then(async () => {
      ElMessage.success(t('promptManagement.messages.createSuccess'))
      createDialogVisible.value = false
      await Promise.all([fetchPrompts(), fetchCollections()])
    })
    .catch((error) => {
      ElMessage.error(extractErrorMessage(error, t('promptManagement.messages.createFailed')))
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
    ElMessage.success(t('promptManagement.messages.deleteSuccess', { name: target.name }))
    await Promise.all([fetchPrompts(), fetchCollections()])
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, t('promptManagement.messages.deleteFailed')))
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
      return t('promptManagement.messages.resourceNotFound')
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

async function fetchPrompts() {
  try {
    // 设置较大的 limit 值以获取所有数据
    const data = await listPrompts({ limit: 10000 })
    prompts.value = data
    promptError.value = null
  } catch (error) {
    const message = extractErrorMessage(error, t('promptManagement.messages.loadPromptFailed'))
    promptError.value = message
    ElMessage.error(message)
    prompts.value = []
  }
}

// 分页处理函数
function handleSizeChange(newSize: number) {
  pageSize.value = newSize
  currentPage.value = 1 // 改变每页数量时重置到第一页
}

function handleCurrentChange(newPage: number) {
  currentPage.value = newPage
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
    const message = extractErrorMessage(error, t('promptManagement.messages.loadCollectionFailed'))
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

// 监听筛选条件变化，重置到第一页
watch([activeClassKey, searchKeyword, selectedTagIds, selectedMediaTypes, sortKey], () => {
  currentPage.value = 1
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

.media-type-select {
  max-width: 280px;
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

.media-type-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.media-type-icon {
  font-size: 14px;
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
  gap: 16px;
}

.prompt-card__title-section {
  flex: 1;
  display: flex;
  flex-direction: row;
  gap: 16px;
  align-items: flex-start;
}

.prompt-title-row {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.media-type-indicator {
  flex-shrink: 0;
  margin-top: 2px;
}

.media-type-card-icon {
  font-size: 20px;
}

.title-content {
  flex: 1;
  min-width: 0;
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
  word-break: break-word;
}

.version-and-thumbnail {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
  flex-shrink: 0;
}

.thumbnail-preview {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: nowrap;
}

.thumbnail-image {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  background-color: var(--el-fill-color-light);
  flex-shrink: 0;
  cursor: pointer;
  transition: transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumbnail-image:hover {
  transform: scale(1.05);
}

.thumbnail-image :deep(img) {
  object-fit: contain;
}

.thumbnail-more {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-secondary);
  font-size: 14px;
  font-weight: 500;
  flex-shrink: 0;
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  min-height: 60px;
}

.prompt-tags__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex: 1;
  align-content: flex-start;
}

.card-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.card-edit {
  color: var(--el-color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 16px;
  white-space: nowrap;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.card-edit:hover {
  background-color: var(--el-color-primary-light-9);
}

.card-delete {
  color: var(--el-color-danger);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 16px;
  white-space: nowrap;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.card-delete:hover {
  background-color: var(--el-color-danger-light-9);
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dialog-alert {
  margin-bottom: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .page-header__text h2 {
    font-size: 20px;
  }

  .filter-row {
    flex-direction: column;
    gap: 8px;
  }

  .filter-item {
    min-width: unset;
    max-width: unset;
  }

  .search-input,
  .tag-select,
  .media-type-select {
    max-width: unset;
  }

  .sort-select {
    width: 100%;
  }

  .card-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .prompt-card__header {
    flex-direction: column;
    gap: 12px;
  }

  .prompt-card__title-section {
    flex-direction: column;
    gap: 12px;
  }

  .prompt-title-row {
    flex-wrap: wrap;
    gap: 8px;
  }

  .media-type-indicator {
    align-self: flex-start;
  }

  .version-and-thumbnail {
    align-items: flex-start;
    width: 100%;
  }

  .thumbnail-preview {
    flex-wrap: wrap;
  }

  .thumbnail-image {
    width: 50px;
    height: 50px;
  }

  .thumbnail-more {
    width: 50px;
    height: 50px;
    font-size: 13px;
  }

  .prompt-meta {
    font-size: 12px;
  }

  .meta-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .meta-label {
    min-width: unset;
  }

  .prompt-tags {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .prompt-tags__list {
    justify-content: flex-start;
  }

  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .card-edit span {
    display: inline; /* 移动端也显示文字 */
  }
}

@media (max-width: 480px) {
  .page-header__text h2 {
    font-size: 18px;
  }

  .page-desc {
    font-size: 13px;
  }

  .class-tabs {
    --el-tabs-header-height: 36px;
  }

  .prompt-card {
    padding: 12px;
  }

  .prompt-title {
    font-size: 16px;
  }

  .thumbnail-image {
    width: 32px;
    height: 32px;
  }

  .thumbnail-more {
    width: 32px;
    height: 32px;
    font-size: 11px;
  }

  .media-type-card-icon {
    font-size: 18px;
  }
}

/* 新建对话框样式 */
.dialog-alert {
  margin-bottom: 16px;
}

.create-form-header {
  margin-bottom: 20px;
  padding: 16px;
  background-color: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
}

.header-form {
  margin: 0;
}

.header-form .el-form-item {
  margin-bottom: 0;
}

/* 媒体类型选项样式 */
.media-type-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.media-type-icon {
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .create-form-header .el-row {
    flex-direction: column;
  }
  
  .create-form-header .el-col {
    width: 100% !important;
    max-width: 100% !important;
  }
}

/* 全屏编辑器对话框样式 */
:deep(.fullscreen-editor-dialog) {
  .el-dialog {
    margin: 0 !important;
    max-height: 96vh;
    border-radius: 12px;
    overflow: hidden;
  }
  
  .el-dialog__header {
    padding: 16px 24px;
    background-color: var(--el-fill-color-blank);
    border-bottom: 1px solid var(--el-border-color-lighter);
    margin: 0;
  }
  
  .el-dialog__title {
    font-size: 18px;
    font-weight: 600;
  }
  
  .el-dialog__body {
    padding: 0;
    max-height: calc(96vh - 60px);
    overflow-y: auto;
  }
  
  .el-dialog__footer {
    display: none;
  }
}

/* 对话框内的表单头部样式 */
.create-form-header {
  padding: 20px 24px;
  background-color: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.header-form {
  margin: 0;
}

.dialog-alert {
  margin-bottom: 16px;
}

/* 分页组件样式 */
.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

/* 移动端优化 */
@media (max-width: 768px) {
  :deep(.fullscreen-editor-dialog) {
    .el-dialog {
      width: 100% !important;
      margin: 0 !important;
      max-height: 100vh;
      border-radius: 0;
    }
    
    .el-dialog__body {
      max-height: calc(100vh - 60px);
      overflow-y: auto;
    }
  }
  
  .create-form-header {
    padding: 16px;
  }
  
  .pagination {
    margin-top: 16px;
  }
  
  :deep(.pagination) {
    .el-pagination__sizes,
    .el-pagination__jump {
      display: none;
    }
  }
}
</style>
