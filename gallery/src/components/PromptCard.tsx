import React from 'react';
import Image from 'next/image';
import { PromptCardProps } from '@/types';
import { getFullImageUrl } from '@/lib/utils';

/**
 * PromptCard 组件 - 提示词卡片
 * 显示提示词的预览图片、标题和标签
 * 增强的悬停动画效果
 */
export const PromptCard: React.FC<PromptCardProps> = ({ prompt, onClick }) => {
  return (
    <div
      className="
        group relative overflow-hidden rounded-xl
        cursor-pointer flex flex-col
        shadow-md hover:shadow-xl dark:shadow-slate-900/50 dark:hover:shadow-slate-900/70
        transition-smooth
        hover:scale-[1.02] hover:-translate-y-1
        active:scale-[0.98] active:translate-y-0
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:focus-visible:ring-blue-400 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900
        border border-gray-200 dark:border-slate-700
        h-full
      "
      style={{ backgroundColor: 'var(--card-bg)' }}
      onClick={() => onClick(prompt)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(prompt);
        }
      }}
    >
      {/* 预览图片 */}
      <div className="relative w-full aspect-square bg-gray-100 dark:bg-slate-700 overflow-hidden">
        {prompt.attachments && prompt.attachments.length > 0 ? (
          <Image
            src={getFullImageUrl(prompt.attachments[0].thumbnail_url || prompt.attachments[0].download_url)}
            alt={prompt.name}
            fill
            className="object-cover transition-smooth group-hover:scale-105"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500">
            <svg
              className="w-16 h-16 opacity-30"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        )}
        
        {/* 悬停遮罩效果 - 渐变叠加 */}
        <div className="
          absolute inset-0 bg-gradient-to-t from-black/20 to-transparent
          opacity-0 group-hover:opacity-100
          transition-opacity duration-300 ease-out
        " />
        
        {/* 悬停时显示的查看图标 */}
        <div className="
          absolute inset-0 flex items-center justify-center
          opacity-0 group-hover:opacity-100
          transition-all duration-300 ease-out
          transform scale-75 group-hover:scale-100
        ">
          <div className="
            bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm rounded-full p-3
            shadow-lg
          ">
            <svg
              className="w-6 h-6 text-gray-800 dark:text-gray-200"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* 卡片内容 */}
      <div className="p-4 flex-1 flex flex-col">
        {/* 标题 */}
        <h3 className="
          text-base font-semibold text-gray-900 dark:text-gray-100
          line-clamp-2
          transition-colors duration-200
          group-hover:text-blue-600 dark:group-hover:text-blue-400
        ">
          {prompt.name}
        </h3>
        
        {/* 标签列表 - 显示所有标签，距离标题10px */}
        {prompt.tags && prompt.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-auto pt-[10px]">
            {prompt.tags.map((tag) => (
              <span
                key={tag.id}
                className="
                  inline-flex items-center px-2 py-1
                  text-xs font-medium rounded-md
                  transition-all duration-200
                  leading-none
                "
                style={{
                  backgroundColor: `${tag.color}20`,
                  color: tag.color,
                  border: `1px solid ${tag.color}40`
                }}
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}
      </div>
      
      {/* 底部装饰线 - 悬停时显示 */}
      <div className="
        absolute bottom-0 left-0 right-0 h-1
        bg-gradient-to-r from-blue-500 to-purple-500
        transform scale-x-0 group-hover:scale-x-100
        transition-transform duration-300 ease-out
        origin-left
      " />
    </div>
  );
};
