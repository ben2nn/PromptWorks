<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>测试任务</h2>
        <p class="page-desc">统一查看批量测试任务与执行状态，后续将支持任务创建与重跑。</p>
      </div>
      <el-button type="primary" :icon="Memo" disabled>新建测试任务</el-button>
    </section>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
        </div>
      </template>
      <el-table :data="[]" border stripe empty-text="暂未接入测试任务数据">
        <el-table-column prop="name" label="任务名称" min-width="160" />
        <el-table-column prop="prompt" label="关联 Prompt" min-width="160" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
        <el-table-column prop="updated_at" label="最近更新" min-width="160" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Memo } from '@element-plus/icons-vue'
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
