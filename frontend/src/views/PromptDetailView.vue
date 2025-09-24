<template>
  <div class="detail-page">
    <el-breadcrumb separator="/" class="detail-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goHome">Prompt 管理</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>{{ detail.name }}</el-breadcrumb-item>
    </el-breadcrumb>

    <section class="detail-header">
      <div>
        <h2 class="detail-title">{{ detail.name }}</h2>
        <p class="detail-subtitle">{{ detail.scenario }}</p>
      </div>
      <el-tag type="success" effect="light">当前版本 {{ detail.latestVersion }}</el-tag>
    </section>

    <el-row :gutter="20" class="detail-body">
      <el-col :xs="24" :md="16" class="detail-left">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <h3>版本对比</h3>
              <span class="card-subtitle">选择任意两个版本生成差异视图</span>
            </div>
          </template>
          <el-form :inline="true" label-width="80px" class="diff-form">
            <el-form-item label="基准版本">
              <el-select v-model="baseVersion" size="small" @change="handleVersionChange">
                <el-option
                  v-for="version in versionOptions"
                  :key="version"
                  :value="version"
                  :label="version"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="对比版本">
              <el-select v-model="compareVersion" size="small" @change="handleVersionChange">
                <el-option
                  v-for="version in versionOptions"
                  :key="version"
                  :value="version"
                  :label="version"
                />
              </el-select>
            </el-form-item>
          </el-form>
          <div v-if="!diffSegments.length" class="diff-empty">
            <el-empty description="版本内容一致或暂无差异" />
          </div>
          <div v-else class="diff-viewer">
            <div
              v-for="(segment, index) in diffSegments"
              :key="index"
              :class="['diff-line', diffClassMap[segment.type]]"
            >
              <span class="diff-symbol">{{ diffSymbols[segment.type] }}</span>
              <pre class="diff-content">{{ segment.text }}</pre>
            </div>
          </div>
        </el-card>

        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <h3>版本历史</h3>
              <span class="card-subtitle">查看每一次迭代的变更说明</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="version in detail.versions"
              :key="version.version"
              :timestamp="version.createdAt"
              placement="top"
            >
              <div class="timeline-item">
                <div class="timeline-header">
                  <strong>{{ version.version }}</strong>
                  <span class="timeline-author">{{ version.author }}</span>
                </div>
                <p class="timeline-change">{{ version.changeLog }}</p>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="8" class="detail-right">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <h3>Prompt 信息</h3>
              <span class="card-subtitle">基础元数据与标签</span>
            </div>
          </template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="负责人">{{ detail.owner }}</el-descriptions-item>
            <el-descriptions-item label="场景">{{ detail.scenario }}</el-descriptions-item>
            <el-descriptions-item label="最近更新">{{ detail.updatedAt }}</el-descriptions-item>
          </el-descriptions>
          <div class="detail-tags">
            <el-tag
              v-for="tag in detail.tags"
              :key="tag"
              type="info"
              round
              size="small"
            >
              {{ tag }}
            </el-tag>
          </div>
          <div class="detail-description">
            <h4>描述</h4>
            <p>{{ detail.description }}</p>
          </div>
        </el-card>

        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <h3>测试工作台</h3>
              <span class="card-subtitle">后续迭代将完善测试能力</span>
            </div>
          </template>
          <el-empty description="测试功能占位，敬请期待" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { PromptDetail } from '../types/prompt'
import { diffLines, type Change } from 'diff'

interface DiffSegment {
  type: 'added' | 'removed' | 'unchanged'
  text: string
}

const router = useRouter()
const route = useRoute()

const promptLibrary: Record<string, PromptDetail> = {
  'chat-sales': {
    id: 'chat-sales',
    name: '销售跟进话术',
    description: '指导客服与潜客对话的提示词，强调需求挖掘、价值陈述和下一步跟进。',
    tags: ['销售', '对话流程', '转化率'],
    owner: '宋佳',
    scenario: '线索跟进与客户维护',
    updatedAt: '2025-09-18 10:20',
    latestVersion: 'v1.4.2',
    versions: [
      {
        version: 'v1.4.2',
        createdAt: '2025-09-18 10:20',
        author: '宋佳',
        content: `你是资深销售顾问。
1. 先明确客户当前困扰。
2. 提炼产品价值主张。
3. 给出下一步可执行建议。
使用亲和、有温度的语气。`,
        changeLog: '优化价值主张描述，补充下一步建议。'
      },
      {
        version: 'v1.3.0',
        createdAt: '2025-09-10 09:05',
        author: 'Alex Li',
        content: `你是一名资深销售。
1. 询问客户目前的问题。
2. 简要阐述产品优势。
使用亲和语气，保持对话简洁。`,
        changeLog: '增强问题定位指引，语气更聚焦销售场景。'
      },
      {
        version: 'v1.0.0',
        createdAt: '2025-08-01 14:22',
        author: '陈曦',
        content: `你需要协助销售跟进潜在客户，整理合适的回复。`,
        changeLog: '首次创建。'
      }
    ]
  },
  'email-review': {
    id: 'email-review',
    name: '邮件润色助手',
    description: '帮助用户优化英文商务邮件，使其礼貌得体、结构清晰。',
    tags: ['英文', '邮件', '润色'],
    owner: 'Alex Li',
    scenario: '市场团队邮件发送',
    updatedAt: '2025-09-12 08:45',
    latestVersion: 'v0.9.0',
    versions: [
      {
        version: 'v0.9.0',
        createdAt: '2025-09-12 08:45',
        author: 'Alex Li',
        content: `You are a senior copy editor.
- Polish greetings and closings.
- Keep sentences concise and respectful.
- Offer two improved alternatives when possible.`,
        changeLog: '新增建议输出两套候选内容。'
      },
      {
        version: 'v0.5.0',
        createdAt: '2025-08-30 15:12',
        author: 'Will Chen',
        content: `You are a copy editor helping with business emails.
- Make tone polite.
- Check grammar.`,
        changeLog: '调整语气要求，强调语法检查。'
      }
    ]
  },
  'code-review': {
    id: 'code-review',
    name: '代码审查要点',
    description: '聚焦性能、安全和代码规范的审查提示语，帮助研发快速定位风险。',
    tags: ['代码质量', '审查'],
    owner: '陈曦',
    scenario: '研发流程代码检查',
    updatedAt: '2025-09-21 14:05',
    latestVersion: 'v2.1.0',
    versions: [
      {
        version: 'v2.1.0',
        createdAt: '2025-09-21 14:05',
        author: '陈曦',
        content: `你是资深代码审查专家。
请重点关注：
1. 性能热点与复杂度。
2. 安全漏洞与数据校验。
3. 代码风格与可维护性。
给出高优先级问题列表并附理由。`,
        changeLog: '新增高优先级问题输出要求。'
      },
      {
        version: 'v2.0.0',
        createdAt: '2025-09-15 10:30',
        author: '陈曦',
        content: `你是资深代码审查专家。
关注性能、安全、规范三大维度，输出改进建议。`,
        changeLog: '覆盖核心关注点，但缺少输出格式要求。'
      }
    ]
  }
}

