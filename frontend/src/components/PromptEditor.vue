<template>
  <div class="prompt-editor">
    <!-- 编辑器顶部工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <h3 class="editor-title">
          {{ mode === 'create' ? '创建提示词' : '编辑提示词' }}
        </h3>
        <div v-if="form.name" class="current-prompt">
          {{ form.name }}
        </div>
      </div>
      <div class="toolbar-right">
        <el-button 
          v-if="mode === 'edit' && promptId"
          type="info"
          size="small"
          @click="handlePreview"
        >
          预览
        </el-button>
      </div>
    </div>

    <el-form 
      ref="formRef"
      :model="form" 
      :rules="formRules"
      label-width="120px" 
      class="editor-form"
    >
      <!-- 基本信息 -->
      <div class="form-section">
        <h4 class="section-title">基本信息</h4>
        
        <el-form-item label="提示词名称" prop="name" required>
          <el-input
            v-model="form.name"
            placeholder="请输入提示词名称"
            :disabled="disabled"
          />
        </el-form-item>
        
        <el-form-item label="媒体类型" prop="media_type" required>
          <MediaTypeSelector 
            v-model="form.media_type" 
            :disabled="disabled"
            @change="handleMediaTypeChange"
          />
          <div class="field-tip">
            选择提示词的媒体类型，不同类型支持不同的内容格式
          </div>
        </el-form-item>

        <!-- 版本信息 -->
        <el-form-item label="版本号" prop="version">
          <el-input
            v-model="form.version"
            placeholder="请输入版本号（如 1.0.0），留空则默认为 1.0.0"
            :disabled="disabled"
          />
          <div class="field-tip">
            {{ mode === 'create' ? '留空将使用默认版本号 1.0.0' : '留空将自动生成版本号' }}
          </div>
        </el-form-item>

        <el-form-item v-if="mode === 'edit'" label="版本说明" prop="summary">
          <el-input
            v-model="form.summary"
            type="textarea"
            :rows="2"
            placeholder="请输入本次更新的说明（可选）"
            :disabled="disabled"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="请输入提示词描述（可选）"
            :disabled="disabled"
          />
        </el-form-item>

        <el-form-item label="作者" prop="author">
          <el-input
            v-model="form.author"
            placeholder="请输入作者名称（可选）"
            :disabled="disabled"
          />
        </el-form-item>

        
      </div>

      <!-- 内容编辑 -->
      <div class="form-section">
        <h4 class="section-title">内容编辑</h4>
        
        <!-- 文本内容（所有媒体类型都显示） -->
        <el-form-item 
          label="英文提示词" 
          prop="content" 
          :required="form.media_type === MediaType.TEXT"
        >
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="8"
            :placeholder="form.media_type === MediaType.TEXT ? '请输入英文提示词内容' : '请输入英文提示词内容（可选）'"
            :disabled="disabled"
            show-word-limit
            :maxlength="10000"
          />
          <div class="field-tip">
            {{ form.media_type === MediaType.TEXT ? '支持 Markdown 格式，可以使用变量占位符如 {' + '{variable}' + '}' : '可选字段，用于补充说明附件内容或提供文本版本' }}
          </div>
        </el-form-item>

        <el-form-item 
          label="中文提示词" 
          prop="contentzh"
        >
          <el-input
            v-model="form.contentzh"
            type="textarea"
            :rows="8"
            placeholder="请输入中文提示词内容（可选）"
            :disabled="disabled"
            show-word-limit
            :maxlength="10000"
          />
          <div class="field-tip">
            可选字段，用于提供中文版本的提示词内容
          </div>
        </el-form-item>

        
      </div>

      <!-- 附件管理（当媒体类型非文本时显示） -->
      <div v-if="form.media_type !== MediaType.TEXT" class="form-section">
        <div class="section-header">
          <h4 class="section-title">附件 ({{ attachments.length }})</h4>
          <el-button 
            v-if="!disabled && attachments.length > 0"
            size="small" 
            type="danger" 
            text 
            @click="clearAllAttachments"
          >
            清空所有
          </el-button>
        </div>
        
        <div class="attachments-grid">
          <!-- 上传插件卡片 - 始终显示在第一个 -->
          <div v-if="!disabled" class="upload-card">
            <FileUploader
              ref="fileUploaderRef"
              :prompt-id="promptId"
              :media-type="form.media_type"
              :disabled="disabled"
              :defer-upload="mode === 'create'"
              @upload-success="handleAttachmentUpload"
              @upload-error="handleUploadError"
              @files-ready="handleFilesReady"
            />
          </div>
          
          <!-- 附件预览卡片 - 图片排在后面 -->
          <AttachmentPreview
            v-for="attachment in attachments"
            :key="attachment.id"
            :attachment="attachment"
            :is-grid-view="true"
            :show-actions="!disabled"
            @delete="handleAttachmentDelete"
            @preview="handleAttachmentPreview"
            @download="handleAttachmentDownload"
          />
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <el-button 
          type="primary" 
          :loading="isSubmitting"
          :disabled="disabled"
          @click="handleSubmit"
        >
          {{ mode === 'create' ? '创建提示词' : '保存更改' }}
        </el-button>
        <el-button @click="handleCancel">
          取消
        </el-button>

      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { 
  ElForm, 
  ElFormItem, 
  ElInput, 
  ElButton, 
  ElIcon,
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules
} from 'element-plus'
import { MediaType, type AttachmentInfo } from '../types/prompt'
import MediaTypeSelector from './MediaTypeSelector.vue'
import FileUploader from './FileUploader.vue'
import AttachmentPreview from './AttachmentPreview.vue'
import { attachmentApi } from '../api/attachment'

