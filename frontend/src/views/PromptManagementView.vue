<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>Prompt 管理</h2>
        <p class="page-desc">集中管理不同业务场景的提示词，快速查看版本与负责人。</p>
      </div>
      <el-button type="primary" :icon="Plus" disabled>新建 Prompt</el-button>
    </section>

    <el-row :gutter="16" class="card-grid">
      <el-col
        v-for="prompt in prompts"
        :key="prompt.id"
        :xs="24"
        :sm="12"
        :md="8"
        class="card-grid__col"
      >
        <el-card class="prompt-card" shadow="hover" @click="goDetail(prompt.id)">
          <div class="prompt-card__header">
            <div>
              <h3 class="prompt-title">{{ prompt.name }}</h3>
              <p class="prompt-scenario">应用场景：{{ prompt.scenario }}</p>
            </div>
            <el-tag type="success" round size="small">
              当前版本 {{ prompt.latestVersion }}
            </el-tag>
          </div>
          <p class="prompt-desc">{{ prompt.description }}</p>
          <div class="prompt-meta">
            <div class="meta-item">
              <span class="meta-label">负责人</span>
              <span>{{ prompt.owner }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">更新</span>
              <span>{{ prompt.updatedAt }}</span>
            </div>
          </div>
          <div class="prompt-tags">
            <el-tag
              v-for="(tag, index) in prompt.tags"
              :key="tag"
              :type="tagTypes[index % tagTypes.length]"
              size="small"
              round
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import type { PromptSummary } from '../types/prompt'

const router = useRouter()

const prompts: PromptSummary[] = [
  {
    id: 'chat-sales',
    name: '销售跟进话术',
    description: '用于客服跟进潜在客户的对话模板，强调需求澄清与价值陈述。',
    tags: ['销售', '中文', '对话流程'],
    owner: '宋佳',
    scenario: '线索跟进与客户维护',
    updatedAt: '2025-09-18 10:20',
    latestVersion: 'v1.4.2'
  },
  {
    id: 'email-review',
    name: '邮件润色助手',
    description: '自动优化英文商务邮件措辞，确保语气礼貌、结构清晰。',
    tags: ['英文', '邮件', '润色'],
    owner: 'Alex Li',
    scenario: '市场团队邮件发送',
    updatedAt: '2025-09-12 08:45',
    latestVersion: 'v0.9.0'
  },
  {
    id: 'code-review',
    name: '代码审查要点',
    description: '引导 AI 关注性能、安全和规范的代码审查提示语。',
    tags: ['代码质量', '审查'],
    owner: '陈曦',
    scenario: '研发流程代码检查',
    updatedAt: '2025-09-21 14:05',
    latestVersion: 'v2.1.0'
  }
]

const tagTypes = ['primary', 'warning', 'info', 'success'] as const

function goDetail(id: string) {
  router.push({ name: 'prompt-detail', params: { id } })
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

.card-grid__col {
  margin-bottom: 16px;
}

.prompt-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border-radius: 12px;
  border: 1px solid transparent;
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

.prompt-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.prompt-scenario {
  margin: 4px 0 0;
  color: var(--text-weak-color);
  font-size: 13px;
}

.prompt-desc {
  margin: 16px 0;
  color: var(--header-text-color);
  font-size: 14px;
  line-height: 1.6;
}

.prompt-meta {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: var(--text-weak-color);
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
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
