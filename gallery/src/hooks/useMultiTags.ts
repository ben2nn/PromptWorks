import { useState, useEffect, useCallback } from 'react';
import { Tag } from '@/types';
import { getTags } from '@/lib/api';

interface UseMultiTagsReturn {
  tags: Tag[];
  selectedTags: Set<string>;
  toggleTag: (tagId: string) => void;
  clearTags: () => void;
  selectAllTags: () => void;
  isTagSelected: (tagId: string) => boolean;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * useMultiTags Hook - 管理多选标签筛选
 * 负责获取标签列表、管理多选状态和筛选逻辑
 * 
 * 功能特性:
 * - 使用 Set 数据结构管理选中状态，提供 O(1) 查找性能
 * - 实现"全部"标签与其他标签的互斥逻辑
 * - 支持标签切换（toggleTag）和清空（clearTags）操作
 * - 自动处理空状态（无标签选中时自动选中"全部"）
 * 
 * 需求: 3.1, 3.5
 */
export const useMultiTags = (): UseMultiTagsReturn => {
  const [tags, setTags] = useState<Tag[]>([]);
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 获取标签列表
  const fetchTags = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await getTags();

      if (response.success) {
        // 处理后端返回的标签数据，统一字段名
        const processedTags = response.data.items.map(tag => ({
          ...tag,
          count: tag.prompt_count || tag.count || 0  // 兼容 prompt_count 和 count
        }));

        setTags(processedTags);
      } else {
        setError(response.message || '获取标签失败');
        setTags([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络请求失败');
      setTags([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // 初始化时获取标签
  useEffect(() => {
    fetchTags();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 只在组件挂载时执行一次

  /**
   * 切换标签选中状态
   * 支持多选标签
   */
  const toggleTag = useCallback((tagId: string) => {
    setSelectedTags(prevSelected => {
      const newSelected = new Set(prevSelected);
      
      if (newSelected.has(tagId)) {
        // 如果标签已选中，取消选中
        newSelected.delete(tagId);
      } else {
        // 如果标签未选中，添加到选中集合
        newSelected.add(tagId);
      }
      
      return newSelected;
    });
  }, []);

  /**
   * 清空所有标签选择
   */
  const clearTags = useCallback(() => {
    setSelectedTags(new Set());
  }, []);

  /**
   * 选中所有标签
   */
  const selectAllTags = useCallback(() => {
    setSelectedTags(new Set());
  }, []);

  /**
   * 检查标签是否被选中
   */
  const isTagSelected = useCallback((tagId: string): boolean => {
    return selectedTags.has(tagId);
  }, [selectedTags]);

  /**
   * 重新获取标签列表
   */
  const refetch = useCallback(async () => {
    await fetchTags();
  }, [fetchTags]);

  return {
    tags,
    selectedTags,
    toggleTag,
    clearTags,
    selectAllTags,
    isTagSelected,
    loading,
    error,
    refetch
  };
};
