import React, { useState } from 'react';
import Image from 'next/image';
import { PromptModalProps } from '@/types';
import { Modal } from './ui/Modal';
import { getFullImageUrl } from '@/lib/utils';

/**
 * PromptModal 组件 - 提示词详情弹框
 * 显示提示词的完整信息，包括标题、来源、标签、示例图片和内容
 * 增强的视觉效果和动画
 */
export const PromptModal: React.FC<PromptModalProps> = ({
  prompt,
  isOpen,
  onClose,
}) => {
  // 为每个内容块管理独立的复制状态
  const [copyStates, setCopyStates] = useState<Record<string, boolean>>({});

  // 如果没有提示词数据，不渲染
  if (!prompt) return null;

  // 复制单个内容块到剪贴板
  const handleCopyContent = async (content: string, contentId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopyStates(prev => ({ ...prev, [contentId]: true }));
      
      // 3秒后重置复制成功状态
      setTimeout(() => {
        setCopyStates(prev => ({ ...prev, [contentId]: false }));
      }, 3000);
    } catch (error) {
      console.error('复制失败:', error);
    }
  };

  // 创建复制按钮组件
  const CopyButton: React.FC<{ content: string; contentId: string; size?: 'sm' | 'md' }> = ({ 
    content, 
    contentId, 
    size = 'sm' 
  }) => {
    const isSuccess = copyStates[contentId];
    
    return (
      <button
        onClick={() => handleCopyContent(content, contentId)}
        className={`
          ${size === 'sm' ? 'px-2 py-1 text-xs' : 'px-3 py-1.5 text-sm'} 
          rounded-md font-medium
          transition-all duration-200 ease-out
          flex items-center gap-1.5
          shadow-sm hover:shadow-md
          active:scale-95
          focus:outline-none focus:ring-2 focus:ring-offset-1
          ${
            isSuccess
              ? 'bg-green-600 hover:bg-green-700 text-white focus:ring-green-400'
              : 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-400'
          }
        `}
        type="button"
        aria-label={isSuccess ? '已复制到剪贴板' : '复制内容到剪贴板'}
        title={isSuccess ? '已复制' : '复制'}
      >
        {isSuccess ? (
          <>
            <svg
              className={`${size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} animate-scale-in`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            已复制
          </>
        ) : (
          <>
            <svg
              className={`${size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
            复制
          </>
        )}
      </button>
    );
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="p-6 sm:p-8 max-h-[90vh] overflow-y-auto ultra-smooth-scroll">
        {/* 头部：标题和关闭按钮 */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1 pr-4">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3 leading-tight">
              {prompt.name}
            </h2>
            
            {/* 来源信息 */}
            {prompt.author && (
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
                <span>作者: <span className="font-medium text-gray-900 dark:text-gray-100">{prompt.author}</span></span>
              </div>
            )}
          </div>

          {/* 关闭按钮 */}
          <button
            onClick={onClose}
            className="
              flex-shrink-0 p-2 rounded-lg
              text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700
              transition-all duration-200 ease-out
              active:scale-90
              focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:ring-offset-2 dark:focus:ring-offset-slate-800
            "
            type="button"
            aria-label="关闭对话框"
            title="关闭"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* 标签列表 */}
        <div className="flex flex-wrap gap-2 mb-8">
          {prompt.tags.map((tag, index) => (
            <span
              key={tag.id}
              className="
                px-3 py-1.5 text-sm font-medium
                rounded-full
                border
                shadow-sm
                animate-fade-in
              "
              style={{
                backgroundColor: `${tag.color}15`,
                color: tag.color,
                borderColor: `${tag.color}40`,
                animationDelay: `${index * 50}ms`,
                animationFillMode: 'backwards'
              }}
            >
              {tag.name}
            </span>
          ))}
        </div>

        {/* 示例图片展示 - 显示所有图片 */}
        {prompt.attachments && prompt.attachments.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
              <svg
                className="w-5 h-5 text-blue-600 dark:text-blue-400"
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
              示例图片
              <span className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded-full">
                {prompt.attachments.length} 张
              </span>
            </h3>
            
            {/* 根据图片数量调整布局 */}
            <div className={`
              grid gap-4
              ${prompt.attachments.length === 1 ? 'grid-cols-1 max-w-md mx-auto' : 
                prompt.attachments.length === 2 ? 'grid-cols-1 md:grid-cols-2' :
                prompt.attachments.length === 3 ? 'grid-cols-1 md:grid-cols-3' :
                'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'}
            `}>
              {prompt.attachments.map((attachment, attachmentIndex) => (
                <div
                  key={attachment.id || attachmentIndex}
                  className="
                    relative w-full aspect-square rounded-xl overflow-hidden
                    bg-gray-100 dark:bg-slate-700 shadow-md dark:shadow-slate-900/50
                    group cursor-pointer
                    animate-fade-in
                    hover:shadow-xl transition-all duration-300
                  "
                  style={{
                    animationDelay: `${attachmentIndex * 100}ms`,
                    animationFillMode: 'backwards'
                  }}
                >
                  <Image
                    src={getFullImageUrl(attachment.download_url || attachment.thumbnail_url)}
                    alt={attachment.original_filename || attachment.filename || `示例图片 ${attachmentIndex + 1}`}
                    fill
                    className="object-cover transition-transform duration-300 group-hover:scale-110"
                    sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
                  />
                  
                  {/* 悬停遮罩和信息 */}
                  <div className="
                    absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent
                    opacity-0 group-hover:opacity-100
                    transition-opacity duration-300
                    flex flex-col justify-end p-3
                  ">
                    <div className="text-white text-sm">
                      <p className="font-medium truncate">
                        {attachment.original_filename || attachment.filename}
                      </p>
                      {attachment.file_size && (
                        <p className="text-xs opacity-80">
                          {(attachment.file_size / 1024 / 1024).toFixed(1)} MB
                        </p>
                      )}
                    </div>
                  </div>
                  
                  {/* 图片序号 */}
                  <div className="absolute top-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded-full">
                    {attachmentIndex + 1}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 提示词内容区域 - 显示所有版本 */}
        <div>
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <svg
                className="w-5 h-5 text-blue-600 dark:text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              提示词内容
              {prompt.versions && prompt.versions.length > 1 && (
                <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-full">
                  {prompt.versions.length} 个版本
                </span>
              )}
            </h3>
          </div>

          {/* 显示所有提示词版本 */}
          <div className="space-y-4">
            {/* 当前版本 */}
            {prompt.current_version && (
              <div className="space-y-4">
                {/* 版本号单独显示 */}
                <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-600">
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    当前版本: {prompt.current_version.version}
                  </span>
                  <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-full">
                    最新
                  </span>
                </div>

                {/* 提示词内容 */}
                {(() => {
                  const hasContent = prompt.current_version.content;
                  const hasContentZh = prompt.current_version.contentzh;
                  
                  if (hasContent && hasContentZh) {
                    // 两个内容都有，显示"提示词1"和"提示词2"
                    return (
                      <div className="space-y-4">
                        <div className="relative p-5 rounded-xl border-2 border-blue-200 dark:border-blue-600 shadow-inner"
                          style={{
                            background: 'linear-gradient(to bottom right, var(--surface), var(--background))'
                          }}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                              提示词1
                            </span>
                            <CopyButton 
                              content={prompt.current_version.content || ''} 
                              contentId={`current-content-${prompt.current_version.id}`}
                            />
                          </div>
                          <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                            {prompt.current_version.content}
                          </pre>
                          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-300 dark:via-blue-500 to-transparent" />
                        </div>
                        
                        <div className="relative p-5 rounded-xl border-2 border-blue-200 dark:border-blue-600 shadow-inner"
                          style={{
                            background: 'linear-gradient(to bottom right, var(--surface), var(--background))'
                          }}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                              提示词2
                            </span>
                            <CopyButton 
                              content={prompt.current_version.contentzh || ''} 
                              contentId={`current-contentzh-${prompt.current_version.id}`}
                            />
                          </div>
                          <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                            {prompt.current_version.contentzh}
                          </pre>
                          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-300 dark:via-blue-500 to-transparent" />
                        </div>
                      </div>
                    );
                  } else {
                    // 只有一个内容，显示"提示词"
                    return (
                      <div className="relative p-5 rounded-xl border-2 border-blue-200 dark:border-blue-600 shadow-inner"
                        style={{
                          background: 'linear-gradient(to bottom right, var(--surface), var(--background))'
                        }}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                            提示词
                          </span>
                          <CopyButton 
                            content={hasContent ? prompt.current_version.content : prompt.current_version.contentzh || '暂无内容'} 
                            contentId={`current-single-${prompt.current_version.id}`}
                          />
                        </div>
                        <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                          {hasContent ? prompt.current_version.content : prompt.current_version.contentzh || '暂无内容'}
                        </pre>
                        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-300 dark:via-blue-500 to-transparent" />
                      </div>
                    );
                  }
                })()}
              </div>
            )}

            {/* 其他版本 */}
            {prompt.versions && prompt.versions.length > 0 && (
              <>
                {prompt.versions
                  .filter(version => version.id !== prompt.current_version?.id)
                  .map((version) => (
                    <div key={version.id} className="space-y-4">
                      {/* 版本号单独显示 */}
                      <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-600">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          版本: {version.version}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(version.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      {/* 提示词内容 */}
                      {(() => {
                        const hasContent = version.content;
                        const hasContentZh = version.contentzh;
                        
                        if (hasContent && hasContentZh) {
                          // 两个内容都有，显示"提示词1"和"提示词2"
                          return (
                            <div className="space-y-4">
                              <div className="relative p-5 rounded-xl border-2 border-gray-200 dark:border-slate-600 shadow-inner"
                                style={{
                                  background: 'linear-gradient(to bottom right, var(--surface), var(--background))'
                                }}
                              >
                                <div className="flex items-center justify-between mb-3">
                                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                                    提示词1
                                  </span>
                                  <CopyButton 
                                    content={version.content || ''} 
                                    contentId={`version-content-${version.id}`}
                                  />
                                </div>
                                <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                                  {version.content}
                                </pre>
                                <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-slate-500 to-transparent" />
                              </div>
                              
                              <div className="relative p-5 rounded-xl border-2 border-gray-200 dark:border-slate-600 shadow-inner"
                                style={{
                                  background: 'linear-gradient(to bottom right, var(--surface), var(--background))'
                                }}
                              >
                                <div className="flex items-center justify-between mb-3">
                                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                                    提示词2
                                  </span>
                                  <CopyButton 
                                    content={version.contentzh || ''} 
                                    contentId={`version-contentzh-${version.id}`}
                                  />
                                </div>
                                <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                                  {version.contentzh}
                                </pre>
                                <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-slate-500 to-transparent" />
                              </div>
                            </div>
                          );
                        } else {
                          // 只有一个内容，显示"提示词"
                          return (
                            <div className="relative p-5 rounded-xl border-2 border-gray-200 dark:border-slate-600 shadow-inner"
                              style={{
                                background: 'linear-gradient(to bottom right, var(--surface), var(--background))'
                              }}
                            >
                              <div className="flex items-center justify-between mb-3">
                                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                                  提示词
                                </span>
                                <CopyButton 
                                  content={hasContent ? version.content : version.contentzh || '暂无内容'} 
                                  contentId={`version-single-${version.id}`}
                                />
                              </div>
                              <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                                {hasContent ? version.content : version.contentzh || '暂无内容'}
                              </pre>
                              <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-slate-500 to-transparent" />
                            </div>
                          );
                        }
                      })()}
                    </div>
                  ))}
              </>
            )}

            {/* 如果没有版本信息，显示基础内容 */}
            {!prompt.current_version && (!prompt.versions || prompt.versions.length === 0) && (
              (() => {
                const hasContent = prompt.content;
                const hasContentZh = prompt.contentzh;
                
                if (hasContent && hasContentZh) {
                  // 两个内容都有，显示"提示词1"和"提示词2"
                  return (
                    <div className="space-y-4">
                      <div className="relative p-5 rounded-xl border-2 border-gray-200 dark:border-slate-600 shadow-inner"
                        style={{
                          background: 'linear-gradient(to bottom right, var(--surface), var(--background))'
                        }}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            提示词1
                          </span>
                          <CopyButton 
                            content={prompt.content || ''} 
                            contentId={`base-content-${prompt.id}`}
                          />
                        </div>
                        <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                          {prompt.content}
                        </pre>
                        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-slate-500 to-transparent" />
                      </div>
                      
                      <div className="relative p-5 rounded-xl border-2 border-gray-200 dark:border-slate-600 shadow-inner"
                        style={{
                          background: 'linear-gradient(to bottom right, var(--surface), var(--background))'
                        }}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            提示词2
                          </span>
                          <CopyButton 
                            content={prompt.contentzh || ''} 
                            contentId={`base-contentzh-${prompt.id}`}
                          />
                        </div>
                        <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                          {prompt.contentzh}
                        </pre>
                        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-slate-500 to-transparent" />
                      </div>
                    </div>
                  );
                } else {
                  // 只有一个内容，显示"提示词"
                  return (
                    <div className="relative p-5 rounded-xl border-2 border-gray-200 dark:border-slate-600 shadow-inner"
                      style={{
                        background: 'linear-gradient(to bottom right, var(--surface), var(--background))'
                      }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          提示词
                        </span>
                        <CopyButton 
                          content={hasContent ? (prompt.content || '') : (prompt.contentzh || '暂无内容')} 
                          contentId={`base-single-${prompt.id}`}
                        />
                      </div>
                      <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono leading-relaxed">
                        {hasContent ? prompt.content : prompt.contentzh || '暂无内容'}
                      </pre>
                      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-slate-500 to-transparent" />
                    </div>
                  );
                }
              })()
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
};
