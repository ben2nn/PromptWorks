# 提示词导入脚本使用指南

## 概述

`import_prompts.py` 脚本用于从 JSON 文件批量导入提示词数据到数据库。

## 功能特性

1. ✅ 自动解析 JSON 数据结构
2. ✅ 优先插入所有唯一的标签（tags）
3. ✅ 自动下载图片并上传到系统
4. ✅ 自动生成缩略图
5. ✅ 智能分离中英文提示词内容
6. ✅ 自动关联分类与标签
7. ✅ 错误处理和进度显示

## 使用方法

### 基本用法

```bash
python scripts/import_prompts.py <json_file> [class_id]
```

### 参数说明

- `json_file`: JSON 数据文件路径（必需）
- `class_id`: 目标分类 ID（可选，默认为 4，即 opennana 分类）

### 示例

```bash
# 使用默认分类 ID (4)
python scripts/import_prompts.py prompts_20251025_192918.json

# 指定分类 ID
python scripts/import_prompts.py prompts_20251025_192918.json 5
```

## JSON 数据格式

脚本期望的 JSON 格式如下：

```json
{
  "metadata": {
    "export_time": "2025-10-25T19:29:18.271184",
    "total_count": 367,
    "data_source": "opennana.com"
  },
  "prompts": [
    {
      "id": "prompt_xxx",
      "title": "案例标题",
      "content": "英文提示词内容\n\n=== 提示词 ===\n\n中文提示词内容",
      "category": "AI提示词",
      "tags": ["tag1", "tag2"],
      "image_url": "https://example.com/image.jpg",
      "source_url": "https://example.com"
    }
  ]
}
```

## 内容分离规则

脚本会自动分离中英文内容：

1. **包含分隔符**: 如果内容包含 `=== 提示词 ===`，则分隔符前为英文，后为中文
2. **自动判断**: 如果没有分隔符，根据中文字符占比判断：
   - 中文字符 > 30%：视为中文内容
   - 中文字符 ≤ 30%：视为英文内容

## 标签颜色

脚本会为新创建的标签自动分配颜色，使用预定义的调色板：

```python
["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
 "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52B788"]
```

## 图片处理

1. **下载**: 从 `image_url` 下载图片
2. **存储**: 保存到 `uploads/attachments/` 目录
3. **缩略图**: 自动生成缩略图并保存到 `uploads/thumbnails/`
4. **元数据**: 提取图片分辨率等信息

## 错误处理

- 单个提示词导入失败不会影响其他提示词
- 图片下载失败不会阻止提示词创建
- 缩略图生成失败会记录错误但继续导入
- 每个提示词的导入状态都会显示

## 输出示例

```
读取文件: prompts_20251025_192918.json
找到 367 个提示词
目标分类: opennana

开始导入...

[1/367] 导入: 案例 368：影楼拍摄女性坐在椅子上肖像照
  ✓ 创建标签: fashion
  ✓ 创建标签: portrait
  → 下载图片: https://opennana.com/awesome-prompt-gallery/images/368.jpeg
  ✓ 图片已上传: abc123.jpeg
  ✓ 提示词已创建 (ID: 1)
    - 标签: fashion, portrait
    - 附件: abc123.jpeg

[2/367] 导入: 案例 367：一位年轻女性的时尚电影肖像
  → 下载图片: https://opennana.com/awesome-prompt-gallery/images/367.jpeg
  ✓ 图片已上传: def456.jpeg
  ✓ 提示词已创建 (ID: 2)
    - 标签: fashion, interior, portrait
    - 附件: def456.jpeg

...

============================================================
导入完成!
  成功: 365
  失败: 2
  总计: 367
============================================================
```

## 前置条件

1. **数据库**: 确保数据库已启动并可连接
2. **分类**: 目标分类 ID 必须存在（默认 ID 4）
3. **依赖**: 安装所有必需的 Python 包
4. **存储**: 确保有足够的磁盘空间存储图片

## 依赖包

```
httpx
sqlalchemy
pillow (用于图片处理)
```

## 注意事项

1. **网络连接**: 需要稳定的网络连接以下载图片
2. **执行时间**: 导入大量数据可能需要较长时间
3. **数据库事务**: 每个提示词使用独立事务，失败不影响其他
4. **文件权限**: 确保对 `uploads/` 目录有写权限

## 故障排查

### 数据库连接失败

检查 `.env` 文件中的 `DATABASE_URL` 配置。

### 分类不存在

确保目标分类 ID 在数据库中存在，或使用正确的 class_id 参数。

### 图片下载失败

- 检查网络连接
- 验证图片 URL 是否有效
- 图片下载失败不会阻止提示词创建

### 权限错误

确保对以下目录有写权限：
- `uploads/attachments/`
- `uploads/thumbnails/`

## 高级用法

### 只导入部分数据

修改 JSON 文件，只保留需要导入的提示词。

### 自定义分类

创建新的分类并使用其 ID：

```bash
python scripts/import_prompts.py data.json 10
```

### 批量导入多个文件

```bash
for file in *.json; do
    python scripts/import_prompts.py "$file"
done
```

## 维护

定期清理临时附件：

```python
from app.services.attachment import attachment_service
from app.db.session import SessionLocal

db = SessionLocal()
cleaned = attachment_service.cleanup_temporary_attachments(db, older_than_hours=24)
print(f"清理了 {cleaned} 个临时附件")
db.close()
```
