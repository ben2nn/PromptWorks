<template>
  <div class="version-info">
    <el-tooltip :content="tooltipContent" placement="top">
      <span class="version-text">
        v{{ version }}
      </span>
    </el-tooltip>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getSystemVersion, type VersionInfo } from '@/api/system'

const version = ref('0.1.0')
const versionInfo = ref<VersionInfo | null>(null)

const tooltipContent = computed(() => {
  if (!versionInfo.value) {
    return `版本: ${version.value}`
  }
  
  const { version: ver, version_info, history } = versionInfo.value
  const currentVersionDesc = history[ver] || '当前版本'
  
  return `版本: ${ver}\n构建: ${version_info.join('.')}\n${currentVersionDesc}`
})

const fetchVersion = async () => {
  try {
    const data = await getSystemVersion()
    version.value = data.version
    versionInfo.value = data
  } catch (error) {
    console.warn('获取版本信息失败，使用默认版本号:', error)
  }
}

onMounted(() => {
  fetchVersion()
})
</script>

<style scoped>
.version-info {
  display: inline-block;
}

.version-text {
  font-size: 12px;
  color: #909399;
  cursor: pointer;
  user-select: none;
}

.version-text:hover {
  color: #409eff;
}</style>