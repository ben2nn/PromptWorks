<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>快速测试</h2>
        <p class="page-desc">针对单个 Prompt 快速发起临时调用，验证模型输出效果。</p>
      </div>
      <el-button type="primary" :icon="MagicStick" disabled>快速调试</el-button>
    </section>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试输入</span>
        </div>
      </template>
      <el-form label-width="100px" class="dialog-form">
        <el-form-item label="选择 Prompt">
          <el-select placeholder="功能待接入" disabled>
            <el-option label="示例 Prompt" value="demo" />
          </el-select>
        </el-form-item>
        <el-form-item label="变量输入">
          <el-input type="textarea" :autosize="{ minRows: 4, maxRows: 8 }" placeholder="变量配置功能待接入" disabled />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试结果</span>
        </div>
      </template>
      <el-empty description="待触发快速测试后展示模型响应" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { MagicStick } from '@element-plus/icons-vue'
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

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
