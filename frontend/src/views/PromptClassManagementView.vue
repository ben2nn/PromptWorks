<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>{{ t('promptClassManagement.headerTitle') }}</h2>
        <p class="page-desc">{{ t('promptClassManagement.headerDescription') }}</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openDialog">
        {{ t('promptClassManagement.newClass') }}
      </el-button>
    </section>

    <el-card class="table-card">
      <template #header>
        <div class="table-card__header">
          <span>{{ t('promptClassManagement.summary', { totalClasses, totalPrompts }) }}</span>
        </div>
      </template>
      <el-table
        :data="classRows"
        v-loading="tableLoading"
        border
        stripe
        :empty-text="t('promptClassManagement.empty')"
      >
        <el-table-column prop="name" :label="t('promptClassManagement.columns.name')" min-width="160" />
        <el-table-column prop="description" :label="t('promptClassManagement.columns.description')" min-width="220">
          <template #default="{ row }">
            {{ row.description ?? t('common.descriptionNone') }}
          </template>
        </el-table-column>
        <el-table-column
          prop="prompt_count"
          :label="t('promptClassManagement.columns.promptCount')"
          width="120"
          align="center"
        />
        <el-table-column prop="created_at" :label="t('promptClassManagement.columns.createdAt')" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="latest_prompt_updated_at"
          :label="t('promptClassManagement.columns.latestUpdated')"
          min-width="160"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.latest_prompt_updated_at ?? row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('promptClassManagement.columns.actions')" width="120" align="center">
          <template #default="{ row }">
            <el-button type="danger" link @click="handleDelete(row)">
              {{ t('promptClassManagement.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="t('promptClassManagement.dialogTitle')" width="520px">
      <el-form :model="classForm" label-width="100px" class="dialog-form">
        <el-form-item :label="t('promptClassManagement.form.name')">
          <el-input v-model="classForm.name" :placeholder="t('promptClassManagement.form.namePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('promptClassManagement.form.description')">
          <el-input
            v-model="classForm.description"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            :placeholder="t('promptClassManagement.form.descriptionPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('promptClassManagement.footer.cancel') }}</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleCreate">
          {{ t('promptClassManagement.footer.submit') }}
        </el-button>
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
import { useI18n } from 'vue-i18n'

const tableLoading = ref(false)
const submitLoading = ref(false)
const promptClasses = ref<PromptClassStats[]>([])
const { t, locale } = useI18n()

const classRows = computed(() => {
  return [...promptClasses.value].sort((a, b) => {
    if (b.prompt_count !== a.prompt_count) {
      return b.prompt_count - a.prompt_count
    }
    return a.name.localeCompare(b.name, locale.value)
  })
})

const totalClasses = computed(() => classRows.value.length)
const totalPrompts = computed(() =>
  classRows.value.reduce((acc, item) => acc + (item.prompt_count ?? 0), 0)
)

const dateTimeFormatter = computed(
  () =>
    new Intl.DateTimeFormat(locale.value === 'zh-CN' ? 'zh-CN' : 'en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
)

function formatDateTime(value: string | null | undefined) {
  if (!value) return '--'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : dateTimeFormatter.value.format(date)
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
    ElMessage.error(t('promptClassManagement.messages.loadFailed'))
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
    ElMessage.warning(t('promptClassManagement.messages.nameRequired'))
    return
  }
  submitLoading.value = true
  try {
    await createPromptClass({
      name: classForm.name.trim(),
      description: classForm.description.trim() || null
    })
    ElMessage.success(t('promptClassManagement.messages.createSuccess'))
    dialogVisible.value = false
    await fetchPromptClasses()
  } catch (error: any) {
    console.error(error)
    const message = error?.payload?.detail ?? t('promptClassManagement.messages.createFailed')
    ElMessage.error(message)
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row: PromptClassStats) {
  try {
    await ElMessageBox.confirm(
      t('promptClassManagement.messages.deleteConfirmMessage', { name: row.name }),
      t('promptClassManagement.messages.deleteConfirmTitle'),
      {
      type: 'warning',
        confirmButtonText: t('promptClassManagement.messages.confirmDelete'),
        cancelButtonText: t('common.cancel')
      }
    )
  } catch {
    return
  }

  try {
    await deletePromptClass(row.id)
    ElMessage.success(t('promptClassManagement.messages.deleteSuccess'))
    await fetchPromptClasses()
  } catch (error: any) {
    if (error?.status === 409) {
      ElMessage.error(t('promptClassManagement.messages.deleteBlocked'))
      return
    }
    console.error(error)
    const message = error?.payload?.detail ?? t('promptClassManagement.messages.deleteFailed')
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
