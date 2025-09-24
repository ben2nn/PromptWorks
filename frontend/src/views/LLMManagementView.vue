<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>LLMs 管理</h2>
        <p class="page-desc">集中配置可用的大模型服务，统一管理调用凭证与配额信息。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openDialog">新增模型</el-button>
    </section>
    <el-empty description="后续迭代将支持模型管理配置" />

    <el-dialog v-model="dialogVisible" title="新增模型提供方" width="620px">
      <el-form :model="llmForm" label-width="120px" class="dialog-form">
        <el-form-item label="提供方名称">
          <el-input v-model="llmForm.provider_name" placeholder="如 OpenAI / Anthropic" />
        </el-form-item>
        <el-form-item label="模型标识">
          <el-input v-model="llmForm.model_name" placeholder="如 gpt-4o-mini" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="llmForm.base_url" placeholder="可选，覆盖默认接口地址" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="llmForm.api_key" placeholder="请输入调用凭证" type="password" show-password />
        </el-form-item>
        <el-form-item label="参数配置">
          <el-input
            v-model="llmForm.parameters"
            type="textarea"
            :autosize="{ minRows: 4, maxRows: 8 }"
            placeholder="请输入 JSON 格式的参数，如 { &quot;temperature&quot;: 0.7 }"
          />
        </el-form-item>
        <el-form-item label="Logo 链接">
          <el-input v-model="llmForm.logo_url" placeholder="可选，模型展示图片地址" />
        </el-form-item>
        <el-form-item label="Logo Emoji">
          <el-input v-model="llmForm.logo_emoji" placeholder="可选，用于展示的 Emoji" />
        </el-form-item>
        <el-form-item label="自定义提供方">
          <el-switch v-model="llmForm.is_custom" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const dialogVisible = ref(false)
const llmForm = reactive({
  provider_name: '',
  model_name: '',
  base_url: '',
  api_key: '',
  parameters: '{\n  "temperature": 0.7\n}',
  logo_url: '',
  logo_emoji: '',
  is_custom: false
})

function resetForm() {
  llmForm.provider_name = ''
  llmForm.model_name = ''
  llmForm.base_url = ''
  llmForm.api_key = ''
  llmForm.parameters = '{\n  "temperature": 0.7\n}'
  llmForm.logo_url = ''
  llmForm.logo_emoji = ''
  llmForm.is_custom = false
}

function openDialog() {
  resetForm()
  dialogVisible.value = true
}

function handleCreate() {
  if (!llmForm.provider_name.trim() || !llmForm.model_name.trim() || !llmForm.api_key.trim()) {
    ElMessage.warning('请填写提供方名称、模型标识与 API Key')
    return
  }
  try {
    const parsed = JSON.parse(llmForm.parameters || '{}')
    if (typeof parsed !== 'object' || parsed === null) {
      throw new Error('参数需为 JSON 对象')
    }
  } catch (error) {
    ElMessage.warning('参数配置需符合 JSON 格式')
    return
  }
  ElMessage.info('后端接口建设中，提交数据暂未保存')
  dialogVisible.value = false
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

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>

