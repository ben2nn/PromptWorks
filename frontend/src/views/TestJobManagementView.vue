<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>测试任务</h2>
        <p class="page-desc">统一查看批量测试任务与执行状态，后续将支持任务创建与重跑。</p>
      </div>
      <el-button type="primary" :icon="Memo" @click="handleCreateTestJob">新建测试任务</el-button>
    </section>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
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
        <el-table-column label="测试名称" min-width="260">
          <template #default="{ row }">
            <div class="table-name-cell">
              <span class="table-name__title">{{ row.jobName }}</span>
              <el-tag v-if="row.versionLabels.length > 1" size="small" type="info">
                {{ row.versionLabels.length }} 版本
              </el-tag>
            </div>
            <p class="table-subtitle">Prompt：{{ row.promptName }}</p>
            <p v-if="row.description" class="table-subtitle">备注：{{ row.description }}</p>
          </template>
        </el-table-column>
        <el-table-column label="模型" min-width="180">
          <template #default="{ row }">
            <div class="table-model">
              <span>{{ row.modelName }}</span>
              <span v-if="row.providerName" class="table-subtext">{{ row.providerName }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="版本列表" min-width="220">
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
        <el-table-column label="温度" width="100">
          <template #default="{ row }">{{ formatTemperature(row.temperature) }}</template>
        </el-table-column>
        <el-table-column label="测试次数" width="100">
          <template #default="{ row }">{{ row.repetitions }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status] ?? 'info'" size="small">
              {{ statusLabel[row.status] ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="最近更新" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.updatedAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewJob(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Memo } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { listTestRuns } from '../api/testRun'
import type { TestRun } from '../types/testRun'

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
  runIds: number[]
  mode: string
}

const router = useRouter()

const testRuns = ref<TestRun[]>([])
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

const tableEmptyText = computed(() => errorMessage.value ?? '暂未创建测试任务')

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
      const promptName = primary.prompt?.name ?? '未命名 Prompt'
      const jobNameCandidate = typeof schema.job_name === 'string' ? schema.job_name.trim() : ''
      const jobName = jobNameCandidate || primary.notes || promptName
      const versionLabels = ordered.map((run) => {
        const data = (run.schema ?? {}) as Record<string, unknown>
        const label = typeof data.version_label === 'string' ? data.version_label : null
        return label ?? run.prompt_version?.version ?? `版本 #${run.prompt_version_id}`
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
        runIds: ordered.map((run) => run.id),
        mode
      }
    })
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
})

const statusTagType = {
  completed: 'success',
  running: 'warning',
  failed: 'danger',
  pending: 'info'
} as const

const statusLabel = {
  completed: '已完成',
  running: '执行中',
  failed: '失败',
  pending: '排队中'
} as const

const dateTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit'
})

function formatDateTime(value: string) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return dateTimeFormatter.format(date)
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
    errorMessage.value = extractErrorMessage(error, '加载测试任务失败')
    testRuns.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  void fetchTestRuns()
})

function handleCreateTestJob() {
  router.push({ name: 'test-job-create' })
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
</style>
