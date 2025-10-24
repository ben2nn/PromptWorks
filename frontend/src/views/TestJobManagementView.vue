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
        <el-button
          v-if="showLegacyCreateButton"
          type="primary"
          :icon="Memo"
          @click="handleCreateTestJob"
        >
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
        <el-table-column :label="t('testJobManagement.table.columns.actions')" width="210" fixed="right">
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
              <el-button
                type="danger"
                link
                size="small"
                :loading="isJobDeleting(row.id)"
                @click="handleDelete(row)"
              >
                {{ t('testJobManagement.table.delete') }}
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteTestRun, listTestRuns, retryTestRun } from '../api/testRun'
import { deletePromptTestTask, listPromptTestTasks } from '../api/promptTest'
import type { TestRun } from '../types/testRun'
import type { PromptTestTask, PromptTestUnit } from '../types/promptTest'
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
  isNewResultPage: boolean
  newResultTaskId: number | null
}

const router = useRouter()
const { t, locale } = useI18n()
const retryingJobIds = ref<string[]>([])
const deletingJobIds = ref<string[]>([])
const showLegacyCreateButton = false

const testRuns = ref<TestRun[]>([])
const promptTestTasks = ref<PromptTestTask[]>([])
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
  const hasLegacyInProgress = testRuns.value.some(
    (run) => run.status === 'pending' || run.status === 'running'
  )
  const hasPromptTaskInProgress = promptTestTasks.value.some((task) => {
    const status = mapPromptTestTaskStatus(task.status)
    return status === 'pending' || status === 'running'
  })
  if (hasLegacyInProgress || hasPromptTaskInProgress) {
    pollingTimer.value = window.setTimeout(() => {
      void fetchAllJobs(false)
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

function isJobDeleting(id: string): boolean {
  return deletingJobIds.value.includes(id)
}

function markJobDeleting(id: string) {
  if (isJobDeleting(id)) return
  deletingJobIds.value = [...deletingJobIds.value, id]
}

function unmarkJobDeleting(id: string) {
  if (!isJobDeleting(id)) return
  deletingJobIds.value = deletingJobIds.value.filter((item) => item !== id)
}

const jobs = computed<AggregatedJobRow[]>(() => {
  const legacyRows = buildLegacyJobRows(testRuns.value)
  const promptTaskRows = buildPromptTestTaskRows(promptTestTasks.value)
  const merged = [...legacyRows, ...promptTaskRows]
  return merged.sort((a, b) => b.createdAt.localeCompare(a.createdAt))
})

function buildLegacyJobRows(runs: TestRun[]): AggregatedJobRow[] {
  const groups = new Map<string, TestRun[]>()
  for (const run of runs) {
    const key = run.batch_id ?? `run-${run.id}`
    const group = groups.get(key)
    if (group) {
      group.push(run)
    } else {
      groups.set(key, [run])
    }
  }

  const aggregateStatus = (items: TestRun[]): string => {
    if (items.some((item) => item.status === 'failed')) return 'failed'
    if (items.some((item) => item.status === 'running')) return 'running'
    if (items.some((item) => item.status === 'pending')) return 'pending'
    return 'completed'
  }

  return Array.from(groups.entries()).map(([key, items]) => {
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
    const mode =
      typeof schema.mode === 'string' ? String(schema.mode) : 'same-model-different-version'
    const failedRuns = ordered.filter((run) => run.status === 'failed')
    const failedRunIds = failedRuns.map((run) => run.id)
    const failureReasons = failedRuns
      .map((run) => resolveFailureReason(run))
      .filter((value): value is string => Boolean(value))
    const mergedReason = failureReasons.length
      ? Array.from(new Set(failureReasons)).join('；')
      : null
    let newResultTaskId: number | null = null
    const rawTaskId = schema.prompt_test_task_id
    if (typeof rawTaskId === 'number') {
      newResultTaskId = rawTaskId
    } else if (typeof rawTaskId === 'string' && rawTaskId.trim()) {
      const parsed = Number(rawTaskId)
      if (!Number.isNaN(parsed)) {
        newResultTaskId = parsed
      }
    }
    const isNewResultPage =
      typeof schema.new_result_page === 'boolean'
        ? schema.new_result_page
        : Boolean(newResultTaskId)

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
      mode,
      isNewResultPage,
      newResultTaskId
    }
  })
}

function buildPromptTestTaskRows(tasks: PromptTestTask[]): AggregatedJobRow[] {
  return tasks.map((task) => {
    const units = Array.isArray(task.units) ? task.units : []
    const unitExtras = units.map((unit) => extractRecord(unit.extra))
    const configRecord = extractRecord(task.config)
    const jobName = task.name?.trim() || t('testJobManagement.unnamedPrompt')
    const promptNames = deduplicateStrings(
      unitExtras
        .map((extra) => extractString(extra.prompt_name))
        .filter((value): value is string => Boolean(value))
    )
    const configPromptName = extractString(configRecord.prompt_name)
    const promptName =
      promptNames[0] ?? configPromptName ?? t('testJobManagement.unnamedPrompt')

    const versionLabels = deduplicateStrings(
      units
        .map((unit, index) => formatVersionLabel(unit, unitExtras[index]))
        .filter((label): label is string => Boolean(label))
    )
    if (!versionLabels.length) {
      versionLabels.push(
        t('testJobManagement.versionFallback', {
          id: task.prompt_version_id ?? '-'
        })
      )
    }

    const modelNames = deduplicateStrings(
      units.map((unit) => unit.model_name)
    )
    const providerNames = deduplicateStrings(
      unitExtras
        .map((extra) => extractString(extra.llm_provider_name))
        .filter((value): value is string => Boolean(value))
    )

    const temperatureValues = units
      .map((unit) => unit.temperature)
      .filter((value): value is number => typeof value === 'number' && !Number.isNaN(value))
    const roundsValues = units
      .map((unit) => unit.rounds)
      .filter((value): value is number => typeof value === 'number' && !Number.isNaN(value))

    const failureDetail = extractString(configRecord.last_error)
    const status = mapPromptTestTaskStatus(task.status)

    return {
      id: `task-${task.id}`,
      batchId: null,
      jobName,
      promptName,
      versionLabels,
      modelName: modelNames.length ? modelNames.join(' / ') : '--',
      providerName: providerNames.length ? providerNames.join(' / ') : null,
      temperature: temperatureValues.length ? temperatureValues[0] : Number.NaN,
      repetitions: roundsValues.length ? Math.max(...roundsValues) : 1,
      status,
      createdAt: task.created_at,
      updatedAt: task.updated_at,
      description: task.description ?? null,
      failureReason: status === 'failed' ? failureDetail : null,
      runIds: [],
      failedRunIds: [],
      mode: 'prompt-test-task',
      isNewResultPage: true,
      newResultTaskId: task.id
    }
  })
}

function deduplicateStrings(values: Array<string | null | undefined>): string[] {
  return Array.from(
    new Set(
      values
        .map((value) => (typeof value === 'string' ? value.trim() : ''))
        .filter((value) => value.length > 0)
    )
  )
}

function extractString(value: unknown): string | null {
  if (typeof value === 'string') {
    const trimmed = value.trim()
    return trimmed || null
  }
  return null
}

function extractRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }
  return {}
}

