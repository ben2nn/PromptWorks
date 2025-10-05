<template>
  <div class="result-page">
    <el-breadcrumb separator="/" class="page-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goTestManagement">{{ t('menu.testJob') }}</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item v-if="summary">{{ summary.title }}</el-breadcrumb-item>
      <el-breadcrumb-item>{{ t('testJobResult.breadcrumb.current') }}</el-breadcrumb-item>
    </el-breadcrumb>

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
    />

    <el-skeleton v-else-if="isLoading" animated :rows="6" />

    <el-empty v-else-if="!summary" :description="t('testJobResult.empty')" />

    <template v-else>
      <el-card class="info-card">
        <template #header>
          <div class="info-header">
            <div>
              <h2 class="info-title">{{ summary.title }}</h2>
              <div class="info-tags">
                <el-tag size="small" type="info">{{ modeLabelMap[comparisonMode] }}</el-tag>
                <el-tag :type="statusTagType[summary.status] ?? 'info'" size="small">
                  {{ statusLabel[summary.status] ?? summary.status }}
                </el-tag>
              </div>
            </div>
            <div class="info-actions">
              <el-button
                v-if="summary.status === 'failed'"
                type="danger"
                link
                :loading="isRetrying"
                :disabled="isRetrying"
                @click="handleRetry"
              >
                {{ t('testJobResult.info.retryButton') }}
              </el-button>
              <el-button
                type="primary"
                link
                :disabled="!summary.promptId || isRetrying"
                @click="goPrompt(summary.promptId)"
              >
                {{ t('testJobResult.info.viewPrompt') }}
              </el-button>
            </div>
          </div>
        </template>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item :label="t('testJobResult.info.fields.prompt')">
            {{ summary.promptName }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('testJobResult.info.fields.model')">
            {{ summary.modelName }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('testJobResult.info.fields.repetitionsLabel')">
            {{ t('testJobResult.info.fields.repetitionsValue', { count: summary.repetitions }) }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('testJobResult.info.fields.temperature')">
            {{ formatTemperature(summary.temperature) }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('testJobResult.info.fields.topP')">
            {{ formatTopP(summary.top_p) }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('testJobResult.info.fields.createdAt')">
            {{ formatDateTime(summary.createdAt) }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('testJobResult.info.fields.updatedAt')">
            {{ formatDateTime(summary.updatedAt) }}
          </el-descriptions-item>
        </el-descriptions>
        <div class="info-description">
          <span class="info-description__label">{{ t('testJobResult.info.descriptionLabel') }}</span>
          <span>{{ summary.description || t('testJobResult.info.descriptionFallback') }}</span>
        </div>
        <el-alert
          v-if="summary.status === 'failed' && summary.failureReason"
          :title="t('testJobResult.info.failureTitle')"
          :description="summary.failureReason"
          type="error"
          show-icon
          class="summary-failure-alert"
        />
        <div class="extra-params">
          <h4>{{ t('testJobResult.info.extraParams') }}</h4>
          <pre>{{ formattedExtraParams }}</pre>
        </div>
      </el-card>

      <el-card class="result-card">
        <template #header>
          <div class="result-header">
            <div>
              <h3 class="result-title">{{ t('testJobResult.resultCard.title') }}</h3>
              <p class="result-subtitle">{{ t('testJobResult.resultCard.subtitle') }}</p>
            </div>
            <div v-if="maxRounds > 1" class="round-switch">
              <el-button-group>
                <el-button
                  :icon="ArrowLeft"
                  plain
                  size="small"
                  :disabled="currentRound === 1"
                  @click="handlePrevRound"
                />
                <span class="round-switch__label">
                  {{ t('testJobResult.resultCard.roundLabel', { current: currentRound, total: maxRounds }) }}
                </span>
                <el-button
                  :icon="ArrowRight"
                  plain
                  size="small"
                  :disabled="currentRound === maxRounds"
                  @click="handleNextRound"
                />
              </el-button-group>
            </div>
          </div>
        </template>

        <div class="result-grid" :style="gridStyle">
          <div
            v-for="target in targets"
            :key="target.id"
            class="result-column"
          >
            <header class="result-column__header">
              <h4>{{ target.title }}</h4>
              <span class="result-column__meta">
                {{ t('testJobResult.resultCard.updatedAt', { time: formatDateTime(target.updatedAt) }) }}
              </span>
            </header>
            <section class="result-column__body">
              <el-alert
                v-if="target.status === 'failed' && target.failureReason"
                :title="t('testJobResult.resultCard.failureTitle')"
                :description="target.failureReason"
                type="error"
                show-icon
                class="result-alert"
              />
              <div class="result-section">
                <h5>{{ t('testJobResult.resultCard.promptContent') }}</h5>
                <p>{{ target.promptPreview }}</p>
              </div>
              <template v-if="getCurrentRun(target.id)">
                <div class="result-section">
                  <h5>{{ t('testJobResult.resultCard.modelOutput') }}</h5>
                  <p>{{ getCurrentRun(target.id)!.output }}</p>
                </div>
                <ul class="metric-list">
                  <li>
                    <span>{{ t('testJobResult.resultCard.tokens') }}</span>
                    <strong>{{ formatNumber(getCurrentRun(target.id)!.tokensUsed) }}</strong>
                  </li>
                  <li>
                    <span>{{ t('testJobResult.resultCard.latency') }}</span>
                    <strong>{{ formatLatency(getCurrentRun(target.id)!.latencyMs) }}</strong>
                  </li>
                </ul>
              </template>
              <el-empty v-else :description="t('testJobResult.resultCard.noResult')" />
            </section>
          </div>
        </div>
      </el-card>

      <el-card class="analysis-card">
        <template #header>
          <div class="analysis-header">
            <h3 class="analysis-title">{{ t('testJobResult.analysis.title') }}</h3>
            <span class="analysis-summary">
              {{
                t('testJobResult.analysis.summary', {
                  tokens: formatNumber(overallStats.averageTokens),
                  latency: formatLatency(overallStats.averageLatencyMs)
                })
              }}
            </span>
          </div>
        </template>
        <el-table :data="analysisRows" size="small" border :empty-text="t('testJobResult.analysis.empty')">
          <el-table-column prop="title" :label="t('testJobResult.analysis.columns.version')" min-width="200" />
          <el-table-column :label="t('testJobResult.analysis.columns.averageTokens')" min-width="150">
            <template #default="{ row }">{{ formatNumber(row.averageTokens) }}</template>
          </el-table-column>
          <el-table-column :label="t('testJobResult.analysis.columns.averageLatency')" min-width="140">
            <template #default="{ row }">{{ formatLatency(row.averageLatencyMs) }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getTestRun, retryTestRun } from '../api/testRun'
import type { TestResult, TestRun } from '../types/testRun'
import { useI18n } from 'vue-i18n'

type ComparisonMode =
  | 'same-model-different-version'
  | 'same-version-different-model'
  | 'multi-turn-same-model'

interface ResultView {
  id: number
  displayIndex: number
  output: string
  tokensUsed: number | null
  latencyMs: number | null
  createdAt: string
}

interface TargetView {
  id: number
  title: string
  versionId: number
  versionLabel: string
  promptPreview: string
  updatedAt: string
  status: TestRun['status']
  failureReason: string | null
  results: ResultView[]
}

interface AnalysisRow {
  id: number
  title: string
  averageTokens: number
  averageLatencyMs: number
}

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()

const requestedRunIds = computed(() => {
  const ids = new Set<number>()
  const primary = Number(route.params.id)
  if (Number.isFinite(primary) && primary > 0) {
    ids.add(primary)
  }
  const append = (value: unknown) => {
    if (typeof value === 'string') {
      value
        .split(',')
        .map((item) => Number(item.trim()))
        .filter((num) => Number.isFinite(num) && num > 0)
        .forEach((num) => ids.add(num))
    } else if (Array.isArray(value)) {
      value.forEach(append)
    }
  }
  append(route.query.runIds)
  return Array.from(ids)
})

const comparisonMode = computed<ComparisonMode>(() => {
  const value = route.query.mode
  if (value === 'same-version-different-model' || value === 'multi-turn-same-model') {
    return value
  }
  return 'same-model-different-version'
})

const runs = ref<TestRun[]>([])
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)
const currentRound = ref(1)
const isRetrying = ref(false)

const failedRuns = computed(() => runs.value.filter((run) => run.status === 'failed'))

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

const modeLabelMap = computed<Record<ComparisonMode, string>>(() => ({
  'same-model-different-version': t('testJobResult.modes.same-model-different-version'),
  'same-version-different-model': t('testJobResult.modes.same-version-different-model'),
  'multi-turn-same-model': t('testJobResult.modes.multi-turn-same-model')
}))

const statusTagType = {
  completed: 'success',
  running: 'warning',
  failed: 'danger',
  pending: 'info'
} as const

const statusLabel = computed<Record<string, string>>(() => ({
  completed: t('testJobResult.status.completed'),
  running: t('testJobResult.status.running'),
  failed: t('testJobResult.status.failed'),
  pending: t('testJobResult.status.pending')
}))

watch(
  requestedRunIds,
  () => {
    void fetchRuns()
  },
  { immediate: true }
)

const targets = computed<TargetView[]>(() =>
  runs.value.map((run) => {
    const schema = (run.schema ?? {}) as Record<string, unknown>
    const versionLabel = typeof schema.version_label === 'string'
      ? schema.version_label
      : run.prompt_version?.version ?? t('promptDetail.table.versionFallback', { id: run.prompt_version_id })
    const promptSnapshot = typeof schema.prompt_snapshot === 'string'
      ? schema.prompt_snapshot
      : run.prompt_version?.content ?? t('testJobResult.messages.promptContentEmpty')
    return {
      id: run.id,
      title: t('testJobResult.summary.targetTitle', { model: run.model_name, version: versionLabel }),
      versionId: run.prompt_version_id,
      versionLabel,
      promptPreview: summarizeText(promptSnapshot),
      updatedAt: run.prompt_version?.updated_at ?? run.updated_at,
      status: run.status,
      failureReason: resolveFailureReason(run),
      results: normalizeResults(run.results)
    }
  })
)

const gridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${Math.max(targets.value.length, 1)}, minmax(280px, 1fr))`
}))

const currentRoundResults = computed(() => {
  const map = new Map<number, ResultView | null>()
  const round = currentRound.value
  for (const target of targets.value) {
    const match =
      target.results.find((result) => result.displayIndex === round) ??
      target.results.find((result) => result.displayIndex === round - 1) ??
      null
    map.set(target.id, match)
  }
  return map
})

const maxRounds = computed(() => {
  const fromResults = targets.value.map((target) =>
    target.results.length
      ? Math.max(...target.results.map((result) => result.displayIndex))
      : 0
  )
  const repetitions = runs.value.length
    ? Math.max(...runs.value.map((run) => run.repetitions ?? 1))
    : 1
  return Math.max(repetitions, ...fromResults, 1)
})

watch(maxRounds, (max) => {
  if (currentRound.value > max) {
    currentRound.value = max
  }
})

const summary = computed(() => {
  if (!runs.value.length) {
    return null
  }
  const first = runs.value[0]
  const schema = (first.schema ?? {}) as Record<string, unknown>
  const promptName = first.prompt?.name ?? t('testJobResult.summary.promptFallback')
  const modelName = first.model_name
  const jobNameCandidate = typeof schema.job_name === 'string' ? schema.job_name.trim() : ''
  const jobName = jobNameCandidate || t('testJobResult.summary.defaultTitle', { prompt: promptName, model: modelName })
  const status = deriveStatus(runs.value)
  const createdAt = runs.value
    .map((run) => run.created_at)
    .reduce((prev, curr) => (prev < curr ? prev : curr))
  const updatedAt = runs.value
    .map((run) => run.updated_at)
    .reduce((prev, curr) => (prev > curr ? prev : curr))
  const failureReasons = failedRuns.value
    .map((run) => resolveFailureReason(run))
    .filter((value): value is string => Boolean(value))
  const failureReason = failureReasons.length
    ? Array.from(new Set(failureReasons)).join('；')
    : null
  return {
    title: jobName,
    promptName,
    promptId: first.prompt?.id ?? null,
    modelName,
    temperature: first.temperature,
    top_p: first.top_p,
    repetitions: maxRounds.value,
    createdAt,
    updatedAt,
    description: first.notes ?? '',
    status,
    failureReason,
    extraParams: first.schema ?? null
  }
})

const formattedExtraParams = computed(() => {
  const params = summary.value?.extraParams
  if (!params) {
    return '{}'
  }
  try {
    return JSON.stringify(params, null, 2)
  } catch (error) {
    void error
    return String(params)
  }
})

const analysisRows = computed<AnalysisRow[]>(() =>
  targets.value.map((target) => {
    const tokens = target.results
      .map((result) => result.tokensUsed)
      .filter((value): value is number => typeof value === 'number' && !Number.isNaN(value))
    const latency = target.results
      .map((result) => result.latencyMs)
      .filter((value): value is number => typeof value === 'number' && !Number.isNaN(value))
    const averageTokens = tokens.length
      ? tokens.reduce((acc, value) => acc + value, 0) / tokens.length
      : 0
    const averageLatency = latency.length
      ? latency.reduce((acc, value) => acc + value, 0) / latency.length
      : 0
    return {
      id: target.id,
      title: target.title,
      averageTokens,
      averageLatencyMs: averageLatency
    }
  })
)

const overallStats = computed(() => {
  if (!analysisRows.value.length) {
    return { averageTokens: 0, averageLatencyMs: 0 }
  }
  const aggregate = analysisRows.value.reduce(
    (acc, row) => {
      acc.tokens += row.averageTokens
      acc.latency += row.averageLatencyMs
      return acc
    },
    { tokens: 0, latency: 0 }
  )
  const count = analysisRows.value.length
  return {
    averageTokens: aggregate.tokens / count,
    averageLatencyMs: aggregate.latency / count
  }
})

watch(runs, () => {
  currentRound.value = 1
})

async function fetchRuns() {
  const ids = requestedRunIds.value
  if (!ids.length) {
    runs.value = []
    errorMessage.value = t('testJobResult.messages.noneSelected')
    return
  }
  isLoading.value = true
  errorMessage.value = null
  try {
    const data = await Promise.all(ids.map((id) => getTestRun(id)))
    runs.value = data
    if (!data.length) {
      errorMessage.value = t('testJobResult.messages.notFound')
    }
  } catch (error) {
    errorMessage.value = extractErrorMessage(error, t('testJobResult.messages.loadFailed'))
    runs.value = []
  } finally {
    isLoading.value = false
  }
}

function deriveStatus(list: TestRun[]) {
  if (list.some((run) => run.status === 'failed')) {
    return 'failed'
  }
  if (list.some((run) => run.status === 'running')) {
    return 'running'
  }
  if (list.some((run) => run.status === 'pending')) {
    return 'pending'
  }
  return 'completed'
}

function normalizeResults(results: TestResult[]): ResultView[] {
  return results
    .map((result) => ({
      id: result.id,
      displayIndex: result.run_index >= 1 ? result.run_index : result.run_index + 1,
      output: result.output,
      tokensUsed: result.tokens_used ?? null,
      latencyMs: result.latency_ms ?? null,
      createdAt: result.created_at
    }))
    .sort((a, b) => a.displayIndex - b.displayIndex)
}

function getCurrentRun(targetId: number): ResultView | null {
  return currentRoundResults.value.get(targetId) ?? null
}

function handlePrevRound() {
  if (currentRound.value > 1) {
    currentRound.value -= 1
  }
}

function handleNextRound() {
  if (currentRound.value < maxRounds.value) {
    currentRound.value += 1
  }
}

function goTestManagement() {
  router.push({ name: 'test-job-management' })
}

function goPrompt(promptId: number | null) {
  if (!promptId) return
  router.push({ name: 'prompt-detail', params: { id: promptId } })
}

async function handleRetry() {
  if (!failedRuns.value.length) {
    ElMessage.info(t('testJobResult.messages.noFailedRuns'))
    return
  }
  if (isRetrying.value) {
    return
  }
  isRetrying.value = true
  try {
    await Promise.all(failedRuns.value.map((run) => retryTestRun(run.id)))
    ElMessage.success(t('testJobResult.messages.retrySuccess'))
    await fetchRuns()
  } catch (error) {
    ElMessage.error(
      extractErrorMessage(error, t('testJobResult.messages.retryFailed'))
    )
  } finally {
    isRetrying.value = false
  }
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

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return '--'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return dateTimeFormatter.value.format(date)
}

const numberLocale = computed(() => (locale.value === 'zh-CN' ? 'zh-CN' : 'en-US'))

function formatNumber(value: number | null | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '--'
  }
  return value.toLocaleString(numberLocale.value)
}

function formatLatency(value: number | null | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '--'
  }
  return t('testJobResult.units.milliseconds', { value: Math.round(value) })
}

function formatTemperature(value: number | null | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '--'
  }
  return value.toFixed(2)
}

function formatTopP(value: number | null | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '--'
  }
  return value.toFixed(2)
}

function summarizeText(value: string) {
  const normalized = value.replace(/\s+/g, ' ').trim()
  if (!normalized) {
    return t('testJobResult.messages.summaryEmpty')
  }
  return normalized.length > 120 ? `${normalized.slice(0, 120)}…` : normalized
}

</script>

<style scoped>
.result-page {
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

.info-card,
.result-card,
.analysis-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
}

.info-tags {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.info-description {
  display: flex;
  gap: 8px;
  font-size: 13px;
  color: var(--text-weak-color);
}

.info-description__label {
  color: var(--header-text-color);
}

.summary-failure-alert {
  margin-top: 12px;
}

.extra-params h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
}

.extra-params pre {
  margin: 0;
  padding: 12px;
  background: var(--content-bg-color);
  border-radius: 8px;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.result-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.result-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-weak-color);
}

.round-switch {
  display: flex;
  align-items: center;
  gap: 12px;
}

.round-switch__label {
  font-size: 13px;
  color: var(--header-text-color);
}

.result-grid {
  display: grid;
  gap: 16px;
}

.result-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--side-border-color);
  border-radius: 12px;
  background: var(--content-bg-color);
}

.result-alert {
  margin-bottom: 12px;
}

.result-column__header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.result-column__meta {
  font-size: 12px;
  color: var(--text-weak-color);
}

.result-section h5 {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
}

.result-section p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
}

.metric-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.metric-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(64, 158, 255, 0.08);
  font-size: 12px;
}

.metric-list strong {
  font-size: 13px;
  color: var(--header-text-color);
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.analysis-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.analysis-summary {
  font-size: 13px;
  color: var(--text-weak-color);
}
</style>
