<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>用量管理</h2>
        <p class="page-desc">汇总各模型与团队的调用用量，为配额管理和成本分析提供数据支撑。</p>
      </div>
      <el-button type="primary" :icon="Histogram" disabled>导出报表</el-button>
    </section>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>用量概览</span>
        </div>
      </template>
      <el-empty description="用量统计功能正在接入" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Histogram } from '@element-plus/icons-vue'
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

.card-header {
  font-size: 14px;
  font-weight: 600;
}
</style>
