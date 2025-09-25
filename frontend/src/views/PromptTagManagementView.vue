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
      <el-table :data="tagRows" border stripe empty-text="暂无标签数据">
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
        <el-table-column prop="promptCount" label="引用 Prompt 数" width="140" align="center" />
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
import type { Prompt, PromptTag } from '../types/prompt'

type TagRow = PromptTag & {
  promptCount: number
}

const prompts: Prompt[] = mockPrompts

const tagRows = computed<TagRow[]>(() => {
  const map = new Map<number, TagRow>()
  prompts.forEach((prompt) => {
    prompt.tags.forEach((tag) => {
      if (!map.has(tag.id)) {
        map.set(tag.id, {
          ...tag,
          promptCount: 0
        })
      }
      const record = map.get(tag.id)!
      record.promptCount += 1
      if (new Date(tag.created_at).getTime() < new Date(record.created_at).getTime()) {
        record.created_at = tag.created_at
      }
      const latestUpdated = [tag.updated_at, prompt.updated_at].reduce((acc, cur) => {
        return new Date(cur).getTime() > new Date(acc).getTime() ? cur : acc
      }, record.updated_at)
      record.updated_at = latestUpdated
    })
  })

  return Array.from(map.values()).sort((a, b) => {
    if (b.promptCount !== a.promptCount) {
      return b.promptCount - a.promptCount
    }
    return a.name.localeCompare(b.name, 'zh-CN')
  })
})

const totalTags = computed(() => tagRows.value.length)
const totalTaggedPrompts = computed(() => prompts.filter((item) => item.tags.length > 0).length)

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

function resetTagForm() {
  tagForm.name = ''
  tagForm.color = '#409EFF'
}

function openDialog() {
  resetTagForm()
  dialogVisible.value = true
}

function handleCreate() {
  if (!tagForm.name.trim()) {
    ElMessage.warning('请填写标签名称')
    return
  }
  ElMessage.info('后端接口建设中，提交数据暂未保存')
  dialogVisible.value = false
}

function handleDelete(row: TagRow) {
  ElMessageBox.confirm(`确认删除标签“${row.name}”并解除关联？`, '删除确认', {
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
