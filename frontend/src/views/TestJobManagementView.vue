<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>{{ t('testJobManagement.headerTitle') }}</h2>
        <p class="page-desc">{{ t('testJobManagement.headerDescription') }}</p>
      </div>
      <div class="page-header__actions">
        <el-button type="primary" plain :icon="Memo" @click="handleCreateNewTask">
          {{ t('testJobManagement.createButtonNew') }}
        </el-button>
        <el-button type="primary" :icon="Memo" @click="handleCreateTestJob">
          {{ t('testJobManagement.createButton') }}
        </el-button>
      </div>
    </section>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('testJobManagement.listTitle') }}</span>
        </div>
      </template>
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        class="table-alert"
      />
      <el-table
        :data="jobs"
        border
        stripe
        height="520"
        :empty-text="tableEmptyText"
        v-loading="isLoading"
      >
        <el-table-column :label="t('testJobManagement.table.columns.name')" min-width="260">
          <template #default="{ row }">
            <div class="table-name-cell">
              <span class="table-name__title">{{ row.jobName }}</span>
              <el-tag v-if="row.versionLabels.length > 1" size="small" type="info">
                {{ t('testJobManagement.versionCount', { count: row.versionLabels.length }) }}
              </el-tag>
            </div>
            <p class="table-subtitle">{{ t('testJobManagement.table.promptPrefix') }}{{ row.promptName }}</p>
            <p v-if="row.description" class="table-subtitle">
              {{ t('testJobManagement.table.notePrefix') }}{{ row.description }}
            </p>
            <p v-if="row.failureReason" class="table-failure">
              <el-icon class="table-failure__icon"><WarningFilled /></el-icon>
              <span class="table-failure__label">{{ t('testJobManagement.failureReasonPrefix') }}</span>
              <span class="table-failure__content">{{ row.failureReason }}</span>
            </p>
          </template>
        </el-table-column>
        <el-table-column :label="t('testJobManagement.table.columns.model')" min-width="180">
          <template #default="{ row }">
            <div class="table-model">
              <span>{{ row.modelName }}</span>
              <span v-if="row.providerName" class="table-subtext">{{ row.providerName }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="t('testJobManagement.table.columns.versions')" min-width="220">
          <template #default="{ row }">
            <el-space wrap>
              <el-tag
                v-for="label in row.versionLabels"
                :key="label"
                size="small"
                type="info"
              >
                {{ label }}
              </el-tag>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column :label="t('testJobManagement.table.columns.temperature')" width="100">
          <template #default="{ row }">{{ formatTemperature(row.temperature) }}</template>
        </el-table-column>
        <el-table-column :label="t('testJobManagement.table.columns.repetitions')" width="100">
          <template #default="{ row }">{{ row.repetitions }}</template>
        </el-table-column>
        <el-table-column :label="t('testJobManagement.table.columns.status')" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status] ?? 'info'" size="small">
              {{ statusLabel[row.status] ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('testJobManagement.table.columns.createdAt')" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column :label="t('testJobManagement.table.columns.updatedAt')" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.updatedAt) }}</template>
        </el-table-column>
        <el-table-column :label="t('testJobManagement.table.columns.actions')" width="150" fixed="right">
          <template #default="{ row }">
            <el-space size="4">
              <el-button type="primary" link size="small" @click="handleViewJob(row)">
                {{ t('testJobManagement.table.viewDetails') }}
              </el-button>
              <el-button
                v-if="row.failedRunIds.length"
                type="danger"
                link
                size="small"
                :loading="isJobRetrying(row.id)"
                @click="handleRetry(row)"
              >
                {{ t('testJobManagement.table.retry') }}
              </el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Memo, WarningFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listTestRuns, retryTestRun } from '../api/testRun'
import type { TestRun } from '../types/testRun'
import { useI18n } from 'vue-i18n'

interface AggregatedJobRow {
  id: string
  batchId: string | null
  jobName: string
  promptName: string
  versionLabels: string[]
  modelName: string
  providerName: string | null
  temperature: number
  repetitions: number
  status: string
  createdAt: string
  updatedAt: string
  description: string | null
  failureReason: string | null
  runIds: number[]
  failedRunIds: number[]
  mode: string
}

const router = useRouter()
const { t, locale } = useI18n()
const retryingJobIds = ref<string[]>([])

const testRuns = ref<TestRun[]>([])
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)
const pollingTimer = ref<number | null>(null)

