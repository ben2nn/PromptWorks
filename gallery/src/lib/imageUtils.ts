/**
 * 图像处理工具函数
 */

// 检查图像 URL 是否可访问
export const checkImageUrl = async (url: string): Promise<boolean> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5秒超时
    
    const response = await fetch(url, { 
      method: 'HEAD',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch (error) {
    console.warn(`图像 URL 检查失败: ${url}`, error);
    return false;
  }
};

// 生成占位符图像的 data URL
export const generatePlaceholderImage = (width: number = 400, height: number = 400, text: string = '图像加载失败'): string => {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return '';
  
  // 背景
  ctx.fillStyle = '#f3f4f6';
  ctx.fillRect(0, 0, width, height);
  
  // 图标
  ctx.fillStyle = '#9ca3af';
  ctx.font = '24px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  
  // 绘制图标（简单的图片符号）
  ctx.fillText('🖼️', width / 2, height / 2 - 20);
  
  // 文字
  ctx.font = '14px Arial';
  ctx.fillText(text, width / 2, height / 2 + 20);
  
  return canvas.toDataURL();
};

// 图像预加载函数
export const preloadImage = (src: string): Promise<boolean> => {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = src;
  });
};

// 批量预加载图像
export const preloadImages = async (urls: string[]): Promise<{ [key: string]: boolean }> => {
  const results: { [key: string]: boolean } = {};
  
  const promises = urls.map(async (url) => {
    const success = await preloadImage(url);
    results[url] = success;
    return { url, success };
  });
  
  await Promise.all(promises);
  return results;
};

// 获取图像的实际尺寸
export const getImageDimensions = (src: string): Promise<{ width: number; height: number } | null> => {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.onerror = () => {
      resolve(null);
    };
    img.src = src;
  });
};

// 图像 URL 验证
export const isValidImageUrl = (url: string): boolean => {
  try {
    const urlObj = new URL(url);
    const validProtocols = ['http:', 'https:', 'data:'];
    return validProtocols.includes(urlObj.protocol);
  } catch {
    return false;
  }
};

// 从错误中提取有用信息
export const getImageErrorMessage = (error: any): string => {
  if (error?.code === 'UND_ERR_SOCKET') {
    return '网络连接中断';
  }
  if (error?.code === 'EAI_AGAIN') {
    return 'DNS 解析失败';
  }
  if (error?.statusCode === 504) {
    return '服务器响应超时';
  }
  if (error?.statusCode === 404) {
    return '图像不存在';
  }
  if (error?.statusCode === 403) {
    return '访问被拒绝';
  }
  return '图像加载失败';
};