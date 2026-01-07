#!/usr/bin/env node

/**
 * 图像加载测试脚本
 * 用于验证图像 URL 的可访问性
 */

const https = require('https');
const http = require('http');

// 测试图像 URL 列表（从错误日志中提取）
const testUrls = [
  'https://pw.hrids.com/api/v1/files/thumbnails/20_thumb.jpg',
  'https://pw.hrids.com/api/v1/files/thumbnails/musk-in-the-park_thumb.jpg',
  'https://pw.hrids.com/api/v1/files/thumbnails/13_thumb.png',
  'https://pw.hrids.com/api/v1/files/thumbnails/26_thumb.jpg',
  'https://pw.hrids.com/api/v1/files/thumbnails/23_thumb.png',
  'https://pw.hrids.com/api/v1/files/thumbnails/22_thumb.jpg',
  'https://pw.hrids.com/api/v1/files/thumbnails/24_thumb.png',
  'https://pw.hrids.com/api/v1/files/thumbnails/21_thumb.jpg',
  'https://pw.hrids.com/api/v1/files/thumbnails/25_thumb.jpg'
];

// 测试单个 URL
function testUrl(url) {
  return new Promise((resolve) => {
    const protocol = url.startsWith('https:') ? https : http;
    const timeout = 5000; // 5秒超时
    
    const req = protocol.get(url, { timeout }, (res) => {
      resolve({
        url,
        status: res.statusCode,
        success: res.statusCode >= 200 && res.statusCode < 300,
        headers: {
          'content-type': res.headers['content-type'],
          'content-length': res.headers['content-length']
        }
      });
    });
    
    req.on('error', (error) => {
      resolve({
        url,
        success: false,
        error: error.message,
        code: error.code
      });
    });
    
    req.on('timeout', () => {
      req.destroy();
      resolve({
        url,
        success: false,
        error: '请求超时'
      });
    });
  });
}

// 主测试函数
async function runTests() {
  console.log('🔍 开始测试图像 URL 可访问性...\n');
  
  const results = [];
  
  for (const url of testUrls) {
    console.log(`测试: ${url}`);
    const result = await testUrl(url);
    results.push(result);
    
    if (result.success) {
      console.log(`✅ 成功 (${result.status}) - ${result.headers['content-type'] || 'unknown'}`);
    } else {
      console.log(`❌ 失败 - ${result.error || result.status}`);
    }
    console.log('');
  }
  
  // 统计结果
  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log('📊 测试结果统计:');
  console.log(`✅ 成功: ${successful}/${testUrls.length}`);
  console.log(`❌ 失败: ${failed}/${testUrls.length}`);
  
  if (failed > 0) {
    console.log('\n🔧 建议的解决方案:');
    console.log('1. 检查网络连接');
    console.log('2. 验证域名 pw.hrids.com 是否可访问');
    console.log('3. 考虑使用图像代理或 CDN');
    console.log('4. 实现图像加载失败的降级处理');
  }
}

// 运行测试
runTests().catch(console.error);