function mapPromptTestTaskStatus(status: string): 'pending' | 'running' | 'completed' | 'failed' {
  const normalized = typeof status === 'string' ? status.toLowerCase() : ''
  if (normalized === 'running') return 'running'
  if (normalized === 'completed') return 'completed'
  if (normalized === 'failed') return 'failed'
  return 'pending'
}

function formatVersionLabel(
  unit: PromptTestUnit,
  extraRecord?: Record<string, unknown>
): string | null {
  const extra = extraRecord ?? extractRecord(unit.extra)
  const label = extractString(extra.prompt_version)
  if (label) {
    return label
  }
  if (typeof unit.prompt_version_id === 'number') {
    return t('testJobManagement.versionFallback', { id: unit.prompt_version_id })
  }
  return null
}

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

async function fetchAllJobs(withLoading = true) {
  if (withLoading) {
    isLoading.value = true
  }
  errorMessage.value = null
  try {
    const [runs, tasks] = await Promise.all([
      listTestRuns({ limit: 200 }),
      listPromptTestTasks()
    ])
    testRuns.value = runs
    promptTestTasks.value = tasks
  } catch (error) {
    errorMessage.value = extractErrorMessage(error, t('testJobManagement.messages.loadFailed'))
    testRuns.value = []
    promptTestTasks.value = []
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
  void fetchAllJobs()
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
  if (job.isNewResultPage) {
    const targetId = job.newResultTaskId ?? job.id
    router.push({
      name: 'prompt-test-task-result',
      params: { taskId: targetId }
    })
    return
  }
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
    await fetchAllJobs(false)
  } catch (error) {
    ElMessage.error(
      extractErrorMessage(error, t('testJobManagement.messages.retryFailed'))
    )
  } finally {
    unmarkJobRetrying(job.id)
  }
}

async function handleDelete(job: AggregatedJobRow) {
  try {
    await ElMessageBox.confirm(
      t('testJobManagement.messages.deleteConfirmMessage', { name: job.jobName }),
      t('testJobManagement.messages.deleteConfirmTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
  } catch {
    return
  }

  if (isJobDeleting(job.id)) {
    return
  }

  markJobDeleting(job.id)
  try {
    if (job.mode === 'prompt-test-task' && job.newResultTaskId) {
      await deletePromptTestTask(job.newResultTaskId)
    } else if (job.runIds.length) {
      await Promise.all(job.runIds.map((runId) => deleteTestRun(runId)))
    } else {
      ElMessage.warning(t('testJobManagement.messages.deleteUnavailable'))
      return
    }
    ElMessage.success(t('testJobManagement.messages.deleteSuccess'))
    await fetchAllJobs(false)
  } catch (error) {
    ElMessage.error(
      extractErrorMessage(error, t('testJobManagement.messages.deleteFailed'))
    )
  } finally {
    unmarkJobDeleting(job.id)
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
