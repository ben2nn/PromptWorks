import React, { useMemo, useRef, useEffect, useState, useCallback } from 'react';
import { PromptGridProps } from '@/types';
import { PromptCard } from './PromptCard';
import { PerformanceMonitor } from './PerformanceMonitor';
import { ScrollTransition, StaggeredCard, LoadingIndicator, ScrollProgress } from './ScrollTransition';

/**
 * PromptGrid 组件 - 提示词网格布局（虚拟滚动优化 + 无限滚动）
 * 使用自定义虚拟滚动实现，只渲染可见区域的卡片
 * 支持响应式布局，自动计算列数和行数
 * 支持滚动到底部自动加载更多数据
 * 增强的加载和空状态动画
 */
export const PromptGrid: React.FC<PromptGridProps> = ({
  prompts,
  loading,
  onCardClick,
  hasMore,
  onLoadMore
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(800);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [newContentStartIndex, setNewContentStartIndex] = useState(0);




  // 监听容器宽度和高度变化
  useEffect(() => {
    if (!containerRef.current) return;

    const updateDimensions = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth;
        const height = window.innerHeight - 200; // 视口高度减去头部高度
        
        setContainerWidth(width);
        setContainerHeight(height);
      }
    };

    // 使用 setTimeout 确保 DOM 完全渲染后再测量尺寸
    const timer = setTimeout(() => {
      updateDimensions();
    }, 0);

    // 监听窗口大小变化
    const resizeObserver = new ResizeObserver(() => {
      // 添加小延迟确保布局稳定
      setTimeout(updateDimensions, 10);
    });
    
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    window.addEventListener('resize', updateDimensions);

    return () => {
      clearTimeout(timer);
      resizeObserver.disconnect();
      window.removeEventListener('resize', updateDimensions);
    };
  }, []);

  // 简化的滚动事件处理 - 2/3时提前加载
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const { scrollTop, scrollHeight, clientHeight } = target;
    
    setScrollTop(scrollTop);
    
    // 计算滚动进度
    const progress = scrollHeight > clientHeight ? scrollTop / (scrollHeight - clientHeight) : 0;
    setScrollProgress(progress);
    
    // 2/3时提前触发加载 - 约67%时开始加载下一页
    const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
    
    if (scrollPercentage > 0.67 && hasMore && !loading && !isLoadingMore && onLoadMore) {
      setIsLoadingMore(true);
      setNewContentStartIndex(prompts.length);
      onLoadMore();
    }
  }, [hasMore, loading, isLoadingMore, onLoadMore, prompts.length]);

  // 计算网格布局参数
  const gridLayout = useMemo(() => {
    
    const gap = 21; // 卡片间距
    const padding = 30; // 左右内边距
    const availableWidth = containerWidth - padding * 2;

    // 根据容器宽度计算列数（响应式）
    let columnCount = 6; // 默认 xl
    if (containerWidth < 640) columnCount = 2; // sm
    else if (containerWidth < 1024) columnCount = 3; // md
    else if (containerWidth < 1280) columnCount = 4; // lg
    else if (containerWidth < 1536) columnCount = 5; // xl

    // 计算每列宽度（包含间距）
    const columnWidth = (availableWidth + gap) / columnCount;
    
    // 卡片高度 = 宽度（正方形图片）+ 内容高度
    // 内容高度约为：padding(16) + 标题(40) + 标签间距(10) + 标签(28) = 94px
    const cardContentHeight = 94;
    const rowHeight = columnWidth - gap + cardContentHeight;

    // 计算总行数
    const rowCount = Math.ceil(prompts.length / columnCount);

    return {
      columnCount,
      columnWidth,
      rowHeight,
      rowCount,
      gap,
      padding
    };
  }, [containerWidth, prompts.length]);

  // 计算可见的行范围（虚拟滚动核心逻辑）
  const visibleRange = useMemo(() => {
    const overscan = 2; // 上下额外渲染的行数
    const startRow = Math.max(0, Math.floor(scrollTop / gridLayout.rowHeight) - overscan);
    const endRow = Math.min(
      gridLayout.rowCount,
      Math.ceil((scrollTop + containerHeight) / gridLayout.rowHeight) + overscan
    );

    return { startRow, endRow };
  }, [scrollTop, containerHeight, gridLayout.rowHeight, gridLayout.rowCount]);

  // 计算可见的卡片
  const visiblePrompts = useMemo(() => {
    const startIndex = visibleRange.startRow * gridLayout.columnCount;
    const endIndex = visibleRange.endRow * gridLayout.columnCount;
    
    return prompts.slice(startIndex, endIndex).map((prompt, index) => {
      const absoluteIndex = startIndex + index;
      const row = Math.floor(absoluteIndex / gridLayout.columnCount);
      const col = absoluteIndex % gridLayout.columnCount;
      
      return {
        prompt,
        row,
        col,
        index: absoluteIndex,
        isNewContent: absoluteIndex >= newContentStartIndex // 标记是否为新加载的内容
      };
    });
  }, [prompts, visibleRange, gridLayout.columnCount, newContentStartIndex]);

  // 监听加载状态变化，重置加载更多状态
  useEffect(() => {
    if (!loading && isLoadingMore) {
      // 延迟重置状态，让动画有时间播放
      const timer = setTimeout(() => {
        setIsLoadingMore(false);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [loading, isLoadingMore]);

  // 加载状态 - 增强的骨架屏动画（仅在初次加载时显示）
  if (loading && prompts.length === 0) {
    return (
      <ScrollTransition isLoading={true}>
        <div className="
          grid gap-[21px]
          grid-cols-2
          sm:grid-cols-3
          md:grid-cols-4
          lg:grid-cols-5
          xl:grid-cols-6
          px-[30px] py-8
        ">
          {[...Array(18)].map((_, index) => (
            <StaggeredCard
              key={index}
              index={index % 6}
              className="animate-card-stagger"
            >
              {/* 骨架屏卡片 */}
              <div 
                className="rounded-xl shadow-md dark:shadow-slate-900/50 overflow-hidden border border-gray-200 dark:border-slate-700 animate-shimmer"
                style={{ backgroundColor: 'var(--card-bg)' }}
              >
                {/* 图片占位 */}
                <div className="w-full aspect-square bg-gradient-to-br from-gray-200 to-gray-300 dark:from-slate-700 dark:to-slate-600 animate-loading-pulse" />

                {/* 内容占位 */}
                <div className="p-4 space-y-3">
                  {/* 标题占位 */}
                  <div className="space-y-2">
                    <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-3/4 animate-loading-pulse" />
                    <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2 animate-loading-pulse" style={{ animationDelay: '0.1s' }} />
                  </div>

                  {/* 标签占位 */}
                  <div className="flex gap-2">
                    <div className="h-6 bg-gray-200 dark:bg-slate-700 rounded-full w-16 animate-loading-pulse" style={{ animationDelay: '0.2s' }} />
                    <div className="h-6 bg-gray-200 dark:bg-slate-700 rounded-full w-20 animate-loading-pulse" style={{ animationDelay: '0.3s' }} />
                    <div className="h-6 bg-gray-200 dark:bg-slate-700 rounded-full w-12 animate-loading-pulse" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
              </div>
            </StaggeredCard>
          ))}
        </div>
      </ScrollTransition>
    );
  }

  // 空状态 - 增强的视觉效果
  if (!prompts || prompts.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[500px] px-[30px]">
        <div className="text-center max-w-md animate-fade-in">
          {/* 空状态图标 */}
          <div className="relative inline-block mb-6">
            <div className="absolute inset-0 bg-gray-200 dark:bg-slate-700 opacity-30 blur-3xl rounded-full animate-pulse" />
            <svg
              className="relative z-10 mx-auto h-32 w-32 text-gray-300 dark:text-slate-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>

          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            未找到相关提示词
          </h3>
          <p className="text-base text-gray-500 dark:text-gray-400 mb-6">
            尝试调整搜索关键词或筛选条件
          </p>

          {/* 建议列表 */}
          <div 
            className="rounded-lg p-4 text-left border border-gray-200 dark:border-slate-700"
            style={{ backgroundColor: 'var(--surface)' }}
          >
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">搜索建议：</p>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li className="flex items-center gap-2">
                <svg className="w-4 h-4 text-blue-500 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                使用更通用的关键词
              </li>
              <li className="flex items-center gap-2">
                <svg className="w-4 h-4 text-blue-500 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                检查拼写是否正确
              </li>
              <li className="flex items-center gap-2">
                <svg className="w-4 h-4 text-blue-500 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                尝试选择不同的标签
              </li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // 虚拟滚动网格布局
  const totalHeight = gridLayout.rowCount * gridLayout.rowHeight + 64; // 总高度 + 顶部间距



  return (
    <div ref={containerRef} className="w-full relative">
      {/* 滚动进度指示器 */}
      <ScrollProgress 
        scrollProgress={scrollProgress} 
        isVisible={prompts.length > 20} 
      />
      
      {containerWidth > 0 && prompts.length > 0 ? (
        <ScrollTransition isLoading={loading && prompts.length === 0}>
          <div
            ref={scrollContainerRef}
            className="overflow-y-auto overflow-x-hidden ultra-smooth-scroll"
            style={{ height: `${containerHeight}px` }}
            onScroll={handleScroll}
          >
            {/* 占位容器，用于撑开滚动高度 */}
            <div style={{ height: `${totalHeight}px`, position: 'relative' }}>
              {/* 只渲染可见区域的卡片 */}
              {visiblePrompts.map(({ prompt, row, col, index, isNewContent }) => (
                <div
                  key={prompt.id}
                  style={{
                    position: 'absolute',
                    left: `${gridLayout.padding + col * gridLayout.columnWidth}px`,
                    top: `${32 + row * gridLayout.rowHeight}px`,
                    width: `${gridLayout.columnWidth - gridLayout.gap}px`,
                    height: `${gridLayout.rowHeight - gridLayout.gap}px`,
                    zIndex: 1, // 确保卡片在正确的层级
                    pointerEvents: 'auto', // 确保可以接收点击事件
                  }}
                >
                  <StaggeredCard 
                    index={col} 
                    isNewContent={isNewContent}
                    className="h-full"
                  >
                    <PromptCard prompt={prompt} onClick={onCardClick} />
                  </StaggeredCard>
                </div>
              ))}
            </div>
          </div>
          
          {/* 加载更多指示器 */}
          <LoadingIndicator 
            isVisible={loading && prompts.length > 0} 
            text="加载更多内容..."
          />
          
          {/* 没有更多数据提示 */}
          {!hasMore && prompts.length > 0 && (
            <div className="flex justify-center items-center py-8 animate-fade-in">
              <div className="text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-100 dark:bg-slate-800 text-sm text-gray-600 dark:text-gray-400">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  已加载全部 {prompts.length} 个提示词
                </div>
              </div>
            </div>
          )}
          
          {/* 性能监控组件 - 仅在数据量大于50时显示 */}
          {prompts.length > 50 && (
            <PerformanceMonitor
              totalItems={prompts.length}
              visibleItems={visiblePrompts.length}
            />
          )}
        </ScrollTransition>
      ) : prompts.length > 0 ? (
        // 降级方案：使用传统网格布局
        <ScrollTransition isLoading={loading}>
          <div className="
            grid gap-[21px]
            grid-cols-2
            sm:grid-cols-3
            md:grid-cols-4
            lg:grid-cols-5
            xl:grid-cols-6
            px-[30px] py-8
          ">
            {prompts.map((prompt, index) => (
              <StaggeredCard 
                key={prompt.id} 
                index={index % 6}
                className="animate-fade-in"
              >
                <PromptCard prompt={prompt} onClick={onCardClick} />
              </StaggeredCard>
            ))}
          </div>
        </ScrollTransition>
      ) : (
        // 容器尺寸测量中，显示占位
        <div className="flex items-center justify-center min-h-[500px]">
          <div className="text-gray-400 animate-loading-pulse">正在初始化...</div>
        </div>
      )}
    </div>
  );
};
