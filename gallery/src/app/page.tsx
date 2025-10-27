'use client';

import { useState, useMemo, useEffect } from 'react';
import { Header } from '@/components/Header';
import { PromptGrid } from '@/components/PromptGrid';
import { PromptModal } from '@/components/PromptModal';
import { ScrollToTop } from '@/components/ScrollToTop';

import { useInfinitePrompts } from '@/hooks/useInfinitePrompts';

import { useMultiTags } from '@/hooks/useMultiTags';
import { Prompt } from '@/types';

/**
 * 主页面组件
 * 集成 Header、TagFilter、PromptGrid 和 PromptModal 组件
 * 管理搜索、筛选和详情展示的数据流
 * 支持多选标签筛选功能
 * 支持无限滚动分页加载（每页20个）
 * 增强的页面过渡效果和视觉反馈
 * 需求: 1.1, 1.4, 2.1, 2.2, 3.2, 3.4, 4.1, 4.2, 4.3
 */
export default function Home() {
  // 搜索状态
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  // 选中的提示词（用于详情弹框）
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  
  // 使用多选标签 Hook 获取标签数据和状态
  const {
    tags,
    selectedTags,
    toggleTag,
    loading: tagsLoading
  } = useMultiTags();
  
  // 将选中的标签转换为数组（用于API请求）
  // 使用稳定的字符串作为依赖，避免 Set 引用变化导致重复渲染
  const selectedTagsString = Array.from(selectedTags).sort().join(',');
  const selectedTagsArray = useMemo(() => {
    return Array.from(selectedTags);
  }, [selectedTagsString]);

  // 使用简化的无限滚动 Hook 获取提示词数据
  const {
    prompts,
    loading: promptsLoading,
    error: promptsError,
    total,
    hasMore,
    loadMore
  } = useInfinitePrompts({
    pageSize: 30, // 每页30个提示词
    tags: selectedTagsArray.length > 0 ? selectedTagsArray : undefined,
    search: searchQuery || undefined
  });



  // 处理搜索输入
  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  // 处理标签切换（多选）
  const handleTagToggle = (tagId: string) => {
    toggleTag(tagId);
  };

  // 清除标签筛选
  const handleClearFilters = () => {
    // 清除所有选中的标签
    selectedTags.forEach(tagId => toggleTag(tagId));
  };

  // 处理卡片点击，打开详情弹框
  const handleCardClick = (prompt: Prompt) => {
    setSelectedPrompt(prompt);
  };

  // 关闭详情弹框
  const handleCloseModal = () => {
    setSelectedPrompt(null);
  };

  // 处理加载更多
  const handleLoadMore = () => {
    if (!promptsLoading && hasMore) {
      loadMore();
    }
  };

  // 计算加载状态（仅首次加载显示骨架屏）
  const isInitialLoading = promptsLoading;

  // 滚动监听 - 监听内部容器的滚动
  useEffect(() => {
    const handleScroll = (e: Event) => {
      const target = e.target as HTMLElement;
      const { scrollTop, scrollHeight, clientHeight } = target;
      const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
      
      if (scrollPercentage > 0.9 && hasMore && !promptsLoading) {
        handleLoadMore();
      }
    };

    // 获取滚动容器
    const scrollContainer = document.querySelector('.ultra-smooth-scroll');
    if (scrollContainer) {
      scrollContainer.addEventListener('scroll', handleScroll);
      return () => scrollContainer.removeEventListener('scroll', handleScroll);
    }
  }, [hasMore, promptsLoading, handleLoadMore]);

  return (
    <main className="h-screen overflow-hidden">
      {/* 详情弹框 - 提升到最外层，避免定位问题 */}
      <PromptModal
        prompt={selectedPrompt}
        isOpen={!!selectedPrompt}
        onClose={handleCloseModal}
      />

      {/* 主要内容区域 - 设置为满窗口高度并启用滚动 */}
      <div 
        className="h-screen overflow-y-auto ultra-smooth-scroll prevent-flash transition-smooth"
        style={{ 
          background: 'linear-gradient(to bottom, var(--surface), var(--background))' 
        }}
      >
        {/* 头部：标题、搜索框和标签筛选器 */}
        <Header 
          onSearch={handleSearch}
          searchQuery={searchQuery}
          tags={tags}
          selectedTags={selectedTags}
          onTagToggle={handleTagToggle}
          totalPrompts={total}
          filteredPrompts={prompts.length}
          onClearFilters={handleClearFilters}
        />

        {/* 主内容区域 */}
        <div className="relative">
          {/* 错误状态显示 */}
          {promptsError && (
            <div className="px-[30px]">
              <div className="mt-8 p-5 bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-xl shadow-md animate-slide-down">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <svg
                      className="w-6 h-6 text-red-600 dark:text-red-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-red-900 dark:text-red-100 mb-1">加载失败</h3>
                    <p className="text-sm text-red-700 dark:text-red-300">{promptsError}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 提示词网格（简化版无限滚动） */}
          <PromptGrid
            prompts={prompts}
            loading={isInitialLoading}
            onCardClick={handleCardClick}
            hasMore={hasMore}
            onLoadMore={handleLoadMore}
          />
        </div>

        {/* 页面底部装饰 */}
        <footer 
          className="mt-16 py-8 border-t border-gray-200 dark:border-slate-700 animate-fade-in"
          style={{ backgroundColor: 'var(--card-bg)' }}
        >
          <div className="px-[30px] text-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              探索更多优质 AI 提示词，激发创意灵感
            </p>
          </div>
        </footer>

        {/* 滚动到顶部按钮 */}
        <ScrollToTop threshold={300} />
      </div>
    </main>
  );
}
