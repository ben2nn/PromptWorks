import React from 'react';
import { TagFilterProps } from '@/types';

/**
 * TagFilter 组件 - 标签筛选器
 * 紧凑的横向布局，深色主题
 * 需求: 3.1, 3.2, 3.4
 */
export const TagFilter: React.FC<TagFilterProps> = ({
  tags,
  selectedTags,
  onTagToggle
}) => {
  // 处理标签点击
  const handleTagClick = (tagId: string) => {
    onTagToggle(tagId);
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {tags.map((tag) => {
        const isSelected = selectedTags.has(String(tag.id));

        return (
          <button
            key={String(tag.id)}
            onClick={() => handleTagClick(String(tag.id))}
            className={`
              px-3 py-1.5 rounded-md
              text-xs font-medium
              transition-all duration-200
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
  );
};
