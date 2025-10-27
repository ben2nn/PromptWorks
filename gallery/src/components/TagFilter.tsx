import React, { useState } from 'react';
import { TagFilterProps } from '@/types';

/**
 * TagFilter 组件 - 标签筛选器
 * 紧凑的横向布局，深色主题，支持展开/收起功能
 * 需求: 3.1, 3.2, 3.4
 */
export const TagFilter: React.FC<TagFilterProps> = ({
  tags,
  selectedTags,
  onTagToggle
}) => {
  // 展开状态管理
  const [isExpanded, setIsExpanded] = useState(false);

  // 处理标签点击
  const handleTagClick = (tagId: string) => {
    onTagToggle(tagId);
  };

  // 切换展开状态
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="relative">
      {/* 标签容器 - 使用固定布局保持标签位置 */}
      <div
        className="transition-all duration-300"
        style={{
          paddingRight: '100px' // 始终为按钮预留空间
        }}
      >
        <div
          className={`
            flex flex-wrap items-center gap-2
            ${!isExpanded ? 'overflow-hidden' : ''}
          `}
          style={{
            maxHeight: !isExpanded ? '40px' : 'none' // 严格限制高度为40px
          }}
        >
          {tags.map((tag) => {
            const isSelected = selectedTags.has(String(tag.id));

            return (
              <button
                key={String(tag.id)}
                onClick={() => handleTagClick(String(tag.id))}
                className={`
                  px-3 py-1.5 rounded-md
                  text-xs font-medium
                  transition-colors duration-200
                  flex-shrink-0
                  h-8
                  ${isSelected
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }
                `}
                type="button"
              >
                {tag.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* 展开/收起按钮 - 绝对定位在右边 */}
      {tags.length > 0 && (
        <button
          onClick={toggleExpanded}
          className="
            absolute right-0 top-0
            px-3 py-1.5 rounded-md
            text-xs font-medium
            bg-gray-600 text-gray-300 hover:bg-gray-500
            transition-all duration-200
            flex items-center gap-1
            flex-shrink-0
            h-8
            z-10
          "
          type="button"
        >
          {isExpanded ? (
            <>
              收起
              <svg className="w-3 h-3 transform rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </>
          ) : (
            <>
              展开
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </>
          )}
        </button>
      )}
    </div>
  );
};
