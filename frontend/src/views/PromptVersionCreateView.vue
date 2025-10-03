<template>
  <div class="version-create-page">
    <el-breadcrumb separator="/" class="version-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptManagement">Prompt 管理</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goPromptDetail">
          {{ promptDetail?.name ?? '未命名 Prompt' }}
        </span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>新增版本</el-breadcrumb-item>
    </el-breadcrumb>

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
    />

    <el-skeleton v-else-if="isLoading" animated :rows="5" />

    <el-empty v-else-if="!promptDetail" description="未找到 Prompt 信息" />

    <el-card v-else>
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
              v-for="version in promptDetail.versions"
              :key="version.id"
              :label="version.version"
              :value="version.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-space>
            <el-button type="primary" :loading="isSubmitting" @click="handleSubmit">
              提交
            </el-button>
            <el-button @click="goPromptDetail">取消</el-button>
          </el-space>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { usePromptDetail } from '../composables/usePromptDetail'
import { updatePrompt, type HttpError } from '../api/prompt'

const router = useRouter()
const route = useRoute()

const currentId = computed(() => {
  const raw = Number(route.params.id)
  return Number.isFinite(raw) && raw > 0 ? raw : null
})

const {
  prompt: promptDetail,
  loading: isLoading,
  error: errorMessage
} = usePromptDetail(currentId)

const form = reactive({
  version: '',
  summary: '',
  content: '',
  reference: undefined as number | undefined
})

const isSubmitting = ref(false)

watch(
  () => promptDetail.value?.current_version?.id,
  (versionId) => {
    if (typeof versionId === 'number') {
      form.reference = versionId
    }
  },
  { immediate: true }
)

function extractErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'payload' in error) {
    const httpError = error as HttpError
    const detail = (httpError.payload as Record<string, unknown> | null)?.detail
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
    if (httpError.status === 404) {
      return '目标 Prompt 不存在'
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return '提交新版本失败'
}

async function handleSubmit() {
  if (!currentId.value) {
    ElMessage.error('无法识别当前 Prompt 编号')
    return
  }
  if (!form.version.trim() || !form.content.trim()) {
    ElMessage.warning('请填写版本号与内容')
    return
  }

  isSubmitting.value = true
  try {
    await updatePrompt(currentId.value, {
      version: form.version.trim(),
      content: form.content
    })
    ElMessage.success('新增版本成功')
    router.push({ name: 'prompt-detail', params: { id: currentId.value } })
  } catch (error) {
    ElMessage.error(extractErrorMessage(error))
  } finally {
    isSubmitting.value = false
  }
}

function goPromptDetail() {
  if (!currentId.value) {
    router.push({ name: 'prompt-management' })
    return
  }
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
