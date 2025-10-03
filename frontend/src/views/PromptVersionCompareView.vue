<template>
  <div class="compare-page">
    <el-breadcrumb separator="/" class="compare-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptManagement">Prompt 管理</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptDetail">
          {{ promptDetail?.name ?? '未命名 Prompt' }}
        </span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>版本对比</el-breadcrumb-item>
    </el-breadcrumb>

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
    />

    <el-skeleton v-else-if="isLoading" animated :rows="5" />

    <el-empty v-else-if="!promptDetail" description="未找到 Prompt 信息" />

    <el-card v-else>
      <template #header>
        <div class="card-header">
          <div>
            <h3>版本差异对比</h3>
            <span class="card-subtitle">选择两个不同版本进行比对，左列为基准，右列为对比</span>
          </div>
          <el-tag v-if="promptDetail.current_version" size="small" type="success">
            当前版本：{{ promptDetail.current_version.version }}
          </el-tag>
        </div>
      </template>
      <el-form :inline="true" label-width="90px" class="compare-form">
        <el-form-item>
          <template #label>
            <span>基准版本</span>
          </template>
          <el-select
            v-model="baseVersion"
            placeholder="请选择基准版本"
            size="small"
            class="version-select"
          >
            <el-option
              v-for="version in versionOptions"
              :key="version.id"
              :label="version.version"
              :value="version.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <template #label>
            <span>对比版本</span>
          </template>
          <el-select
            v-model="targetVersion"
            placeholder="请选择对比版本"
            size="small"
            class="version-select"
          >
            <el-option
              v-for="version in versionOptions"
              :key="`target-${version.id}`"
              :label="version.version"
              :value="version.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <div v-if="base && target" class="diff-container">
        <div class="diff-header">
          <div class="diff-header__cell">
            <span>基准版本</span>
            <strong>{{ base.version }}</strong>
          </div>
          <div class="diff-header__cell">
            <span>对比版本</span>
            <strong>{{ target.version }}</strong>
          </div>
        </div>
        <div v-if="diffRows.length" class="diff-table">
          <div v-for="(row, index) in diffRows" :key="index" class="diff-row">
            <pre
              class="diff-cell"
              :class="row.left ? diffCellClass[row.left.type] : 'diff-cell--empty'"
            >{{ row.left?.text ?? '' }}</pre>
            <pre
              class="diff-cell"
              :class="row.right ? diffCellClass[row.right.type] : 'diff-cell--empty'"
            >{{ row.right?.text ?? '' }}</pre>
          </div>
        </div>
        <div v-else class="diff-empty">
          <el-empty description="两个版本内容一致，暂无差异" />
        </div>
      </div>
      <el-empty v-else description="请选择两个不同的版本进行对比" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { diffLines, type Change } from 'diff'
import { usePromptDetail } from '../composables/usePromptDetail'

interface DiffRowSegment {
  text: string
  type: 'added' | 'removed' | 'unchanged'
}

interface DiffRow {
  left: DiffRowSegment | null
  right: DiffRowSegment | null
}

const router = useRouter()
const route = useRoute()

const currentId = computed(() => {
  const raw = Number(route.params.id)
  return Number.isFinite(raw) && raw > 0 ? raw : null
})

const {
  prompt: promptDetail,
  loading: isLoading,
  error: errorMessage
} = usePromptDetail(currentId)

const versionOptions = computed(() => promptDetail.value?.versions ?? [])

const baseVersion = ref<number | null>(null)
const targetVersion = ref<number | null>(null)

watch(
  () => promptDetail.value,
  (value) => {
    if (!value || !value.versions.length) {
      baseVersion.value = null
      targetVersion.value = null
      return
    }
    const versions = value.versions
    const current = value.current_version?.id ?? versions[0]?.id ?? null
    baseVersion.value = current
    const fallback = versions.find((item) => item.id !== current)
    targetVersion.value = fallback?.id ?? null
  },
  { immediate: true }
)

watch([baseVersion, targetVersion], ([baseId, targetId]) => {
  const versions = versionOptions.value
  if (!baseId || !versions.length) {
    return
  }
  if (targetId && baseId === targetId) {
    const fallback = versions.find((item) => item.id !== baseId)
    targetVersion.value = fallback?.id ?? null
  }
})

const base = computed(() =>
  versionOptions.value.find((item) => item.id === baseVersion.value) ?? null
)
const target = computed(() =>
  versionOptions.value.find((item) => item.id === targetVersion.value) ?? null
)

const diffRows = computed<DiffRow[]>(() => {
  if (!base.value || !target.value) {
    return []
  }
  if (base.value.id === target.value.id) {
    return []
  }
  const changes: Change[] = diffLines(base.value.content, target.value.content)

  return changes.flatMap((change) => {
    const type: DiffRowSegment['type'] = change.added
      ? 'added'
      : change.removed
        ? 'removed'
        : 'unchanged'

    const lines = change.value.replace(/\n$/, '').split('\n')

    return lines.map((line) => {
      const text = line || ' '
      if (type === 'added') {
        return { left: null, right: { text, type } }
      }
      if (type === 'removed') {
        return { left: { text, type }, right: null }
      }
      return { left: { text, type }, right: { text, type } }
    })
  })
})

const diffCellClass: Record<DiffRowSegment['type'], string> = {
  added: 'diff-cell--added',
  removed: 'diff-cell--removed',
  unchanged: 'diff-cell--unchanged'
}

function goPromptManagement() {
  router.push({ name: 'prompt-management' })
}

function goPromptDetail() {
  if (!currentId.value) return
  router.push({ name: 'prompt-detail', params: { id: currentId.value } })
}
</script>

<style scoped>
.compare-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.compare-breadcrumb {
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
  gap: 12px;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-subtitle {
  font-size: 13px;
  color: var(--text-weak-color);
}

.compare-form {
  margin-bottom: 12px;
}

.version-select {
  width: 180px;
}

.diff-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.diff-header {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.diff-header__cell {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid var(--side-border-color);
  border-radius: 6px;
  background: var(--content-bg-color);
  font-size: 13px;
}

.diff-table {
  border: 1px solid var(--side-border-color);
  border-radius: 8px;
  background: var(--content-bg-color);
  max-height: 520px;
  overflow-y: auto;
}

.diff-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  border-bottom: 1px solid var(--side-border-color);
}

.diff-row:last-child {
  border-bottom: none;
}

.diff-cell {
  margin: 0;
  padding: 8px 12px;
  font-family: 'JetBrains Mono', 'Fira Mono', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  min-height: 24px;
}

.diff-cell--added {
  background: rgba(103, 194, 58, 0.12);
}

.diff-cell--removed {
  background: rgba(245, 108, 108, 0.15);
}

.diff-cell--unchanged {
  background: transparent;
}

.diff-cell--empty {
  background: transparent;
}

.diff-empty {
  padding: 32px 0;
}
</style>
