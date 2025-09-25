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
      <el-col :xs="24" :lg="10">
        <el-card shadow="hover" class="model-card">
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
      <el-col :xs="24" :lg="14">
        <el-card shadow="hover" class="chart-card">
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
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface UsagePoint {
  date: string
  inputTokens: number
  outputTokens: number
  callCount: number
}

interface ModelUsage {
  modelKey: string
  modelName: string
  provider: string
  metrics: UsagePoint[]
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

const mockModelUsage: ModelUsage[] = [
  {
    modelKey: 'gpt-4o-mini',
    modelName: 'gpt-4o-mini',
    provider: 'OpenAI',
    metrics: generateMockUsage(14, 1200, 800, 30)
  },
  {
    modelKey: 'claude-3-sonnet',
    modelName: 'Claude 3 Sonnet',
    provider: 'Anthropic',
    metrics: generateMockUsage(14, 900, 600, 20)
  },
  {
    modelKey: 'gemini-1.5-pro',
    modelName: 'Gemini 1.5 Pro',
    provider: 'Google',
    metrics: generateMockUsage(14, 700, 500, 18)
  },
  {
    modelKey: 'azure-gpt-35',
    modelName: 'Azure GPT-3.5',
    provider: 'Azure OpenAI',
    metrics: generateMockUsage(14, 650, 420, 15)
  }
]

function generateMockUsage(days: number, baseInput: number, baseOutput: number, baseCalls: number): UsagePoint[] {
  const result: UsagePoint[] = []
  for (let i = days - 1; i >= 0; i -= 1) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    const factor = 0.8 + Math.random() * 0.4
    result.push({
      date: date.toISOString().slice(0, 10),
      inputTokens: Math.round(baseInput * factor),
      outputTokens: Math.round(baseOutput * factor * (0.9 + Math.random() * 0.2)),
      callCount: Math.round(baseCalls * factor * (0.9 + Math.random() * 0.2))
    })
  }
  return result
}

function withinRange(date: string, range: [Date, Date]): boolean {
  if (!range[0] || !range[1]) return true
  const [start, end] = range
  const value = new Date(date)
  return value >= start && value <= new Date(end.getTime() + 24 * 60 * 60 * 1000)
}

const enrichedModels = computed(() => {
  return mockModelUsage.map((model) => {
    const filtered = model.metrics.filter((point) => withinRange(point.date, dateRange.value))
    const totals = filtered.reduce(
      (acc, cur) => {
        acc.inputTokens += cur.inputTokens
        acc.outputTokens += cur.outputTokens
        acc.totalTokens += cur.inputTokens + cur.outputTokens
        acc.callCount += cur.callCount
        return acc
      },
      { inputTokens: 0, outputTokens: 0, totalTokens: 0, callCount: 0 }
    )
    return {
      ...model,
      summary: totals,
      filteredMetrics: filtered,
      totalTokens: totals.totalTokens,
      inputTokens: totals.inputTokens,
      outputTokens: totals.outputTokens,
      callCount: totals.callCount
    }
  })
})

const overviewCards = computed(() => {
  const totals = enrichedModels.value.reduce(
    (acc, model) => {
      acc.totalTokens += model.summary.totalTokens
      acc.inputTokens += model.summary.inputTokens
      acc.outputTokens += model.summary.outputTokens
      acc.callCount += model.summary.callCount
      return acc
    },
    { totalTokens: 0, inputTokens: 0, outputTokens: 0, callCount: 0 }
  )
  return [
    { key: 'totalTokens', title: '总 Token 数', value: totals.totalTokens },
    { key: 'inputTokens', title: '输入 Token 数', value: totals.inputTokens },
    { key: 'outputTokens', title: '输出 Token 数', value: totals.outputTokens },
    { key: 'callCount', title: '调用次数', value: totals.callCount }
  ]
})

const sortKey = ref<'totalTokens' | 'callCount' | 'inputTokens' | 'outputTokens'>('totalTokens')

const sortedModels = computed(() => {
  const list = enrichedModels.value
  return [...list].sort((a, b) => b.summary[sortKey.value] - a.summary[sortKey.value])
})

const activeModelKey = ref(sortedModels.value[0]?.modelKey ?? '')

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

const activeModel = computed(() => sortedModels.value.find((item) => item.modelKey === activeModelKey.value))

function handleModelSelect(row: (typeof sortedModels.value)[number] | undefined) {
  if (row) {
    activeModelKey.value = row.modelKey
  }
}

function rowClassName({ row }: { row: (typeof sortedModels.value)[number] }) {
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
  if (!chartInstance || !activeModel.value) return
  const metrics = activeModel.value.filteredMetrics
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

  chartInstance.setOption(option)
}

onMounted(() => {
  initChart()
  nextTick(updateChart)
  window.addEventListener('resize', resizeChart)
})

function resizeChart() {
  chartInstance?.resize()
}

watch([activeModel, dateRange], () => {
  nextTick(updateChart)
})

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

.usage-chart {
  width: 100%;
  height: 340px;
}

:deep(.is-active) {
  font-weight: 600;
}
</style>