// 组件属性
interface Props {
  promptId?: number
  mode?: 'create' | 'edit'
  initialData?: Partial<PromptFormData>
  disabled?: boolean
}

// 表单数据接口
interface PromptFormData {
  name: string
  description: string
  author: string
  media_type: MediaType
  content: string
  contentzh?: string
  version: string
  summary: string
}

// 组件事件
interface Emits {
  (e: 'submit', data: PromptFormData & { attachments: AttachmentInfo[] }): void
  (e: 'cancel'): void
  (e: 'preview', data: PromptFormData & { attachments: AttachmentInfo[] }): void
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'create',
  disabled: false
})

const emit = defineEmits<Emits>()

// 响应式数据
const formRef = ref<FormInstance>()
const fileUploaderRef = ref<InstanceType<typeof FileUploader>>()
const attachments = ref<AttachmentInfo[]>([])
const pendingFiles = ref<File[]>([]) // 待上传的文件（创建模式）
const isSubmitting = ref(false)

// 表单数据
const form = reactive<PromptFormData>({
  name: '',
  description: '',
  author: '',
  media_type: MediaType.TEXT,
  content: '',
  contentzh: '',
  version: '',
  summary: ''
})

// 表单验证规则
const formRules = computed<FormRules>(() => ({
  name: [
    { required: true, message: '请输入提示词名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度应在 1 到 100 个字符', trigger: 'blur' }
  ],
  media_type: [
    { required: true, message: '请选择媒体类型', trigger: 'change' }
  ],
  version: [
    { max: 50, message: '版本号长度不能超过 50 个字符', trigger: 'blur' }
  ],
  content: form.media_type === MediaType.TEXT ? [
    { required: true, message: '请输入提示词内容', trigger: 'blur' },
    { min: 1, max: 10000, message: '内容长度应在 1 到 10000 个字符', trigger: 'blur' }
  ] : [
    { max: 10000, message: '内容长度不能超过 10000 个字符', trigger: 'blur' }
  ],
  attachments: []
}))

// 监听初始数据变化
watch(() => props.initialData, (newData) => {
  if (newData) {
    Object.assign(form, {
      name: newData.name || '',
      description: newData.description || '',
      author: newData.author || '',
      media_type: newData.media_type || MediaType.TEXT,
      content: newData.content || '',
      contentzh: newData.contentzh || '',
      version: newData.version || '',
      summary: newData.summary || ''
    })
    
    // 加载附件数据
    if (newData.attachments && Array.isArray(newData.attachments)) {
      attachments.value = [...newData.attachments]
    }
  }
}, { immediate: true, deep: true })

// 监听 promptId 变化，加载附件
watch(() => props.promptId, async (newId) => {
  if (newId && props.mode === 'edit') {
    await loadAttachments(newId)
  }
}, { immediate: true })

// 获取媒体类型描述
const getMediaTypeDescription = (mediaType: MediaType): string => {
  switch (mediaType) {
    case MediaType.IMAGE:
      return '支持 JPG、PNG、GIF、WebP 格式图片，单个文件不超过 10MB'
    case MediaType.DOCUMENT:
      return '支持 PDF、Word、文本文档，单个文件不超过 10MB'
    case MediaType.AUDIO:
      return '支持 MP3、WAV、OGG 音频文件，单个文件不超过 10MB'
    case MediaType.VIDEO:
      return '支持 MP4、AVI、MOV 视频文件，单个文件不超过 10MB'
    default:
      return '请选择合适的文件类型'
  }
}