function clearPolling() {
  if (pollingTimer.value !== null) {
    window.clearTimeout(pollingTimer.value)
    pollingTimer.value = null
  }
}

function scheduleNextPoll() {
  clearPolling()
  const hasInProgress = testRuns.value.some((run) => run.status === 'pending' || run.status === 'running')
  if (hasInProgress) {
    pollingTimer.value = window.setTimeout(() => {
      void fetchTestRuns()
    }, 3000)
  }
}

const tableEmptyText = computed(() => errorMessage.value ?? t('testJobManagement.empty'))

function resolveFailureReason(run: TestRun): string | null {
  const direct = typeof run.failure_reason === 'string' ? run.failure_reason.trim() : ''
  if (direct) {
    return direct
  }
  const schema = (run.schema ?? {}) as Record<string, unknown>
  const fallback = schema['last_error']
  if (typeof fallback === 'string') {
    const trimmed = fallback.trim()
    if (trimmed) {
      return trimmed
    }
  }
  return null
}

function isJobRetrying(id: string): boolean {
  return retryingJobIds.value.includes(id)
}

function markJobRetrying(id: string) {
  if (isJobRetrying(id)) return
  retryingJobIds.value = [...retryingJobIds.value, id]
}

function unmarkJobRetrying(id: string) {
  if (!isJobRetrying(id)) return
  retryingJobIds.value = retryingJobIds.value.filter((item) => item !== id)
}

const jobs = computed<AggregatedJobRow[]>(() => {
  const groups = new Map<string, TestRun[]>()
  for (const run of testRuns.value) {
    const key = run.batch_id ?? `run-${run.id}`
    const group = groups.get(key)
    if (group) {
      group.push(run)
    } else {
      groups.set(key, [run])
    }
  }

  const aggregateStatus = (runs: TestRun[]): string => {
    if (runs.some((item) => item.status === 'failed')) return 'failed'
    if (runs.some((item) => item.status === 'running')) return 'running'
    if (runs.some((item) => item.status === 'pending')) return 'pending'
    return 'completed'
  }

  return Array.from(groups.entries())
    .map(([key, items]) => {
      const ordered = [...items].sort((a, b) => a.created_at.localeCompare(b.created_at))
      const primary = ordered[0]
      const schema = (primary.schema ?? {}) as Record<string, unknown>
      const promptName = primary.prompt?.name ?? t('testJobManagement.unnamedPrompt')
      const jobNameCandidate = typeof schema.job_name === 'string' ? schema.job_name.trim() : ''
      const jobName = jobNameCandidate || primary.notes || promptName
      const versionLabels = ordered.map((run) => {
        const data = (run.schema ?? {}) as Record<string, unknown>
        const label = typeof data.version_label === 'string' ? data.version_label : null
        return (
          label ??
          run.prompt_version?.version ??
          t('testJobManagement.versionFallback', { id: run.prompt_version_id })
        )
      })
      const repetitions = Math.max(...ordered.map((run) => run.repetitions ?? 1))
      const createdAt = ordered.reduce(
        (acc, run) => (run.created_at < acc ? run.created_at : acc),
        ordered[0].created_at
      )
      const updatedAt = ordered.reduce(
        (acc, run) => (run.updated_at > acc ? run.updated_at : acc),
        ordered[0].updated_at
      )
      const mode = typeof schema.mode === 'string' ? String(schema.mode) : 'same-model-different-version'
      const failedRuns = ordered.filter((run) => run.status === 'failed')
      const failedRunIds = failedRuns.map((run) => run.id)
      const failureReasons = failedRuns
        .map((run) => resolveFailureReason(run))
        .filter((value): value is string => Boolean(value))
      const mergedReason = failureReasons.length
        ? Array.from(new Set(failureReasons)).join('；')
        : null

      return {
        id: key,
        batchId: primary.batch_id ?? null,
        jobName,
        promptName,
        versionLabels,
        modelName: primary.model_name,
        providerName: primary.model_version ?? null,
        temperature: primary.temperature,
        repetitions,
        status: aggregateStatus(ordered),
        createdAt,
        updatedAt,
        description: primary.notes,
        failureReason: mergedReason,
        runIds: ordered.map((run) => run.id),
        failedRunIds,
        mode
      }
    })
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
})

