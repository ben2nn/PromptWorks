<template>
  <div class="detail-page">
    <el-breadcrumb separator="/" class="detail-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goHome">Prompt 管理</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>{{ detail.name }}</el-breadcrumb-item>
    </el-breadcrumb>

    <section class="detail-header">
      <div class="detail-header__text">
        <p class="detail-class">所属分类 · {{ detail.prompt_class.name }}</p>
        <h2 class="detail-title">{{ detail.name }}</h2>
        <p class="detail-subtitle">{{ detail.description ?? '暂无描述' }}</p>
      </div>
      <div class="detail-header__meta">
        <el-tag type="success" effect="light">当前版本 {{ detail.current_version?.version ?? '未启用' }}</el-tag>
        <span class="detail-updated">更新于 {{ formatDateTime(detail.updated_at) }}</span>
      </div>
    </section>

    <el-row :gutter="20" class="detail-body">
      <el-col :xs="24" :md="16" class="detail-left">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <h3>版本对比</h3>
              <span class="card-subtitle">选择任意两个版本对比内容差异</span>
            </div>
          </template>
          <el-form :inline="true" label-width="80px" class="diff-form">
            <el-form-item label="基准版本">
              <el-select v-model="baseVersion" size="small" @change="handleVersionChange">
                <el-option
                  v-for="version in versionOptions"
                  :key="version"
                  :value="version"
                  :label="version"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="对比版本">
              <el-select v-model="compareVersion" size="small" @change="handleVersionChange">
                <el-option
                  v-for="version in versionOptions"
                  :key="version"
                  :value="version"
                  :label="version"
                />
              </el-select>
            </el-form-item>
          </el-form>
          <div v-if="!diffSegments.length" class="diff-empty">
            <el-empty description="版本内容一致或暂无差异" />
          </div>
          <div v-else class="diff-viewer">
            <div
              v-for="(segment, index) in diffSegments"
              :key="index"
              :class="['diff-line', diffClassMap[segment.type]]"
            >
              <span class="diff-symbol">{{ diffSymbols[segment.type] }}</span>
              <pre class="diff-content">{{ segment.text }}</pre>
            </div>
          </div>
        </el-card>

        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <h3>版本历史</h3>
              <span class="card-subtitle">按时间查看每次迭代内容</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="version in detail.versions"
              :key="version.id"
              :timestamp="formatDateTime(version.created_at)"
              placement="top"
            >
              <div class="timeline-item">
                <div class="timeline-header">
                  <strong>{{ version.version }}</strong>
                  <span class="timeline-updated">{{ formatDateTime(version.updated_at) }}</span>
                </div>
                <p class="timeline-content">{{ summarizeContent(version.content) }}</p>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="8" class="detail-right">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <h3>Prompt 信息</h3>
              <span class="card-subtitle">基础字段与关联标签</span>
            </div>
          </template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="作者">{{ detail.author ?? '未设置' }}</el-descriptions-item>
            <el-descriptions-item label="分类描述">{{ detail.prompt_class.description ?? '暂无说明' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDateTime(detail.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatDateTime(detail.updated_at) }}</el-descriptions-item>
          </el-descriptions>
          <div class="detail-tags">
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
          <div class="detail-description">
            <h4>当前版本内容</h4>
            <pre class="detail-content">{{ detail.current_version?.content ?? '暂无内容' }}</pre>
          </div>
        </el-card>

        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <h3>测试工作台</h3>
              <span class="card-subtitle">后续将接入在线调试与回归测试</span>
            </div>
          </template>
          <el-empty description="测试功能占位，敬请期待" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { diffLines, type Change } from 'diff'
import { mockPrompts, getPromptById } from '../mocks/prompts'

interface DiffSegment {
  type: 'added' | 'removed' | 'unchanged'
  text: string
}

const router = useRouter()
const route = useRoute()

const fallbackId = mockPrompts[0]?.id ?? 1
const currentId = computed(() => {
  const value = Number(route.params.id)
  return Number.isNaN(value) ? fallbackId : value
})

const detail = computed(() => getPromptById(currentId.value) ?? mockPrompts[0])

const versionOptions = computed(() => detail.value?.versions.map((item) => item.version) ?? [])

const baseVersion = ref('')
const compareVersion = ref('')

watch(
  detail,
  (value) => {
    if (!value || !value.versions.length) {
      baseVersion.value = ''
      compareVersion.value = ''
      return
    }
    baseVersion.value = value.versions[0]?.version ?? ''
    compareVersion.value = value.versions[1]?.version ?? value.versions[0]?.version ?? ''
  },
  { immediate: true }
)

const diffSymbols: Record<DiffSegment['type'], string> = {
  added: '+',
  removed: '-',
  unchanged: ' '
}

const diffClassMap: Record<DiffSegment['type'], string> = {
  added: 'diff-line--added',
  removed: 'diff-line--removed',
  unchanged: 'diff-line--unchanged'
}

const diffSegments = computed<DiffSegment[]>(() => {
  const prompt = detail.value
  if (!prompt) {
    return []
  }
  const base = prompt.versions.find((item) => item.version === baseVersion.value)
  const target = prompt.versions.find((item) => item.version === compareVersion.value)

  if (!base || !target || base.version === target.version) {
    return []
  }

  const changes: Change[] = diffLines(base.content, target.content)

  return changes.flatMap((change) => {
    const type: DiffSegment['type'] = change.added ? 'added' : change.removed ? 'removed' : 'unchanged'
    const parts = change.value.replace(/\n$/, '').split('\n')
    return parts.map((line) => ({
      type,
      text: line || ' '
    }))
  })
})

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

function handleVersionChange() {
  if (baseVersion.value === compareVersion.value) {
    const fallback = versionOptions.value.find((item) => item !== baseVersion.value)
    if (fallback) {
      compareVersion.value = fallback
    }
  }
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

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.detail-header__text {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-class {
  margin: 0;
  font-size: 13px;
  color: var(--text-weak-color);
}

.detail-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.detail-subtitle {
  margin: 0;
  color: var(--text-weak-color);
  line-height: 1.6;
}

.detail-header__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  font-size: 13px;
  color: var(--text-weak-color);
}

.detail-updated {
  margin: 0;
}

.detail-body {
  margin-top: 8px;
}

.detail-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-subtitle {
  color: var(--text-weak-color);
  font-size: 13px;
}

.diff-form {
  margin-bottom: 16px;
}

.diff-viewer {
  border: 1px solid var(--side-border-color);
  border-radius: 8px;
  background: var(--content-bg-color);
  max-height: 360px;
  overflow: auto;
  font-family: 'JetBrains Mono', 'Fira Mono', Consolas, monospace;
}

.diff-line {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 6px 12px;
  border-bottom: 1px solid var(--side-border-color);
  white-space: pre-wrap;
}

.diff-line:last-child {
  border-bottom: none;
}

.diff-line--added {
  background: rgba(103, 194, 58, 0.12);
}

.diff-line--removed {
  background: rgba(245, 108, 108, 0.15);
}

.diff-line--unchanged {
  background: transparent;
}

.diff-symbol {
  width: 16px;
  text-align: center;
  font-weight: 600;
}

.diff-content {
  margin: 0;
  font-size: 13px;
}

.diff-empty {
  padding: 24px 0;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.timeline-updated {
  color: var(--text-weak-color);
  font-size: 12px;
}

.timeline-content {
  margin: 0;
  color: var(--header-text-color);
  font-size: 13px;
  line-height: 1.6;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
}

.detail-description h4 {
  margin: 0 0 8px;
  font-size: 16px;
}

.detail-content {
  margin: 0;
  padding: 12px;
  border-radius: 8px;
  background: var(--content-bg-color);
  white-space: pre-wrap;
  font-family: 'JetBrains Mono', 'Fira Mono', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
}
</style>
