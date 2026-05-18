import React, { useState } from 'react';
import Image from 'next/image';
import { getProxiedImageUrl, getPlaceholderImageUrl, isS3Url } from '@/lib/utils';
import s3Loader from '@/lib/s3Loader';

interface SafeImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  fill?: boolean;
  sizes?: string;
  priority?: boolean;
  placeholder?: 'blur' | 'empty';
  blurDataURL?: string;
  useProxy?: boolean;
}

// 安全的图像组件 - 处理加载失败的情况
export const SafeImage: React.FC<SafeImageProps> = ({
  src,
  alt,
  width,
  height,
  className,
  fill,
  sizes,
  priority,
  placeholder,
  blurDataURL,
  useProxy = true,
}) => {
  const [imageError, setImageError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentSrc, setCurrentSrc] = useState(() => getProxiedImageUrl(src, useProxy));

  // 如果图像加载失败，显示占位符
  if (imageError) {
    return (
      <div 
        className={`bg-gray-200 flex items-center justify-center ${className}`}
        style={{ width, height }}
      >
        <div className="text-gray-400 text-center p-4">
          <svg 
            className="w-8 h-8 mx-auto mb-2" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
            />
          </svg>
          <p className="text-xs">图像加载失败</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      {isLoading && (
        <div 
          className={`absolute inset-0 bg-gray-200 animate-pulse ${className}`}
          style={{ width, height }}
        />
      )}
      <Image
        src={currentSrc}
        alt={alt}
        width={width}
        height={height}
        className={className}
        fill={fill}
        sizes={sizes}
        priority={priority}
        placeholder={placeholder}
        blurDataURL={blurDataURL}
        loader={isS3Url(currentSrc) ? s3Loader : undefined}
        onError={() => {
          console.warn(`图像加载失败: ${currentSrc}`);
          
          // 如果当前使用的是代理 URL，尝试使用原始 URL
          if (currentSrc !== src && useProxy) {
            console.log(`尝试使用原始 URL: ${src}`);
            setCurrentSrc(src);
            return;
          }
          
          // 如果原始 URL 也失败，显示错误状态
          setImageError(true);
          setIsLoading(false);
        }}
        onLoad={() => {
          setIsLoading(false);
        }}
      />
    </div>
  );
};

export default SafeImage;