// 加载附件列表
const loadAttachments = async (promptId: number) => {
  try {
    attachments.value = await attachmentApi.list(promptId)
  } catch (error) {
    console.error('加载附件失败:', error)
    ElMessage.error('加载附件失败')
  }
}

// 处理媒体类型变更
const handleMediaTypeChange = (newType: MediaType) => {
  // 如果从非文本类型切换到文本类型，询问是否清空附件
  if (newType === MediaType.TEXT && attachments.value.length > 0) {
    ElMessageBox.confirm(
      '切换到纯文本类型建议清空附件，是否清空？（可选择保留）',
      '确认切换',
      {
        confirmButtonText: '清空附件',
        cancelButtonText: '保留附件',
        type: 'warning'
      }
    ).then(() => {
      clearAllAttachments()
    }).catch(() => {
      // 用户选择保留附件，不做任何操作
    })
  }
  
  // 所有媒体类型都可以有文本内容，不需要清空
  // 只是在界面上调整必填状态和提示信息
}

// 处理附件上传成功
const handleAttachmentUpload = (attachment: AttachmentInfo) => {
  // 添加到附件列表以显示预览
  if (attachment && attachment.id) {
    attachments.value.push(attachment)
  }
}

// 处理上传错误
const handleUploadError = (error: Error) => {
  ElMessage.error('上传失败：' + error.message)
}

// 处理文件准备就绪（创建模式）
const handleFilesReady = (files: File[]) => {
  pendingFiles.value = files
}

// 处理附件删除
const handleAttachmentDelete = async (attachmentId: number) => {
  const index = attachments.value.findIndex(a => a.id === attachmentId)
  if (index > -1) {
    attachments.value.splice(index, 1)
    ElMessage.success('附件删除成功')
  }
}

// 处理附件预览
const handleAttachmentPreview = (attachment: AttachmentInfo) => {
  console.log('预览附件:', attachment)
}

// 处理附件下载
const handleAttachmentDownload = (attachment: AttachmentInfo) => {
  console.log('下载附件:', attachment)
}

// 清空所有附件
const clearAllAttachments = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除所有附件吗？此操作不可撤销。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 删除所有附件
    for (const attachment of attachments.value) {
      try {
        await attachmentApi.delete(attachment.id)
      } catch (error) {
        console.error('删除附件失败:', error)
      }
    }
    
    attachments.value = []
    ElMessage.success('所有附件已删除')
  } catch {
    // 用户取消
  }
}

// 处理表单提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    isSubmitting.value = true
    
    // 如果版本号为空，设置默认值
    const version = form.version.trim() || '1.0.0'
    
    const submitData = {
      ...form,
      version,
      attachments: attachments.value,
      pendingFiles: pendingFiles.value // 传递待上传的文件
    }
    
    emit('submit', submitData)
  } catch (error) {
    ElMessage.error('请检查表单填写是否正确')
  } finally {
    isSubmitting.value = false
  }
}

// 处理取消
const handleCancel = () => {
  emit('cancel')
}

// 处理预览
const handlePreview = () => {
  const previewData = {
    ...form,
    attachments: attachments.value
  }
  emit('preview', previewData)
}

// 关联临时附件到提示词
const attachPendingFiles = async (promptId: number): Promise<AttachmentInfo[]> => {
  if (!fileUploaderRef.value || pendingFiles.value.length === 0) {
    return []
  }
  
  try {
    const attachedFiles = await fileUploaderRef.value.attachToPrompt(promptId)
    attachments.value.push(...attachedFiles)
    pendingFiles.value = []
    return attachedFiles
  } catch (error) {
    console.error('关联附件失败:', error)
    throw error
  }
}

// 兼容旧方法名
const uploadPendingFiles = attachPendingFiles

// 暴露给父组件的方法
defineExpose({
  validate: () => formRef.value?.validate(),
  resetFields: () => formRef.value?.resetFields(),
  clearValidate: () => formRef.value?.clearValidate(),
  uploadPendingFiles,
  attachPendingFiles,
  getPendingFiles: () => pendingFiles.value
})
</script>

