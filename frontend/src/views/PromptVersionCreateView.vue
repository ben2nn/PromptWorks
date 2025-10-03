<template>
  <div class="version-create-page">
    <el-breadcrumb separator="/" class="version-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptManagement">Prompt 管理</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptDetail">{{ prompt?.name ?? '未命名 Prompt' }}</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>新增版本</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card>
      <template #header>
        <div class="card-header">
          <h3>新增版本基础表单</h3>
          <span class="card-subtitle">提交后可接入后端接口，现阶段用于演示输入结构</span>
        </div>
      </template>
      <el-form label-width="90px" class="version-form">
        <el-form-item label="版本号">
          <el-input v-model="form.version" placeholder="例如 v1.5.0" />
        </el-form-item>
        <el-form-item label="版本摘要">
          <el-input v-model="form.summary" placeholder="简要说明本次更新要点" />
        </el-form-item>
        <el-form-item label="内容正文">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="12"
            placeholder="在这里粘贴完整 Prompt 内容"
          />
        </el-form-item>
        <el-form-item label="引用版本">
          <el-select v-model="form.reference" clearable placeholder="可选择参考版本">
            <el-option
              v-for="version in prompt?.versions ?? []"
              :key="version.id"
              :label="version.version"
              :value="version.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-space>
            <el-button type="primary" @click="handleSubmit">提交（演示）</el-button>
            <el-button @click="goPromptDetail">取消</el-button>
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
  version: '',
  summary: '',
  content: '',
  reference: undefined as number | undefined
})

function handleSubmit() {
  // 基础示例：真实项目可通过 API 提交
  ElMessage.success('已模拟提交，新版本创建逻辑待接入 API')
}

function goPromptDetail() {
  router.push({ name: 'prompt-detail', params: { id: currentId.value } })
}

function goPromptManagement() {
  router.push({ name: 'prompt-management' })
}
</script>

<style scoped>
.version-create-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.version-breadcrumb {
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

.version-form {
  max-width: 720px;
}
</style>
