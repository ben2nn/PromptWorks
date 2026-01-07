# 提示词导入示例脚本 (PowerShell)
# 演示完整的导入流程

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "提示词数据导入示例" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 确保分类存在
Write-Host "步骤 1/3: 确保 opennana 分类存在..." -ForegroundColor Yellow
python scripts\ensure_class.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 分类创建失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 2: 环境检查
Write-Host "步骤 2/3: 检查环境..." -ForegroundColor Yellow
python scripts\test_import.py prompts_20251025_192918.json
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 环境检查失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 3: 执行导入
Write-Host "步骤 3/3: 开始导入数据..." -ForegroundColor Yellow
python scripts\import_prompts.py prompts_20251025_192918.json
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 导入失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ 导入完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 显示统计信息
Write-Host ""
Write-Host "查看导入统计..." -ForegroundColor Cyan
python -c @"
from app.db.session import SessionLocal
from app.models.prompt import Prompt, PromptTag
from app.models.attachment import PromptAttachment

db = SessionLocal()
try:
    prompt_count = db.query(Prompt).filter(Prompt.class_id == 4).count()
    tag_count = db.query(PromptTag).count()
    attachment_count = db.query(PromptAttachment).filter(
        PromptAttachment.prompt_id.isnot(None)
    ).count()
    
    print(f'📊 导入统计:')
    print(f'  - 提示词: {prompt_count} 个')
    print(f'  - 标签: {tag_count} 个')
    print(f'  - 附件: {attachment_count} 个')
finally:
    db.close()
"@

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