<style scoped>
.prompt-editor {
  width: 100%;
  height: 100%;
  min-height: calc(96vh - 120px);
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: var(--el-fill-color-blank);
  border-bottom: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  z-index: 100;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.editor-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.current-prompt {
  padding: 4px 12px;
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  gap: 24px;
}

.form-section {
  padding: 24px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  background-color: var(--el-fill-color-blank);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.form-section:hover {
  border-color: var(--el-border-color);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 2px solid var(--el-color-primary-light-8);
  padding-bottom: 12px;
  position: relative;
}

.section-title::before {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 40px;
  height: 2px;
  background-color: var(--el-color-primary);
  border-radius: 1px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.field-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.attachments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

/* 上传卡片样式 */
.upload-card {
  border: 2px dashed var(--el-border-color);
  border-radius: 12px;
  background-color: var(--el-fill-color-blank);
  transition: all 0.3s ease;
  overflow: hidden;
  aspect-ratio: 1;
  position: relative;
}

.upload-card:hover {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.upload-card :deep(.file-uploader) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.upload-card :deep(.upload-dragger) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.upload-card :deep(.el-upload) {
  width: 100%;
  height: 100%;
}

.upload-card :deep(.el-upload-dragger) {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 0;
  background: transparent;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0;
}

.upload-card :deep(.upload-content) {
  padding: 20px 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-card :deep(.upload-icon) {
  font-size: 36px;
  margin-bottom: 12px;
}

.upload-card :deep(.primary-text) {
  font-size: 13px;
  margin-bottom: 6px;
  text-align: center;
}

.upload-card :deep(.secondary-text) {
  font-size: 11px;
  line-height: 1.5;
  text-align: center;
  padding: 0 8px;
}

.form-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 24px;
  margin-top: auto;
  border-top: 1px solid var(--el-border-color-lighter);
  background-color: var(--el-fill-color-blank);
  border-radius: 12px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
  position: sticky;
  bottom: 0;
  z-index: 10;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .editor-toolbar {
    padding: 12px 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .toolbar-left {
    width: 100%;
    justify-content: space-between;
  }
  
  .editor-title {
    font-size: 16px;
  }
  
  .current-prompt {
    max-width: 150px;
  }
  
  .editor-form {
    padding: 16px;
  }
  
  .form-section {
    padding: 20px;
  }
  
  .attachments-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
  
  .upload-card :deep(.upload-content) {
    padding: 16px 12px;
  }
  
  .upload-card :deep(.upload-icon) {
    font-size: 32px;
    margin-bottom: 10px;
  }
  
  .upload-card :deep(.primary-text) {
    font-size: 12px;
  }
  
  .upload-card :deep(.secondary-text) {
    font-size: 10px;
  }
  
  .form-actions {
    flex-direction: column;
    padding: 20px;
  }
  
  .section-title {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .editor-form {
    padding: 12px;
  }
  
  .form-section {
    padding: 16px;
  }
  
  .form-actions {
    padding: 16px;
  }
  
  .attachments-grid {
    grid-template-columns: 1fr;
  }
  
  .upload-card :deep(.upload-content) {
    padding: 16px 12px;
  }
  
  .upload-card :deep(.upload-icon) {
    font-size: 28px;
    margin-bottom: 8px;
  }
  
  .upload-card :deep(.primary-text) {
    font-size: 12px;
    margin-bottom: 4px;
  }
  
  .upload-card :deep(.secondary-text) {
    font-size: 10px;
  }
}

/* 深度样式 */
:deep(.el-form-item__label) {
  font-weight: 500;
  font-size: 14px;
}

:deep(.el-textarea__inner) {
  font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
  line-height: 1.6;
  font-size: 14px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  transition: all 0.3s ease;
  resize: vertical;
  min-height: 120px;
}

:deep(.el-textarea__inner:focus) {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
}

:deep(.el-input__inner) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-input__inner:focus) {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
}

:deep(.el-input__count) {
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__content) {
  line-height: 1.5;
}

/* 编辑器特有样式 */
.editor-form :deep(.el-textarea) {
  position: relative;
}

.editor-form :deep(.el-textarea__inner[rows="8"]) {
  min-height: 200px;
  max-height: 400px;
}

/* 按钮样式优化 */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--el-color-primary), var(--el-color-primary-dark-2));
  border: none;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, var(--el-color-primary-light-3), var(--el-color-primary));
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* 滚动条样式 */
.editor-form::-webkit-scrollbar {
  width: 8px;
}

.editor-form::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.editor-form::-webkit-scrollbar-thumb {
  background: var(--el-border-color-dark);
  border-radius: 4px;
}

.editor-form::-webkit-scrollbar-thumb:hover {
  background: var(--el-text-color-secondary);
}
</style>