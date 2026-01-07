import { NextRequest, NextResponse } from 'next/server';

/**
 * 图像代理 API 路由
 * 用于代理外部图像请求，处理 CORS 和网络问题
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const imageUrl = searchParams.get('url');
  
  if (!imageUrl) {
    return NextResponse.json(
      { error: '缺少图像 URL 参数' },
      { status: 400 }
    );
  }
  
  try {
    // 验证 URL 格式
    const url = new URL(imageUrl);
    if (!['http:', 'https:'].includes(url.protocol)) {
      return NextResponse.json(
        { error: '不支持的协议' },
        { status: 400 }
      );
    }
    
    // 设置请求超时
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时
    
    // 代理请求
    const response = await fetch(imageUrl, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
      },
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      console.warn(`图像代理失败: ${imageUrl} - ${response.status} ${response.statusText}`);
      return NextResponse.json(
        { 
          error: '图像获取失败',
          status: response.status,
          statusText: response.statusText 
        },
        { status: response.status }
      );
    }
    
    // 检查内容类型
    const contentType = response.headers.get('content-type');
    if (!contentType?.startsWith('image/')) {
      return NextResponse.json(
        { error: '响应不是图像类型' },
        { status: 400 }
      );
    }
    
    // 获取图像数据
    const imageBuffer = await response.arrayBuffer();
    
    // 返回图像数据
    return new NextResponse(imageBuffer, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Length': imageBuffer.byteLength.toString(),
        'Cache-Control': 'public, max-age=3600, s-maxage=3600', // 缓存1小时
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    });
    
  } catch (error: any) {
    console.error('图像代理错误:', error);
    
    let errorMessage = '图像加载失败';
    let statusCode = 500;
    
    if (error.name === 'AbortError') {
      errorMessage = '请求超时';
      statusCode = 408;
    } else if (error.code === 'ENOTFOUND' || error.code === 'EAI_AGAIN') {
      errorMessage = 'DNS 解析失败';
      statusCode = 502;
    } else if (error.code === 'ECONNREFUSED') {
      errorMessage = '连接被拒绝';
      statusCode = 502;
    } else if (error.code === 'ETIMEDOUT') {
      errorMessage = '连接超时';
      statusCode = 408;
    }
    
    return NextResponse.json(
      { 
        error: errorMessage,
        code: error.code,
        details: error.message 
      },
      { status: statusCode }
    );
  }
}

// 支持 OPTIONS 请求（CORS 预检）
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}