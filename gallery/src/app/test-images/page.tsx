'use client';

import React from 'react';
import SafeImage from '@/components/SafeImage';

/**
 * 图像加载测试页面
 * 用于测试图像代理和错误处理功能
 */

const testImages = [
  {
    id: 1,
    name: '正常图像',
    url: 'https://via.placeholder.com/300x300/4f46e5/ffffff?text=Normal+Image',
    description: '这是一个正常的图像，应该能正常加载'
  },
  {
    id: 2,
    name: '问题域名图像 (pw.hrids.com)',
    url: 'https://pw.hrids.com/api/v1/files/thumbnails/20_thumb.jpg',
    description: '这个图像来自有问题的域名，会通过代理加载'
  },
  {
    id: 3,
    name: '不存在的图像',
    url: 'https://httpstat.us/404',
    description: '这个 URL 会返回 404，应该显示错误占位符'
  },
  {
    id: 4,
    name: '超时图像',
    url: 'https://httpstat.us/200?sleep=15000',
    description: '这个请求会超时，应该显示错误占位符'
  }
];

export default function TestImagesPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            图像加载测试页面
          </h1>
          <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            这个页面用于测试图像代理功能和错误处理机制。包括正常图像、问题域名图像、404错误和超时情况。
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {testImages.map((image) => (
            <div
              key={image.id}
              className="bg-white dark:bg-slate-800 rounded-lg shadow-md overflow-hidden"
            >
              {/* 图像区域 */}
              <div className="relative aspect-square bg-gray-100 dark:bg-slate-700">
                <SafeImage
                  src={image.url}
                  alt={image.name}
                  fill
                  className="object-cover"
                  sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 25vw"
                />
              </div>

              {/* 信息区域 */}
              <div className="p-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  {image.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {image.description}
                </p>
                <div className="text-xs text-gray-500 dark:text-gray-500 break-all">
                  <strong>URL:</strong> {image.url}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 说明信息 */}
        <div className="mt-12 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-blue-900 dark:text-blue-100 mb-4">
            测试说明
          </h2>
          <div className="space-y-3 text-blue-800 dark:text-blue-200">
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                1
              </span>
              <div>
                <strong>正常图像:</strong> 应该正常显示，无需代理
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-yellow-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                2
              </span>
              <div>
                <strong>问题域名图像:</strong> 会自动通过 /api/image-proxy 代理加载
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                3
              </span>
              <div>
                <strong>404 错误:</strong> 显示"图像加载失败"占位符
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                4
              </span>
              <div>
                <strong>超时错误:</strong> 10秒后显示"图像加载失败"占位符
              </div>
            </div>
          </div>
        </div>

        {/* 返回首页 */}
        <div className="text-center mt-8">
          <a
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            返回首页
          </a>
        </div>
      </div>
    </div>
  );
}