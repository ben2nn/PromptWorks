/**
 * 工具函数集合
 */

/**
 * 将相对路径的图片 URL 转换为完整 URL
 * @param url 图片 URL（可能是相对路径或完整 URL）
 * @returns 完整的图片 URL
 */
export const getFullImageUrl = (url: string | undefined | null): string => {
  if (!url) return '/placeholder.svg';
  
  // 如果已经是完整 URL，直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  
  // 如果是相对路径，拼接后端 API 地址
  const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  return `${baseURL}${url.startsWith('/') ? url : `/${url}`}`;
};

/**
 * 获取代理后的图像 URL
 * 用于处理外部图像加载问题
 * @param originalUrl 原始图像 URL
 * @param useProxy 是否使用代理（默认为 true）
 * @returns 代理后的图像 URL 或原始 URL
 */
export const getProxiedImageUrl = (originalUrl: string, useProxy: boolean = true): string => {
  if (!originalUrl || !useProxy) return originalUrl;
  
  // 只对外部 URL 使用代理
  if (originalUrl.startsWith('http://') || originalUrl.startsWith('https://')) {
    // 检查是否是已知的问题域名
    const problematicDomains = ['pw.hrids.com'];
    const url = new URL(originalUrl);
    
    if (problematicDomains.some(domain => url.hostname.includes(domain))) {
      return `/api/image-proxy?url=${encodeURIComponent(originalUrl)}`;
    }
  }
  
  return originalUrl;
};

/**
 * 检查是否应该使用图像代理
 * @param url 图像 URL
 * @returns 是否应该使用代理
 */
export const shouldUseImageProxy = (url: string): boolean => {
  if (!url) return false;
  
  try {
    const urlObj = new URL(url);
    const problematicDomains = ['pw.hrids.com'];
    return problematicDomains.some(domain => urlObj.hostname.includes(domain));
  } catch {
    return false;
  }
};

/**
 * 生成占位符图像 URL
 * @param width 宽度
 * @param height 高度
 * @param text 显示文本
 * @returns 占位符图像 URL
 */
export const getPlaceholderImageUrl = (
  width: number = 400, 
  height: number = 400, 
  text: string = '图像加载失败'
): string => {
  return `https://via.placeholder.com/${width}x${height}/f3f4f6/9ca3af?text=${encodeURIComponent(text)}`;
};