const statusTagType = {
  completed: 'success',
  running: 'warning',
  failed: 'danger',
  pending: 'warning'
} as const

const statusLabel = computed<Record<string, string>>(() => ({
  completed: t('testJobManagement.status.completed'),
  running: t('testJobManagement.status.running'),
  failed: t('testJobManagement.status.failed'),
  pending: t('testJobManagement.status.pending')
}))

const dateTimeFormatter = computed(
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

function formatDateTime(value: string) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return dateTimeFormatter.value.format(date)
}

function formatTemperature(value: number | null | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '--'
  }
  return value.toFixed(2)
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

async function fetchTestRuns() {
  isLoading.value = true
  errorMessage.value = null
  try {
    testRuns.value = await listTestRuns({ limit: 200 })
  } catch (error) {
    errorMessage.value = extractErrorMessage(error, t('testJobManagement.messages.loadFailed'))
    testRuns.value = []
  } finally {
    isLoading.value = false
    if (!errorMessage.value) {
      scheduleNextPoll()
    } else {
      clearPolling()
    }
  }
}

onMounted(() => {
  void fetchTestRuns()
})

onUnmounted(() => {
  clearPolling()
})

function handleCreateTestJob() {
  router.push({ name: 'test-job-create' })
}

function handleCreateNewTask() {
  router.push({ name: 'prompt-test-task-create' })
}

function handleViewJob(job: AggregatedJobRow) {
  if (!job.runIds.length) {
    return
  }
  const [firstId, ...rest] = job.runIds
  const query: Record<string, string> = {}
  if (rest.length) {
    query.runIds = rest.join(',')
  }
  query.mode = job.mode
  router.push({ name: 'test-job-result', params: { id: firstId }, query })
}

async function handleRetry(job: AggregatedJobRow) {
  if (!job.failedRunIds.length) {
    ElMessage.info(t('testJobManagement.messages.noFailedRuns'))
    return
  }
  if (isJobRetrying(job.id)) {
    return
  }
  markJobRetrying(job.id)
  try {
    await Promise.all(job.failedRunIds.map((runId) => retryTestRun(runId)))
    ElMessage.success(t('testJobManagement.messages.retrySuccess'))
    await fetchTestRuns()
  } catch (error) {
    ElMessage.error(
      extractErrorMessage(error, t('testJobManagement.messages.retryFailed'))
    )
  } finally {
    unmarkJobRetrying(job.id)
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

.page-header__actions {
  display: flex;
  gap: 8px;
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

.card-header {
  font-size: 14px;
  font-weight: 600;
}

.table-alert {
  margin-bottom: 12px;
}

.table-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-name__title {
  font-weight: 600;
}

.table-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--text-weak-color);
}

.table-model {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.table-subtext {
  font-size: 12px;
  color: var(--text-weak-color);
}

.table-failure {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--el-color-danger);
  display: flex;
  align-items: flex-start;
  gap: 4px;
  line-height: 1.4;
  white-space: normal;
}

.table-failure__icon {
  margin-top: 2px;
}

.table-failure__label {
  font-weight: 600;
}

.table-failure__content {
  word-break: break-word;
  flex: 1;
}
</style>
