# 提示词双语支持更新

## 更新概述

为了更好地支持中英文差异，我们在提示词系统中新增了 `contentzh` 字段，用于存储中文版本的提示词内容。

## 数据库更改

### 新增字段
- `prompts_versions.contentzh`: 中文提示词内容（可选）

### 迁移文件
- `alembic/versions/e7e517f0f530_add_dual_prompt_fields.py`

## 后端更改

### 模型更新
- `app/models/prompt.py`: 在 `PromptVersion` 模型中添加 `contentzh` 字段
- `app/schemas/prompt.py`: 更新相关的 Pydantic 模式以支持新字段

### API 更新
- `app/api/v1/endpoints/prompts.py`: 更新创建和更新提示词的逻辑以处理 `contentzh` 字段

## 前端更改

### 类型定义
- `frontend/src/types/prompt.ts`: 在 `PromptVersion` 接口中添加 `contentzh` 字段
- `frontend/src/api/prompt.ts`: 更新 API 接口以支持新字段

### 组件更新
- `frontend/src/components/PromptEditor.vue`: 添加中文提示词输入框
- `frontend/src/views/PromptManagementView.vue`: 支持创建包含中文内容的提示词
- `frontend/src/views/PromptVersionCreateView.vue`: 支持创建包含中文内容的版本
- `frontend/src/views/PromptDetailView.vue`: 添加中英文内容切换显示功能

## 使用方式

### 创建包含中文内容的提示词
```python
# 后端示例
prompt_version = PromptVersion(
    prompt=prompt,
    version="v1.0.0",
    content="You are a helpful AI assistant.",  # 英文内容
    contentzh="你是一个有用的AI助手。"  # 中文内容（可选）
)
```

```typescript
// 前端示例
const payload: PromptCreatePayload = {
  name: "双语提示词",
  version: "v1.0.0",
  content: "You are a helpful AI assistant.",
  contentzh: "你是一个有用的AI助手。",  // 可选
  // ... 其他字段
}
```

### 前端功能
1. **创建提示词**: 在新建提示词页面，现在有两个文本框分别输入英文和中文内容
2. **版本管理**: 创建新版本时可以同时提供中英文内容
3. **内容查看**: 在提示词详情页面，如果有中文内容，会显示语言切换按钮
4. **复制功能**: 复制时会根据当前选择的语言复制对应的内容

## 向后兼容性

- ✅ 现有的提示词不受影响
- ✅ `content` 字段保持必填
- ✅ `contentzh` 字段为可选，不影响现有功能
- ✅ 所有现有 API 继续正常工作

## 测试验证

已通过以下测试：
- ✅ 数据库迁移成功
- ✅ 创建包含中英文内容的提示词
- ✅ 创建仅包含英文内容的提示词
- ✅ 查询和更新功能正常
- ✅ 后端代码无语法错误
- ✅ 前端组件无语法错误
- ✅ API 接口支持新字段

## 注意事项

1. `contentzh` 字段为可选，可以为 `null`
2. 现有的验证逻辑仍然基于 `content` 字段（英文内容必填）
3. 前端界面已更新支持双语编辑和显示功能
4. 语言切换功能仅在有中文内容时显示
5. 复制功能会根据当前选择的语言复制对应内容