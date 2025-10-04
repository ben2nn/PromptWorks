<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>用量管理</h2>
        <p class="page-desc">汇总各模型与团队的调用用量，为配额管理和成本分析提供数据支撑。</p>
      </div>
    </section>

    <div class="page-toolbar">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        unlink-panels
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :shortcuts="dateShortcuts"
      />
    </div>

    <el-row :gutter="16" class="overview-row">
      <el-col :xs="12" :sm="6" v-for="card in overviewCards" :key="card.key">
        <el-card shadow="hover" class="overview-card">
          <div class="overview-card__title">{{ card.title }}</div>
          <div class="overview-card__value">{{ formatNumber(card.value) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="detail-row">
      <el-col :xs="24" :lg="10" class="model-col">
        <el-card shadow="hover" class="model-card" v-loading="modelLoading">
          <template #header>
            <div class="model-card__header">
              <span>模型用量</span>
              <el-select v-model="sortKey" size="small" class="sort-select">
                <el-option label="按总 Token" value="totalTokens" />
                <el-option label="按调用次数" value="callCount" />
                <el-option label="按输入 Token" value="inputTokens" />
                <el-option label="按输出 Token" value="outputTokens" />
              </el-select>
            </div>
          </template>
          <el-table
            :data="sortedModels"
            border
            stripe
            highlight-current-row
            :row-class-name="rowClassName"
            @current-change="handleModelSelect"
            empty-text="暂无用量数据"
          >
            <el-table-column prop="modelName" label="模型" min-width="160">
              <template #default="{ row }">
                <span class="model-name">{{ row.modelName }}</span>
                <span class="provider-name">{{ row.provider }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="totalTokens" label="总 Token" width="120">
              <template #default="{ row }">{{ formatNumber(row.totalTokens) }}</template>
            </el-table-column>
            <el-table-column prop="callCount" label="调用次数" width="120">
              <template #default="{ row }">{{ formatNumber(row.callCount) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="14" class="chart-col">
        <el-card shadow="hover" class="chart-card" v-loading="chartLoading">
          <template #header>
            <div class="chart-card__header">
              <span>{{ activeModel?.modelName ?? '模型用量' }} - Token 趋势</span>
            </div>
          </template>
          <div ref="chartRef" class="usage-chart"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

import {
  getModelTimeseries,
  getUsageOverview,
  listModelUsage
} from '../api/usage'

interface UsagePoint {
  date: string
  inputTokens: number
  outputTokens: number
  callCount: number
}

interface ModelSummary {
  modelKey: string
  modelName: string
  provider: string
  totalTokens: number
  inputTokens: number
  outputTokens: number
  callCount: number
}

interface UsageOverviewTotals {
  totalTokens: number
  inputTokens: number
  outputTokens: number
  callCount: number
}

const now = new Date()
const sevenDaysAgo = new Date(now.getTime() - 6 * 24 * 60 * 60 * 1000)
const dateRange = ref<[Date, Date]>([sevenDaysAgo, now])

const dateShortcuts = [
  {
    text: '最近 7 天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 6)
      return [start, end] as [Date, Date]
    }
  },
  {
    text: '最近 30 天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 29)
      return [start, end] as [Date, Date]
    }
  }
]

const overviewData = ref<UsageOverviewTotals | null>(null)
const modelSummaries = ref<ModelSummary[]>([])
const chartMetrics = ref<UsagePoint[]>([])

const overviewLoading = ref(false)
const modelLoading = ref(false)
const chartLoading = ref(false)

const sortKey = ref<'totalTokens' | 'callCount' | 'inputTokens' | 'outputTokens'>('totalTokens')

const sortedModels = computed(() => {
  const list = modelSummaries.value
  return [...list].sort((a, b) => b[sortKey.value] - a[sortKey.value])
})

const activeModelKey = ref('')

const activeModel = computed(() =>
  sortedModels.value.find((item) => item.modelKey === activeModelKey.value)
)

const rangeKey = computed(() => {
  const [start, end] = dateRange.value
  const startKey = start ? formatDateParam(start) : ''
  const endKey = end ? formatDateParam(end) : ''
  return `${startKey}|${endKey}`
})

let modelDataToken = 0
let chartDataToken = 0

watch(
  rangeKey,
  () => {
    refreshUsageData()
  },
  { immediate: true }
)

watch(sortedModels, (list) => {
  if (!list.length) {
    activeModelKey.value = ''
    return
  }
  const exists = list.some((item) => item.modelKey === activeModelKey.value)
  if (!exists) {
    activeModelKey.value = list[0].modelKey
  }
})

const overviewCards = computed(() => {
  const fallback = modelSummaries.value.reduce(
    (acc, item) => {
      acc.totalTokens += item.totalTokens
      acc.inputTokens += item.inputTokens
      acc.outputTokens += item.outputTokens
      acc.callCount += item.callCount
      return acc
    },
    { totalTokens: 0, inputTokens: 0, outputTokens: 0, callCount: 0 }
  )
  const source: UsageOverviewTotals =
    overviewData.value ?? {
      totalTokens: fallback.totalTokens,
      inputTokens: fallback.inputTokens,
      outputTokens: fallback.outputTokens,
      callCount: fallback.callCount
    }
  return [
    { key: 'totalTokens', title: '总 Token 数', value: source.totalTokens },
    { key: 'inputTokens', title: '输入 Token 数', value: source.inputTokens },
    { key: 'outputTokens', title: '输出 Token 数', value: source.outputTokens },
    { key: 'callCount', title: '调用次数', value: source.callCount }
  ]
})

function formatDateParam(date: Date): string {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getDateParams() {
  const [start, end] = dateRange.value
  return {
    start_date: start ? formatDateParam(start) : undefined,
    end_date: end ? formatDateParam(end) : undefined
  }
}

async function refreshUsageData() {
  const currentToken = ++modelDataToken
  const params = getDateParams()
  overviewLoading.value = true
  modelLoading.value = true
  chartLoading.value = true
  try {
    const [overviewResp, modelResp] = await Promise.all([
      getUsageOverview(params),
      listModelUsage(params)
    ])
    if (currentToken !== modelDataToken) {
      return
    }

    overviewData.value = overviewResp
      ? {
          totalTokens: overviewResp.total_tokens,
          inputTokens: overviewResp.input_tokens,
          outputTokens: overviewResp.output_tokens,
          callCount: overviewResp.call_count
        }
      : null

    const mappedModels = modelResp.map<ModelSummary>((item) => ({
      modelKey: item.model_key,
      modelName: item.model_name,
      provider: item.provider,
      totalTokens: item.total_tokens ?? 0,
      inputTokens: item.input_tokens ?? 0,
      outputTokens: item.output_tokens ?? 0,
      callCount: item.call_count ?? 0
    }))

    modelSummaries.value = mappedModels

    if (!mappedModels.length) {
      activeModelKey.value = ''
      chartMetrics.value = []
      updateChart()
      chartLoading.value = false
      return
    }

    if (!mappedModels.some((item) => item.modelKey === activeModelKey.value)) {
      activeModelKey.value = mappedModels[0].modelKey
    }

    await loadTimeseriesForActiveModel(params)
  } catch (error) {
    console.error(error)
    if (currentToken === modelDataToken) {
      ElMessage.error('加载用量数据失败，请稍后重试')
    }
  } finally {
    if (currentToken === modelDataToken) {
      overviewLoading.value = false
      modelLoading.value = false
    }
  }
}

async function loadTimeseriesForActiveModel(params = getDateParams()) {
  const modelKey = activeModelKey.value
  const currentToken = ++chartDataToken
  if (!modelKey) {
    chartMetrics.value = []
    chartLoading.value = false
    updateChart()
    return
  }

  chartLoading.value = true
  try {
    const response = await getModelTimeseries(modelKey, params)
    if (currentToken !== chartDataToken) {
      return
    }
    chartMetrics.value = response.map<UsagePoint>((item) => ({
      date: item.date,
      inputTokens: item.input_tokens ?? 0,
      outputTokens: item.output_tokens ?? 0,
      callCount: item.call_count ?? 0
    }))
    updateChart()
  } catch (error) {
    console.error(error)
    if (currentToken === chartDataToken) {
      ElMessage.error('加载趋势数据失败，请稍后重试')
      chartMetrics.value = []
      updateChart()
    }
  } finally {
    if (currentToken === chartDataToken) {
      chartLoading.value = false
    }
  }
}

function handleModelSelect(row: ModelSummary | undefined) {
  if (!row) return
  if (row.modelKey === activeModelKey.value) return
  activeModelKey.value = row.modelKey
  loadTimeseriesForActiveModel()
}

function rowClassName({ row }: { row: ModelSummary }) {
  return row.modelKey === activeModelKey.value ? 'is-active' : ''
}

function formatNumber(value?: number | null) {
  const safeValue = value ?? 0
  return safeValue.toLocaleString('zh-CN')
}

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

function initChart() {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
  }
}

function updateChart() {
  if (!chartInstance) return
  const metrics = chartMetrics.value
  const dates = metrics.map((item) => item.date)
  const inputSeries = metrics.map((item) => item.inputTokens)
  const outputSeries = metrics.map((item) => item.outputTokens)

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['输入 Token', '输出 Token'],
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      top: 60,
      bottom: 20,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '输入 Token',
        type: 'line',
        stack: '总量',
        areaStyle: {},
        emphasis: { focus: 'series' },
        data: inputSeries
      },
      {
        name: '输出 Token',
        type: 'line',
        stack: '总量',
        areaStyle: {},
        emphasis: { focus: 'series' },
        data: outputSeries
      }
    ]
  }

  chartInstance.setOption(option, { notMerge: true })
}

