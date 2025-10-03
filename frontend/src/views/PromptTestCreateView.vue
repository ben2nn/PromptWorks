<template>
  <div class="test-create-page">
    <el-breadcrumb separator="/" class="test-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptManagement">Prompt 管理</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptDetail">{{ prompt?.name ?? '未命名 Prompt' }}</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>新增测试</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card>
      <template #header>
        <div class="card-header">
          <h3>快速搭建测试任务</h3>
          <span class="card-subtitle">填写测试参数，后续可衔接任务编排与回放功能</span>
        </div>
      </template>
      <el-form label-width="100px" class="test-form">
        <el-form-item label="测试名称">
          <el-input v-model="form.name" placeholder="例如：v1.4.2 回归测试" />
        </el-form-item>
        <el-form-item label="使用模型">
          <el-select v-model="form.model" placeholder="请选择模型">
            <el-option label="gpt-4o" value="gpt-4o" />
            <el-option label="claude-3.5-sonnet" value="claude-3.5-sonnet" />
            <el-option label="glm-4-flash" value="glm-4-flash" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试场景">
          <el-input
            v-model="form.scenario"
            type="textarea"
            :rows="6"
            placeholder="描述本次测试的输入输出、成功判定标准等"
          />
        </el-form-item>
        <el-form-item>
          <el-space>
            <el-button type="primary" @click="handleSubmit">发起测试（演示）</el-button>
            <el-button @click="goPromptDetail">返回</el-button>
          </el-space>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { mockPrompts, getPromptById } from '../mocks/prompts'

const router = useRouter()
const route = useRoute()

const fallbackId = mockPrompts[0]?.id ?? 1
const currentId = computed(() => {
  const value = Number(route.params.id)
  return Number.isNaN(value) ? fallbackId : value
})

const prompt = computed(() => getPromptById(currentId.value) ?? mockPrompts[0] ?? null)

const form = reactive({
  name: '',
  model: '',
  scenario: ''
})

function handleSubmit() {
  ElMessage.success('已模拟发起测试，后续可对接真实测试任务')
}

function goPromptDetail() {
  router.push({ name: 'prompt-detail', params: { id: currentId.value } })
}

function goPromptManagement() {
  router.push({ name: 'prompt-management' })
}
</script>

<style scoped>
.test-create-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.test-breadcrumb {
  font-size: 13px;
}

.breadcrumb-link {
  cursor: pointer;
  color: inherit;
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
  font-size: 13px;
  color: var(--text-weak-color);
}

.test-form {
  max-width: 680px;
}
</style>
