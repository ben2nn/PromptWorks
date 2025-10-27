import { useState, useEffect, useCallback } from 'react';
import { Tag } from '@/types';
import { getTags } from '@/lib/api';

interface UseTagsReturn {
  tags: Tag[];
  selectedTag: string;
  setSelectedTag: (tagId: string) => void;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  isTagSelected: (tagId: string) => boolean;
}

/**
 * useTags Hook - 管理标签筛选
 * 负责获取标签列表、管理选中状态和筛选逻辑
 */
export const useTags = (): UseTagsReturn => {
  const [tags, setTags] = useState<Tag[]>([]);
  const [selectedTag, setSelectedTag] = useState<string>('all');
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

        // 添加 "all" 标签到列表开头
        const allTag: Tag = {
          id: 'all',
          name: '全部',
          count: processedTags.reduce((sum, tag) => sum + tag.count, 0)
        };
        setTags([allTag, ...processedTags]);
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
  }, [fetchTags]);

  // 重新获取标签的方法
  const refetch = useCallback(async () => {
    await fetchTags();
  }, [fetchTags]);

  // 检查标签是否被选中
  const isTagSelected = useCallback((tagId: string): boolean => {
    return selectedTag === tagId;
  }, [selectedTag]);

  return {
    tags,
    selectedTag,
    setSelectedTag,
    loading,
    error,
    refetch,
    isTagSelected
  };
};
