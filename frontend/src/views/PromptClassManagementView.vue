<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>分类管理</h2>
        <p class="page-desc">集中维护 Prompt 分类结构，查看各分类下的提示词数量与更新时间。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openDialog">新建分类</el-button>
    </section>

    <el-card class="table-card">
      <template #header>
        <div class="table-card__header">
          <span>共 {{ totalClasses }} 个分类 · 覆盖 {{ totalPrompts }} 条 Prompt</span>
        </div>
      </template>
      <el-table
        :data="classRows"
        v-loading="tableLoading"
        border
        stripe
        empty-text="暂无分类数据"
      >
        <el-table-column prop="name" label="分类名称" min-width="160" />
        <el-table-column prop="description" label="分类描述" min-width="220">
          <template #default="{ row }">
            {{ row.description ?? '暂无描述' }}
          </template>
        </el-table-column>
        <el-table-column prop="prompt_count" label="Prompt 数量" width="120" align="center" />
        <el-table-column prop="created_at" label="创建时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="latest_prompt_updated_at" label="最近更新" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.latest_prompt_updated_at ?? row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新建分类" width="520px">
      <el-form :model="classForm" label-width="100px" class="dialog-form">
        <el-form-item label="分类名称">
          <el-input v-model="classForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="分类描述">
          <el-input
            v-model="classForm.description"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="请输入分类描述（可选）"
          />
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
  createPromptClass,
  deletePromptClass,
  listPromptClasses,
  type PromptClassStats
} from '../api/promptClass'

const tableLoading = ref(false)
const submitLoading = ref(false)
const promptClasses = ref<PromptClassStats[]>([])

const classRows = computed(() => {
  return [...promptClasses.value].sort((a, b) => {
    if (b.prompt_count !== a.prompt_count) {
      return b.prompt_count - a.prompt_count
    }
    return a.name.localeCompare(b.name, 'zh-CN')
  })
})

const totalClasses = computed(() => classRows.value.length)
const totalPrompts = computed(() =>
  classRows.value.reduce((acc, item) => acc + (item.prompt_count ?? 0), 0)
)

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
const classForm = reactive({
  name: '',
  description: ''
})

async function fetchPromptClasses() {
  tableLoading.value = true
  try {
    promptClasses.value = await listPromptClasses()
  } catch (error) {
    console.error(error)
    ElMessage.error('加载分类数据失败，请稍后重试')
  } finally {
    tableLoading.value = false
  }
}

function resetClassForm() {
  classForm.name = ''
  classForm.description = ''
}

function openDialog() {
  resetClassForm()
  dialogVisible.value = true
}

async function handleCreate() {
  if (!classForm.name.trim()) {
    ElMessage.warning('请填写分类名称')
    return
  }
  submitLoading.value = true
  try {
    await createPromptClass({
      name: classForm.name.trim(),
      description: classForm.description.trim() || null
    })
    ElMessage.success('分类创建成功')
    dialogVisible.value = false
    await fetchPromptClasses()
  } catch (error: any) {
    console.error(error)
    const message = error?.payload?.detail ?? '创建分类失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row: PromptClassStats) {
  try {
    await ElMessageBox.confirm(`确认删除分类“${row.name}”及其关联关系？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }

  try {
    await deletePromptClass(row.id)
    ElMessage.success('分类已删除')
    await fetchPromptClasses()
  } catch (error: any) {
    if (error?.status === 409) {
      ElMessage.error('仍有关联 Prompt 使用该分类，请先迁移或删除后再尝试')
      return
    }
    console.error(error)
    const message = error?.payload?.detail ?? '删除分类失败，请稍后重试'
    ElMessage.error(message)
  }
}

onMounted(() => {
  fetchPromptClasses()
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

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
