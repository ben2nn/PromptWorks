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
      <el-table :data="classRows" border stripe empty-text="暂无分类数据">
        <el-table-column prop="name" label="分类名称" min-width="160" />
        <el-table-column prop="description" label="分类描述" min-width="220">
          <template #default="{ row }">
            {{ row.description ?? '暂无描述' }}
          </template>
        </el-table-column>
        <el-table-column prop="promptCount" label="Prompt 数量" width="120" align="center" />
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
        <el-button type="primary" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mockPrompts } from '../mocks/prompts'
import type { Prompt } from '../types/prompt'

type ClassRow = {
  id: number
  name: string
  description: string | null
  promptCount: number
  created_at: string
  updated_at: string
}

const prompts: Prompt[] = mockPrompts

const classRows = computed<ClassRow[]>(() => {
  const map = new Map<number, ClassRow>()
  prompts.forEach((prompt) => {
    const cls = prompt.prompt_class
    if (!map.has(cls.id)) {
      map.set(cls.id, {
        id: cls.id,
        name: cls.name,
        description: cls.description ?? null,
        promptCount: 0,
        created_at: cls.created_at,
        updated_at: cls.updated_at
      })
    }
    const record = map.get(cls.id)!
    record.promptCount += 1
    if (new Date(cls.created_at).getTime() < new Date(record.created_at).getTime()) {
      record.created_at = cls.created_at
    }
    const latestUpdated = [cls.updated_at, prompt.updated_at].reduce((acc, cur) => {
      return new Date(cur).getTime() > new Date(acc).getTime() ? cur : acc
    }, record.updated_at)
    record.updated_at = latestUpdated
  })

  return Array.from(map.values()).sort((a, b) => {
    if (b.promptCount !== a.promptCount) {
      return b.promptCount - a.promptCount
    }
    return a.name.localeCompare(b.name, 'zh-CN')
  })
})

const totalClasses = computed(() => classRows.value.length)
const totalPrompts = computed(() => prompts.length)

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

function resetClassForm() {
  classForm.name = ''
  classForm.description = ''
}

function openDialog() {
  resetClassForm()
  dialogVisible.value = true
}

function handleCreate() {
  if (!classForm.name.trim()) {
    ElMessage.warning('请填写分类名称')
    return
  }
  ElMessage.info('后端接口建设中，提交数据暂未保存')
  dialogVisible.value = false
}

function handleDelete(row: ClassRow) {
  ElMessageBox.confirm(`确认删除分类“${row.name}”及其关联关系？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确认删除',
    cancelButtonText: '取消'
  })
    .then(() => {
      ElMessage.info('后端接口建设中，暂未执行删除操作')
    })
    .catch(() => {
      /* 用户取消 */
    })
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
