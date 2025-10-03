<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>标签管理</h2>
        <p class="page-desc">维护标签名称与颜色，掌握标签在 Prompt 中的使用频次。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openDialog">新建标签</el-button>
    </section>

    <el-card class="table-card">
      <template #header>
        <div class="table-card__header">
          <span>共 {{ totalTags }} 个标签 · 覆盖 {{ totalTaggedPrompts }} 条 Prompt</span>
        </div>
      </template>
      <el-table
        :data="tagRows"
        v-loading="tableLoading"
        border
        stripe
        empty-text="暂无标签数据"
      >
        <el-table-column label="标签" min-width="200">
          <template #default="{ row }">
            <span class="tag-cell">
              <span class="tag-dot" :style="{ backgroundColor: row.color }" />
              <span>{{ row.name }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="color" label="颜色" width="140">
          <template #default="{ row }">
            <el-tag :style="{ backgroundColor: row.color, borderColor: row.color }" effect="dark" size="small">
              {{ row.color }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="prompt_count" label="引用 Prompt 数" width="140" align="center" />
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="最近更新" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新建标签" width="520px">
      <el-form :model="tagForm" label-width="100px" class="dialog-form">
        <el-form-item label="标签名称">
          <el-input v-model="tagForm.name" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="标签颜色">
          <el-color-picker v-model="tagForm.color" :show-alpha="false" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createPromptTag,
  deletePromptTag,
  listPromptTags,
  type PromptTagStats
} from '../api/promptTag'

const tableLoading = ref(false)
const submitLoading = ref(false)
const promptTags = ref<PromptTagStats[]>([])
const taggedPromptTotal = ref(0)

const tagRows = computed(() => {
  return [...promptTags.value].sort((a, b) => {
    if (b.prompt_count !== a.prompt_count) {
      return b.prompt_count - a.prompt_count
    }
    return a.name.localeCompare(b.name, 'zh-CN')
  })
})

const totalTags = computed(() => tagRows.value.length)
const totalTaggedPrompts = computed(() => taggedPromptTotal.value)

const dateTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit'
})

function formatDateTime(value: string | null | undefined) {
  if (!value) return '--'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : dateTimeFormatter.format(date)
}

const dialogVisible = ref(false)
const tagForm = reactive({
  name: '',
  color: '#409EFF'
})

async function fetchPromptTags() {
  tableLoading.value = true
  try {
    const data = await listPromptTags()
    promptTags.value = data.items
    taggedPromptTotal.value = data.tagged_prompt_total
  } catch (error) {
    console.error(error)
    ElMessage.error('加载标签数据失败，请稍后重试')
  } finally {
    tableLoading.value = false
  }
}

function resetTagForm() {
  tagForm.name = ''
  tagForm.color = '#409EFF'
}

function openDialog() {
  resetTagForm()
  dialogVisible.value = true
}

async function handleCreate() {
  if (!tagForm.name.trim()) {
    ElMessage.warning('请填写标签名称')
    return
  }
  submitLoading.value = true
  try {
    await createPromptTag({
      name: tagForm.name.trim(),
      color: tagForm.color.toUpperCase()
    })
    ElMessage.success('标签创建成功')
    dialogVisible.value = false
    await fetchPromptTags()
  } catch (error: any) {
    console.error(error)
    const message = error?.payload?.detail ?? '创建标签失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row: PromptTagStats) {
  try {
    await ElMessageBox.confirm(`确认删除标签“${row.name}”并解除关联？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }

  try {
    await deletePromptTag(row.id)
    ElMessage.success('标签已删除')
    await fetchPromptTags()
  } catch (error: any) {
    if (error?.status === 409) {
      ElMessage.error('仍有关联 Prompt 使用该标签，请先迁移或删除后再尝试')
      return
    }
    console.error(error)
    const message = error?.payload?.detail ?? '删除标签失败，请稍后重试'
    ElMessage.error(message)
  }
}

onMounted(() => {
  fetchPromptTags()
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

.table-card__header {
  font-size: 13px;
  color: var(--text-weak-color);
}

.tag-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #909399;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
