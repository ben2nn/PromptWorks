# Gallery 项目部署脚本
# 用于 Windows 环境下的项目部署

param(
    [string]$Environment = "development",
    [switch]$SkipBuild = $false,
    [switch]$SkipInstall = $false
)

Write-Host "🚀 开始部署 Gallery 项目..." -ForegroundColor Green
Write-Host "环境: $Environment" -ForegroundColor Yellow

# 检查 Node.js 和 npm
Write-Host "📋 检查环境依赖..." -ForegroundColor Blue
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
    Write-Host "✅ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 请先安装 Node.js 和 npm" -ForegroundColor Red
    exit 1
}

# 检查 Sharp 依赖
Write-Host "🔍 检查 Sharp 依赖..." -ForegroundColor Blue
if (Test-Path "node_modules/sharp") {
    Write-Host "✅ Sharp 已安装" -ForegroundColor Green
} else {
    Write-Host "⚠️ Sharp 未安装，将在安装依赖时自动安装" -ForegroundColor Yellow
}

# 安装依赖
if (-not $SkipInstall) {
    Write-Host "📦 安装项目依赖..." -ForegroundColor Blue
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 依赖安装完成" -ForegroundColor Green
}

# 构建项目
if (-not $SkipBuild) {
    Write-Host "🔨 构建项目..." -ForegroundColor Blue
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 项目构建失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 项目构建完成" -ForegroundColor Green
}

# 运行图像测试
Write-Host "🧪 运行图像加载测试..." -ForegroundColor Blue
node scripts/test-images.js

# 启动应用
Write-Host "🌟 启动应用..." -ForegroundColor Blue
if ($Environment -eq "production") {
    Write-Host "生产模式启动..." -ForegroundColor Yellow
    npm run start
} else {
    Write-Host "开发模式启动..." -ForegroundColor Yellow
    Write-Host "访问 http://localhost:3000 查看应用" -ForegroundColor Cyan
    Write-Host "访问 http://localhost:3000/test-images 测试图像加载" -ForegroundColor Cyan
    npm run dev
}

Write-Host "🎉 部署完成！" -ForegroundColor Green