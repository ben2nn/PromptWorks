import React, { useState } from 'react';
import Image from 'next/image';
import { getProxiedImageUrl, isS3Url } from '@/lib/utils';

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

  // S3 URL 直接用原生 img 标签，绕过 Next.js /_next/image 代理
  if (isS3Url(currentSrc)) {
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

    if (fill) {
      return (
        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
          {isLoading && (
            <div className="absolute inset-0 bg-gray-200 animate-pulse" />
          )}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={currentSrc}
            alt={alt}
            className={className}
            sizes={sizes}
            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }}
            onError={() => {
              if (currentSrc !== src && useProxy) {
                setCurrentSrc(src);
                return;
              }
              setImageError(true);
              setIsLoading(false);
            }}
            onLoad={() => setIsLoading(false)}
          />
        </div>
      );
    }

    return (
      <div style={{ position: 'relative' }}>
        {isLoading && (
          <div
            className={`absolute inset-0 bg-gray-200 animate-pulse ${className ?? ''}`}
          />
        )}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={currentSrc}
          alt={alt}
          width={width}
          height={height}
          className={className}
          sizes={sizes}
          onError={() => {
            if (currentSrc !== src && useProxy) {
              setCurrentSrc(src);
              return;
            }
            setImageError(true);
            setIsLoading(false);
          }}
          onLoad={() => setIsLoading(false)}
        />
      </div>
    );
  }

  // 非 S3 URL 使用 Next.js Image 组件
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
        onError={() => {
          if (currentSrc !== src && useProxy) {
            setCurrentSrc(src);
            return;
          }
          setImageError(true);
          setIsLoading(false);
        }}
        onLoad={() => setIsLoading(false)}
      />
    </div>
  );
};

export default SafeImage;