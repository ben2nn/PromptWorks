<template>
  <div class="page">
    <section class="page-header">
      <div>
        <h2>LLMs 管理</h2>
        <p class="page-desc">集中配置可用的大模型服务，统一管理调用凭证和配额。</p>
      </div>
      <el-button type="primary" :icon="Plus" disabled>新增模型</el-button>
    </section>
    <el-empty description="后续迭代将支持模型管理配置" />
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
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

.page-desc {
  margin: 4px 0 0;
  color: var(--text-weak-color);
}
</style>
