#!/bin/bash
# 提示词导入示例脚本
# 演示完整的导入流程

echo "=========================================="
echo "提示词数据导入示例"
echo "=========================================="
echo ""

# 步骤 1: 确保分类存在
echo "步骤 1/3: 确保 opennana 分类存在..."
python scripts/ensure_class.py
if [ $? -ne 0 ]; then
    echo "❌ 分类创建失败"
    exit 1
fi
echo ""

# 步骤 2: 环境检查
echo "步骤 2/3: 检查环境..."
python scripts/test_import.py prompts_20251025_192918.json
if [ $? -ne 0 ]; then
    echo "❌ 环境检查失败"
    exit 1
fi
echo ""

# 步骤 3: 执行导入
echo "步骤 3/3: 开始导入数据..."
python scripts/import_prompts.py prompts_20251025_192918.json
if [ $? -ne 0 ]; then
    echo "❌ 导入失败"
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ 导入完成！"
echo "=========================================="
