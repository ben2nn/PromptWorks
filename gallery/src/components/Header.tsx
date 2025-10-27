import React from 'react';
import { Input } from './ui/Input';
import { ThemeToggle } from './ThemeToggle';
import { TagFilter } from './TagFilter';
import { HeaderProps } from '@/types';

/**
 * Header 组件 - 页面头部，包含网站标题、搜索框和标签筛选
 * 支持置顶和毛玻璃效果
 * 需求: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4
 */
export const Header: React.FC<HeaderProps> = ({
  onSearch,
  searchQuery,
  tags = [],
  selectedTags = new Set(),
  onTagToggle,
  totalPrompts = 0,
  filteredPrompts = 0,
  onClearFilters
}) => {
  // 处理搜索输入变化
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onSearch) {
      onSearch(e.target.value);
    }
  };

  // 清空搜索
  const handleClearSearch = () => {
    if (onSearch) {
      onSearch('');
    }
  };



  return (
    <header className="header-glass">
      {/* 额外的毛玻璃装饰层 */}
      <div className="
        absolute inset-0 
        bg-gradient-to-b from-white/5 via-transparent to-black/5
        dark:from-white/3 dark:via-transparent dark:to-black/8
        pointer-events-none
      " />
      
      {/* 底部光晕效果 */}
      <div className="
        absolute bottom-0 left-0 right-0 h-px
        bg-gradient-to-r from-transparent via-blue-400/30 to-transparent
        dark:via-blue-300/20
      " />
      
      <div className="px-[30px] py-4 relative z-10">
        {/* 主题切换按钮 - 右上角 */}
        <div className="absolute top-4 right-[30px] z-10">
          <ThemeToggle />
        </div>

        {/* 标题和描述 */}
        <div className="mb-4">
          <h1 className="text-2xl font-bold text-white mb-1">
            提示词图库
          </h1>
          <p className="text-sm text-gray-400">
            浏览、精选和提炼您的提示词库。快速查找示例，探索灵感。
          </p>
        </div>

        {/* 搜索框、清除筛选按钮和统计信息 - 排成一排 */}
        <div className="flex items-center gap-3 mb-4">
          {/* 搜索框 - 缩小宽度和高度 */}
          {onSearch && (
            <div className="relative flex-shrink-0 w-80">
              <Input
                type="text"
                placeholder="搜索提示词..."
                value={searchQuery || ''}
                onChange={handleSearchChange}
                className="!py-2 pr-10 bg-gray-800 border-gray-600 text-white placeholder-gray-400 text-sm h-10"
                icon={
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
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                }
              />

              {/* 清空搜索按钮 */}
              {searchQuery && (
                <button
                  onClick={handleClearSearch}
                  className="
                    absolute right-3 top-1/2 -translate-y-1/2
                    p-1 rounded-full
                    text-gray-400 hover:text-gray-200 hover:bg-gray-700
                    transition-all duration-200 ease-out
                    active:scale-90
                  "
                  aria-label="清空搜索"
                >
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
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}
            </div>
          )}

          {/* 清除标签筛选按钮 - 只在有选中标签时显示 */}
          {selectedTags.size > 0 && (
            <button
              onClick={onClearFilters}
              className="
                flex items-center gap-2 px-3 py-2
                bg-gray-700 hover:bg-gray-600
                text-white text-sm font-medium
                rounded-lg border border-gray-600
                transition-all duration-200 ease-out
                active:scale-95
                flex-shrink-0
              "
              aria-label="清除标签筛选"
            >
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
              <span>清除筛选</span>
            </button>
          )}

          {/* 统计信息 */}
          <div className="flex items-center gap-4 text-sm text-gray-400 ml-auto">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>显示 {filteredPrompts} / {totalPrompts} 个案例</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
              </svg>
              <span>{selectedTags.size} 个标签已选</span>
            </div>
          </div>
        </div>

        {/* 标签筛选器 */}
        {tags.length > 0 && onTagToggle && (
          <div className="mt-3">
            <TagFilter
              tags={tags}
              selectedTags={selectedTags}
              onTagToggle={onTagToggle}
            />
          </div>
        )}
      </div>
    </header>
  );
};