const currentId = computed(() => (route.params.id as string) || 'chat-sales')

const detail = computed(() => promptLibrary[currentId.value] ?? promptLibrary['chat-sales'])

const versionOptions = computed(() => detail.value.versions.map((item) => item.version))

const baseVersion = ref('')
const compareVersion = ref('')

watch(
  detail,
  (value) => {
    baseVersion.value = value.versions[0]?.version ?? ''
    compareVersion.value = value.versions[1]?.version ?? value.versions[0]?.version ?? ''
  },
  { immediate: true }
)

const diffSymbols: Record<DiffSegment['type'], string> = {
  added: '+',
  removed: '-',
  unchanged: ' '
}

const diffClassMap: Record<DiffSegment['type'], string> = {
  added: 'diff-line--added',
  removed: 'diff-line--removed',
  unchanged: 'diff-line--unchanged'
}

const diffSegments = computed<DiffSegment[]>(() => {
  const base = detail.value.versions.find((item) => item.version === baseVersion.value)
  const target = detail.value.versions.find((item) => item.version === compareVersion.value)

  if (!base || !target || base.version === target.version) {
    return []
  }

  const changes: Change[] = diffLines(base.content, target.content)

  return changes.flatMap((change) => {
    const type: DiffSegment['type'] = change.added ? 'added' : change.removed ? 'removed' : 'unchanged'
    const lines = change.value.split('\n')
    if (lines[lines.length - 1] === '') {
      lines.pop()
    }
    return lines.map((line) => ({
      type,
      text: line.length ? line : ' '
    }))
  })
})

function handleVersionChange() {
  if (baseVersion.value === compareVersion.value) {
    const fallback = versionOptions.value.find((item) => item !== baseVersion.value)
    if (fallback) {
      compareVersion.value = fallback
    }
  }
}

function goHome() {
  router.push({ name: 'prompt-management' })
}
</script>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-breadcrumb {
  font-size: 13px;
}

.breadcrumb-link {
  cursor: pointer;
  color: inherit;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.detail-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.detail-subtitle {
  margin: 4px 0 0;
  color: var(--text-weak-color);
}

.detail-body {
  margin-top: 8px;
}

.detail-card {
  margin-bottom: 20px;
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
  color: var(--text-weak-color);
  font-size: 13px;
}

.diff-form {
  margin-bottom: 16px;
}

.diff-viewer {
  border: 1px solid var(--side-border-color);
  border-radius: 8px;
  background: var(--content-bg-color);
  max-height: 360px;
  overflow: auto;
  font-family: 'JetBrains Mono', 'Fira Mono', Consolas, monospace;
}

.diff-line {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 6px 12px;
  border-bottom: 1px solid var(--side-border-color);
  white-space: pre-wrap;
}

.diff-line:last-child {
  border-bottom: none;
}

.diff-line--added {
  background: rgba(103, 194, 58, 0.12);
}

.diff-line--removed {
  background: rgba(245, 108, 108, 0.15);
}

.diff-line--unchanged {
  background: transparent;
}

.diff-symbol {
  width: 16px;
  text-align: center;
  font-weight: 600;
}

.diff-content {
  margin: 0;
  font-size: 13px;
}

.diff-empty {
  padding: 24px 0;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.timeline-author {
  color: var(--text-weak-color);
}

.timeline-change {
  margin: 0;
  color: var(--header-text-color);
  font-size: 13px;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
}

.detail-description h4 {
  margin: 0 0 8px;
  font-size: 16px;
}

.detail-description p {
  margin: 0;
  line-height: 1.6;
  color: var(--header-text-color);
}
</style>
