<template>
  <div class="unit-result-page">
    <el-breadcrumb separator="/" class="page-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goTaskResult">{{ t('promptTestResult.breadcrumb.task') }}</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>{{ unit?.name ?? t('promptTestResult.empty.noSelection') }}</el-breadcrumb-item>
    </el-breadcrumb>

    <section class="page-header">
      <div>
        <h2>{{ unit?.name ?? t('promptTestResult.empty.noSelection') }}</h2>
        <p class="page-desc">
          <span>{{ t('promptTestResult.fields.version') }}: {{ unit?.promptVersion ?? '-' }}</span>
          <span>{{ t('promptTestResult.fields.model') }}: {{ unit?.modelName ?? '-' }}</span>
          <span>{{ t('promptTestResult.fields.parameters') }}: {{ unit?.parameterSet ?? '-' }}</span>
        </p>
      </div>
      <el-tag type="success" size="small">Mock</el-tag>
    </section>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('promptTestResult.unitDetail.outputsTitle', { count: unit?.outputs.length ?? 0 }) }}</span>
        </div>
      </template>

      <div class="unit-parameters">
        <h4 class="unit-parameters__title">
          {{ t('promptTestResult.unitDetail.parametersTitle', { name: unit?.parameterSet ?? '-' }) }}
        </h4>
        <el-descriptions
          v-if="parameterEntries.length"
          :column="1"
          size="small"
          border
          class="unit-parameters__table"
        >
          <el-descriptions-item
            v-for="[paramKey, paramValue] in parameterEntries"
            :key="paramKey"
            :label="paramKey"
          >
            {{ paramValue }}
          </el-descriptions-item>
        </el-descriptions>
        <div v-else class="unit-parameters__empty">
          {{ t('promptTestResult.unitDetail.parametersEmpty') }}
        </div>
      </div>

      <el-empty v-if="!unit || !unit.outputs.length" :description="t('promptTestResult.empty.noOutputs')" />
      <el-timeline v-else>
        <el-timeline-item
          v-for="output in unit.outputs"
          :key="output.runIndex"
          :timestamp="`#${output.runIndex}`"
          placement="top"
        >
          <el-card shadow="hover">
            <p class="output-content">{{ output.content }}</p>
            <p class="output-meta">{{ output.meta ?? '' }}</p>
            <div v-if="output.variables && Object.keys(output.variables).length" class="output-variables">
              <div
                v-for="(value, key) in output.variables"
                :key="key"
                class="variable-item"
              >
                <span class="variable-key">{{ key }}:</span>
                <span class="variable-value">{{ value }}</span>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { mockUnits as mockUnitsData, type MockUnit } from './mockPromptTestData'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const taskId = route.params.taskId ?? 'demo'
const unitId = Number(route.params.unitId)

const unit = computed<MockUnit | null>(() => mockUnitsData.find((item) => item.id === unitId) ?? null)
const parameterEntries = computed<Array<[string, string | number]>>(() => {
  const current = unit.value
  if (!current) return []
  return Object.entries(current.parameters) as Array<[string, string | number]>
})

function goTaskResult() {
  router.push({ name: 'prompt-test-task-result', params: { taskId }, query: { tab: 'units' } })
}
</script>

<style scoped>
.unit-result-page {
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

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.page-desc {
  margin: 4px 0 0;
  color: var(--text-weak-color);
  font-size: 13px;
  display: flex;
  gap: 12px;
}

.card-header {
  font-weight: 600;
}

.unit-parameters {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.unit-parameters__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.unit-parameters__table {
  width: 100%;
}

.unit-parameters__empty {
  font-size: 12px;
  color: var(--text-weak-color);
}

.output-content {
  margin: 0 0 8px;
  white-space: pre-wrap;
}

.output-meta {
  margin: 0 0 8px;
  color: var(--text-weak-color);
  font-size: 12px;
}

.output-variables {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}

.variable-item {
  display: flex;
  gap: 6px;
}

.variable-key {
  font-weight: 600;
  color: var(--el-color-primary);
}
</style>
