<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>Prompt 管理</h2>
        <p class="page-desc">集中管理提示词资产，快速了解所属分类、作者与当前启用版本。</p>
      </div>
      <el-button type="primary" :icon="Plus" disabled>新建 Prompt</el-button>
    </section>

    <div class="card-grid">
      <div
        v-for="prompt in prompts"
        :key="prompt.id"
        class="card-grid__item"
      >
        <el-card class="prompt-card" shadow="hover" @click="goDetail(prompt.id)">
          <div class="prompt-card__header">
            <div>
              <p class="prompt-class">{{ prompt.prompt_class.name }}</p>
              <h3 class="prompt-title">{{ prompt.name }}</h3>
            </div>
            <el-tag type="success" round size="small">
              当前版本 {{ prompt.current_version?.version ?? '未启用' }}
            </el-tag>
          </div>
          <p class="prompt-desc">{{ prompt.description ?? '暂无描述' }}</p>
          <div class="prompt-meta">
            <div class="meta-item">
              <span class="meta-label">作者</span>
              <span>{{ prompt.author ?? '未设置' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">更新时间</span>
              <span>{{ formatDate(prompt.updated_at) }}</span>
            </div>
          </div>
          <div class="prompt-tags">
            <el-tag
              v-for="tag in prompt.tags"
              :key="tag.id"
              size="small"
              effect="dark"
              :style="{ backgroundColor: tag.color, borderColor: tag.color }"
            >
              {{ tag.name }}
            </el-tag>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { mockPrompts } from '../mocks/prompts'

const router = useRouter()
const prompts = mockPrompts

const dateFormatter = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit'
})

function formatDate(value: string | null | undefined) {
  if (!value) {
    return '--'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return dateFormatter.format(date)
}

function goDetail(id: number) {
  router.push({ name: 'prompt-detail', params: { id: String(id) } })
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

.page-header__text h2 {
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: 600;
}

.page-desc {
  margin: 0;
  color: var(--text-weak-color);
  font-size: 14px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  align-items: stretch;
}

.card-grid__item {
  height: 100%;
}

.prompt-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border-radius: 12px;
  border: 1px solid transparent;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.prompt-card:hover {
  transform: translateY(-4px);
  border-color: #409eff33;
}

.prompt-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.prompt-class {
  margin: 0 0 4px;
  font-size: 13px;
  color: var(--text-weak-color);
}

.prompt-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.prompt-desc {
  margin: 16px 0;
  color: var(--header-text-color);
  font-size: 14px;
  line-height: 1.6;
  flex: 1;
}

.prompt-meta {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: var(--text-weak-color);
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-weight: 500;
}

.prompt-tags {
  margin-top: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
