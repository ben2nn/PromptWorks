<template>
  <div class="prompt-test-result-page">
    <el-breadcrumb separator="/" class="page-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goBack">{{ t('menu.testJob') }}</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>{{ displayTaskName }}</el-breadcrumb-item>
    </el-breadcrumb>

    <section class="page-header">
      <div class="page-header__text">
        <h2>{{ displayTaskName }}</h2>
        <p class="page-desc">
          {{ t('promptTestResult.mockDescription', { createdAt: mockSummary.createdAt, unitCount: mockUnits.length }) }}
        </p>
      </div>
      <div class="page-header__meta">
        <el-tag size="small" type="success">Mock</el-tag>
      </div>
    </section>

    <el-card>
      <template #header>
        <div class="card-header">
          <el-radio-group v-model="activeTab" size="small">
            <el-radio-button label="units">{{ t('promptTestResult.tabs.units') }}</el-radio-button>
            <el-radio-button label="results">{{ t('promptTestResult.tabs.results') }}</el-radio-button>
            <el-radio-button label="analysis">{{ t('promptTestResult.tabs.analysis') }}</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <div v-if="activeTab === 'results'" class="result-panel">
        <div class="result-toolbar">
          <div class="columns-control">
            <el-button
              size="small"
              type="primary"
              :disabled="columnConfigs.length >= 5"
              @click="addColumn"
            >
              {{ t('promptTestResult.actions.addColumn') }}
            </el-button>
            <el-button
              size="small"
              type="default"
              :disabled="columnConfigs.length <= 1"
              @click="removeLastColumn"
            >
              {{ t('promptTestResult.actions.removeColumn') }}
            </el-button>
            <span class="column-count">{{ t('promptTestResult.actions.columnCount', { count: columnConfigs.length }) }}</span>
          </div>
        </div>

        <div class="result-grid">
          <div class="result-grid-scroll" :style="{ width: gridWidth, minWidth: '100%' }">
            <div
              class="grid-header"
              :style="{ gridTemplateColumns: gridTemplateColumnsValue, width: gridWidth, minWidth: '100%' }"
            >
              <div
                v-for="(config, idx) in columnConfigs"
                :key="config.columnId"
                class="grid-cell"
              >
                <div class="header-select">
                  <el-select v-model="config.unitId" size="small" class="column-selector">
                    <el-option
                      v-for="unit in mockUnits"
                      :key="unit.id"
                      :label="formatUnitOption(unit)"
                      :value="unit.id"
                    />
                  </el-select>
                  <el-button
                    v-if="columnConfigs.length > 1"
                    size="small"
                    type="text"
                    @click="removeColumn(config.columnId)"
                  >
                    {{ t('promptTestResult.actions.removeSingleColumn') }}
                  </el-button>
                </div>
                <div class="header-details">
                  <div>
                    <strong>{{ selectedUnits[idx]?.name ?? t('promptTestResult.empty.noSelection') }}</strong>
                  </div>
                  <div class="header-meta">
                    <span>{{ t('promptTestResult.fields.version') }}: {{ selectedUnits[idx]?.promptVersion ?? '-' }}</span>
                    <span>{{ t('promptTestResult.fields.model') }}: {{ selectedUnits[idx]?.modelName ?? '-' }}</span>
                    <span>{{ t('promptTestResult.fields.parameters') }}: {{ selectedUnits[idx]?.parameterSet ?? '-' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="alignedRows.length" class="grid-body">
              <div
                v-for="row in alignedRows"
                :key="row.index"
                class="grid-row"
                :style="{ gridTemplateColumns: gridTemplateColumnsValue, width: gridWidth, minWidth: '100%' }"
              >
                <div
                  v-for="(cell, cellIndex) in row.cells"
                  :key="cellIndex"
                  class="grid-cell"
                >
                  <div class="output-badge">#{{ row.index }}</div>
                  <div class="output-content">{{ cell?.content ?? placeholderText }}</div>
                  <div class="output-meta">{{ cell?.meta ?? '' }}</div>
                  <div v-if="cell?.variables && Object.keys(cell.variables).length" class="output-variables">
                    <div
                      v-for="(value, key) in cell.variables"
                      :key="key"
                      class="variable-item"
                    >
                      <span class="variable-key">{{ key }}:</span>
                      <span class="variable-value">{{ value }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <el-empty v-else :description="t('promptTestResult.empty.noOutputs')" />
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'units'" class="units-panel">
        <div class="units-toolbar">
          <div class="units-filters">
            <el-input
              v-model="filterForm.keyword"
              class="units-filter__keyword"
              size="small"
              clearable
              :placeholder="t('promptTestResult.filters.keywordPlaceholder')"
            />
            <el-select
              v-model="filterForm.promptVersion"
              size="small"
              class="units-filter__select"
              :placeholder="t('promptTestResult.filters.promptVersion')"
              clearable
            >
              <el-option
                v-for="version in filterOptions.promptVersions"
                :key="version"
                :label="version"
                :value="version"
              />
            </el-select>
            <el-select
              v-model="filterForm.modelName"
              size="small"
              class="units-filter__select"
              :placeholder="t('promptTestResult.filters.modelName')"
              clearable
            >
              <el-option
                v-for="model in filterOptions.modelNames"
                :key="model"
                :label="model"
                :value="model"
              />
            </el-select>
            <el-select
              v-model="filterForm.parameterSet"
              size="small"
              class="units-filter__select"
              :placeholder="t('promptTestResult.filters.parameterSet')"
              clearable
            >
              <el-option
                v-for="parameter in filterOptions.parameterSets"
                :key="parameter"
                :label="parameter"
                :value="parameter"
              />
            </el-select>
          </div>
          <el-button type="primary" size="small" @click="exportUnitsCsv">
            {{ t('promptTestResult.actions.exportCsv') }}
          </el-button>
        </div>
        <div v-if="filteredUnits.length" class="unit-card-grid">
          <el-card
            v-for="unit in filteredUnits"
            :key="unit.id"
            class="unit-card"
            shadow="hover"
            @click="openUnitDetail(unit.id)"
          >
            <div class="unit-card__header">
              <h4>{{ unit.name }}</h4>
              <el-tag size="small">{{ unit.outputs.length }} {{ t('promptTestResult.labels.outputs') }}</el-tag>
            </div>
            <div class="unit-card__meta">
              <div>{{ t('promptTestResult.fields.version') }}: {{ unit.promptVersion }}</div>
              <div>{{ t('promptTestResult.fields.model') }}: {{ unit.modelName }}</div>
              <div>{{ t('promptTestResult.fields.parameters') }}: {{ unit.parameterSet }}</div>
            </div>
            <div class="unit-card__preview">
              <p v-if="unit.outputs[0]">
                <strong>#1</strong> {{ unit.outputs[0].content.slice(0, 60) }}<span v-if="unit.outputs[0].content.length > 60">...</span>
              </p>
              <p v-else>{{ t('promptTestResult.empty.noOutputs') }}</p>
            </div>
          </el-card>
        </div>
        <el-empty v-else :description="t('promptTestResult.empty.noUnitsFiltered')" />
      </div>
      <div v-else class="analysis-panel">
        <el-empty :description="t('promptTestResult.empty.analysis')" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { mockSummary as mockSummaryData, mockUnits as mockUnitsData, type MockUnit } from './mockPromptTestData'

type MockOutput = MockUnit['outputs'][number]

interface UnitColumnConfig {
  columnId: number
  unitId: number | null
}

interface AlignedRow {
  index: number
  cells: Array<MockOutput | null>
}

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const mockUnits = ref<MockUnit[]>([...mockUnitsData])
const mockSummary = mockSummaryData
const taskId = (route.params.taskId as string | undefined) ?? mockSummary.taskId

const displayTaskName = computed(() =>
  route.params.taskId ? `${mockSummary.taskName} #${route.params.taskId}` : mockSummary.taskName
)

const tabList = ['units', 'results', 'analysis'] as const
type TabKey = (typeof tabList)[number]
const DEFAULT_TAB: TabKey = 'results'

function isTabKey(value: unknown): value is TabKey {
  return typeof value === 'string' && tabList.includes(value as TabKey)
}

function resolveTabFromQuery(value: unknown): TabKey | null {
  if (Array.isArray(value)) {
    const candidate = value.find((item) => isTabKey(item))
    return candidate ?? null
  }
  return isTabKey(value) ? value : null
}

const queryTab = resolveTabFromQuery(route.query.tab)
const activeTab = ref<TabKey>(queryTab ?? DEFAULT_TAB)
const columnConfigs = ref<UnitColumnConfig[]>([
  { columnId: 1, unitId: mockUnits.value[0]?.id ?? null },
  { columnId: 2, unitId: mockUnits.value[1]?.id ?? mockUnits.value[0]?.id ?? null }
])
let columnUid = columnConfigs.value.length

const placeholderText = computed(() => t('promptTestResult.empty.placeholder'))

const filterForm = reactive({
  keyword: '',
  promptVersion: '' as string | undefined,
  modelName: '' as string | undefined,
  parameterSet: '' as string | undefined
})

const filterOptions = computed(() => {
  const promptVersions = Array.from(new Set(mockUnits.value.map((unit) => unit.promptVersion))).filter(Boolean)
  const modelNames = Array.from(new Set(mockUnits.value.map((unit) => unit.modelName))).filter(Boolean)
  const parameterSets = Array.from(new Set(mockUnits.value.map((unit) => unit.parameterSet))).filter(Boolean)
  return {
    promptVersions,
    modelNames,
    parameterSets
  }
})

const filteredUnits = computed(() =>
  mockUnits.value.filter((unit) => {
    const keyword = filterForm.keyword.trim().toLowerCase()
    const keywordMatched =
      !keyword ||
      unit.name.toLowerCase().includes(keyword) ||
      unit.modelName.toLowerCase().includes(keyword) ||
      unit.promptVersion.toLowerCase().includes(keyword)
    const versionMatched = !filterForm.promptVersion || unit.promptVersion === filterForm.promptVersion
    const modelMatched = !filterForm.modelName || unit.modelName === filterForm.modelName
    const parameterMatched = !filterForm.parameterSet || unit.parameterSet === filterForm.parameterSet
    return keywordMatched && versionMatched && modelMatched && parameterMatched
  })
)

const selectedUnits = computed(() =>
  columnConfigs.value.map((config) =>
    mockUnits.value.find((unit) => unit.id === config.unitId) ?? null
  )
)

const columnCount = computed(() => Math.max(columnConfigs.value.length, 1))
const gridTemplateColumnsValue = computed(
  () => `repeat(${columnCount.value}, minmax(240px, 1fr))`
)
const gridWidth = computed(() => {
  const minWidth = 260
  return columnCount.value > 1 ? `${columnCount.value * minWidth}px` : '100%'
})

const alignedRows = computed<AlignedRow[]>(() => {
  const maxLength = Math.max(
    ...selectedUnits.value.map((unit) => unit?.outputs.length ?? 0),
    0
  )
  return Array.from({ length: maxLength }, (_, idx) => ({
    index: idx + 1,
    cells: selectedUnits.value.map((unit) => unit?.outputs[idx] ?? null)
  }))
})

function formatUnitOption(unit: MockUnit) {
  return `${unit.name} | ${unit.promptVersion} | ${unit.modelName} | ${unit.parameterSet}`
}

function addColumn() {
  if (columnConfigs.value.length >= 5) return
  columnUid += 1
  const availableUnit = mockUnits.value.find(
    (unit) => !columnConfigs.value.some((config) => config.unitId === unit.id)
  )
  const fallbackUnitId = availableUnit?.id ?? mockUnits.value[0]?.id ?? null
  columnConfigs.value = [
    ...columnConfigs.value,
    {
      columnId: columnUid,
      unitId: fallbackUnitId
    }
  ]
}

function removeColumn(columnId: number) {
  if (columnConfigs.value.length <= 1) return
  columnConfigs.value = columnConfigs.value.filter((config) => config.columnId !== columnId)
}

function removeLastColumn() {
  if (columnConfigs.value.length <= 1) return
  const lastId = columnConfigs.value[columnConfigs.value.length - 1].columnId
  removeColumn(lastId)
}

watch(
  columnConfigs,
  (configs) => {
    if (!configs.length && mockUnits.value.length) {
      columnUid = 1
      columnConfigs.value = [{ columnId: columnUid, unitId: mockUnits.value[0].id }]
      return
    }
    configs.forEach((config) => {
      if (config.unitId === null && mockUnits.value.length) {
        config.unitId = mockUnits.value[0].id
      }
    })
  },
  { deep: true }
)

watch(
  () => route.query.tab,
  (tab) => {
    const nextTab = resolveTabFromQuery(tab) ?? DEFAULT_TAB
    if (activeTab.value !== nextTab) {
      activeTab.value = nextTab
    }
  }
)

watch(
  activeTab,
  (tab) => {
    const currentTab = resolveTabFromQuery(route.query.tab)
    if (currentTab === tab) return
    router.replace({ query: { ...route.query, tab } })
  }
)

watch(
  mockUnits,
  (units) => {
    const unitIds = new Set(units.map((unit) => unit.id))
    columnConfigs.value = columnConfigs.value.map((config) => {
      if (config.unitId !== null && unitIds.has(config.unitId)) {
        return config
      }
      return { ...config, unitId: units[0]?.id ?? null }
    })
  },
  { deep: true }
)

function goBack() {
  router.push({ name: 'test-job-management' })
}

function exportUnitsCsv() {
  const headers = [
    'unit_id',
    'unit_name',
    'prompt_version',
    'model_name',
    'parameter_set',
    'run_index',
    'content',
    'meta',
    'variables'
  ]

  const rows = mockUnits.value.flatMap((unit) =>
    unit.outputs.map((output) => {
      const variables = output.variables ? JSON.stringify(output.variables) : ''
      const safeContent = output.content.replace(/"/g, '""').replace(/\r?\n/g, ' ')
      return [
        unit.id,
        unit.name,
        unit.promptVersion,
        unit.modelName,
        unit.parameterSet,
        output.runIndex,
        `"${safeContent}"`,
        output.meta ?? '',
        variables
      ]
    })
  )

  const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `prompt-test-units-${mockSummary.taskId}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

function openUnitDetail(unitId: number) {
  router.push({ name: 'prompt-test-unit-result', params: { taskId, unitId } })
}
</script>

<style scoped>
.prompt-test-result-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-breadcrumb {
  margin: 0;
}

.breadcrumb-link {
  cursor: pointer;
  color: var(--el-color-primary);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
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
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

.result-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-toolbar {
  display: flex;
  justify-content: flex-end;
}

.columns-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.column-count {
  font-size: 12px;
  color: var(--text-weak-color);
}

.result-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.result-grid-scroll {
  display: inline-block;
  min-width: 100%;
}

.grid-header {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.grid-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.grid-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.grid-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border: 1px solid var(--el-color-info-light-8);
  border-radius: 6px;
  background-color: var(--el-color-info-light-9);
}

.header-select {
  display: flex;
  align-items: center;
  gap: 8px;
}

.column-selector {
  flex: 1;
}

.header-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
}

.header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: var(--text-weak-color);
}

.output-badge {
  font-size: 12px;
  color: var(--el-color-primary);
  font-weight: 600;
}

.output-content {
  font-size: 14px;
  color: var(--el-text-color-primary);
  white-space: pre-wrap;
}

.output-meta {
  font-size: 12px;
  color: var(--text-weak-color);
}

.output-variables {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.variable-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.variable-key {
  font-weight: 600;
  color: var(--el-color-primary);
}

.variable-value {
  color: var(--el-text-color-regular);
}

.analysis-panel {
  padding: 40px 0;
}

.units-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.units-toolbar {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.units-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.units-filter__keyword {
  width: 200px;
}

.units-filter__select {
  width: 160px;
}

.unit-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.unit-card {
  cursor: pointer;
}

.unit-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.unit-card__meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-weak-color);
}

.unit-card__preview {
  margin-top: 12px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

@media (max-width: 768px) {
  .grid-header,
  .grid-row {
    grid-template-columns: 1fr;
  }
}
</style>