onMounted(() => {
  initChart()
  nextTick(updateChart)
  window.addEventListener('resize', resizeChart)
})

function resizeChart() {
  chartInstance?.resize()
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
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
  flex-direction: column;
  gap: 12px;
}

@media (min-width: 768px) {
  .page-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
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


.page-toolbar {
  display: flex;
  justify-content: flex-end;
}

.page-toolbar :deep(.el-date-editor) {
  width: 280px;
}

.overview-row {
  margin-top: 8px;
}

.overview-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
  min-height: 94px;
}

.overview-card__title {
  font-size: 13px;
  color: var(--text-weak-color);
}

.overview-card__value {
  font-size: 20px;
  font-weight: 600;
  color: var(--header-text-color);
}

.detail-row {
  margin-top: 4px;
  align-items: stretch;
  flex-wrap: wrap;
}

.detail-row :deep(.el-col) {
  display: flex;
  min-width: 0;
}

.model-card,
.chart-card {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.model-col {
  flex: 1 1 auto !important;
  max-width: none !important;
}

.chart-card {
  max-width: 100%;
}

.model-card :deep(.el-card__body),
.chart-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.model-card :deep(.el-table) {
  flex: 1;
}

.model-card :deep(.el-table__body-wrapper) {
  flex: 1;
}

.model-card :deep(.el-table__inner-wrapper) {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.usage-chart {
  width: 100%;
  flex: 1;
  min-height: 340px;
}

@media (min-width: 1200px) {
  .detail-row {
    flex-wrap: nowrap;
  }

  .chart-col {
    flex: 0 0 680px !important;
    max-width: 680px !important;
    width: 680px !important;
  }

  .chart-card {
    width: 680px;
  }
}

.model-card__header,
.chart-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sort-select {
  width: 140px;
}

.model-name {
  display: block;
  font-weight: 600;
}

.provider-name {
  display: block;
  font-size: 12px;
  color: var(--text-weak-color);
}

:deep(.is-active) {
  font-weight: 600;
}
</style>
