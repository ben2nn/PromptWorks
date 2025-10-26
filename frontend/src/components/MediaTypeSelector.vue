<template>
  <div class="media-type-selector">
    <el-select
      v-model="selectedType"
      placeholder="请选择媒体类型"
      @change="handleTypeChange"
      class="media-type-select"
    >
      <el-option
        v-for="type in mediaTypes"
        :key="type.value"
        :label="type.label"
        :value="type.value"
        class="media-type-option"
      >
        <div class="media-type-content">
          <el-icon class="media-type-icon" :color="type.color">
            <component :is="type.icon" />
          </el-icon>
          <span class="media-type-label">{{ type.label }}</span>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElSelect, ElOption, ElIcon } from 'element-plus'
import {
  Document,
  Picture,
  VideoPlay,
  Headset,
  EditPen
} from '@element-plus/icons-vue'
import { MediaType } from '../types/prompt'

// 组件属性
interface Props {
  modelValue?: MediaType
  disabled?: boolean
}

// 组件事件
interface Emits {
  (e: 'update:modelValue', value: MediaType): void
  (e: 'change', value: MediaType): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: MediaType.TEXT,
  disabled: false
})

const emit = defineEmits<Emits>()

// 响应式数据
const selectedType = ref<MediaType>(props.modelValue)

// 媒体类型配置
const mediaTypes = computed(() => [
  {
    value: MediaType.TEXT,
    label: '文本',
    icon: EditPen,
    color: '#409EFF',
    description: '纯文本提示词'
  },
  {
    value: MediaType.IMAGE,
    label: '图片',
    icon: Picture,
    color: '#67C23A',
    description: '包含图片的多模态提示词'
  },
  {
    value: MediaType.DOCUMENT,
    label: '文档',
    icon: Document,
    color: '#E6A23C',
    description: '文档类型提示词'
  },
  {
    value: MediaType.AUDIO,
    label: '音频',
    icon: Headset,
    color: '#F56C6C',
    description: '音频类型提示词'
  },
  {
    value: MediaType.VIDEO,
    label: '视频',
    icon: VideoPlay,
    color: '#909399',
    description: '视频类型提示词'
  }
])

// 监听外部值变化
watch(() => props.modelValue, (newValue) => {
  selectedType.value = newValue
})

// 处理类型变更
const handleTypeChange = (value: MediaType) => {
  emit('update:modelValue', value)
  emit('change', value)
}

// 获取当前选中类型的信息
const getCurrentTypeInfo = () => {
  return mediaTypes.value.find(type => type.value === selectedType.value)
}

// 暴露给父组件的方法
defineExpose({
  getCurrentTypeInfo
})
</script>

<style scoped>
.media-type-selector {
  width: 100%;
}

.media-type-select {
  width: 100%;
}

.media-type-option {
  padding: 8px 12px;
}

.media-type-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.media-type-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.media-type-label {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

/* 选项悬停效果 */
.media-type-option:hover .media-type-label {
  color: var(--el-color-primary);
}
</style>