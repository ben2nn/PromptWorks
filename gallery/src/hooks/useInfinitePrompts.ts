import { useState, useEffect, useCallback, useRef } from 'react';
import { Prompt } from '@/types';
import { getPrompts } from '@/lib/api';

interface UseInfinitePromptsParams {
  pageSize?: number;
  tags?: string[];
  search?: string;
  debounceMs?: number;
}

interface UseInfinitePromptsReturn {
  prompts: Prompt[];
  loading: boolean;
  error: string | null;
  hasMore: boolean;
  loadMore: () => Promise<void>;
  refetch: () => Promise<void>;
  total: number;
}

/**
 * useInfinitePrompts Hook - 无限滚动加载提示词
 * 支持分页加载，滚动到底部时自动加载下一页
 */
export const useInfinitePrompts = (params: UseInfinitePromptsParams = {}): UseInfinitePromptsReturn => {
  
  const {
    pageSize = 20,
    tags,
    search,
    debounceMs = 300
  } = params;

  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [hasMore, setHasMore] = useState<boolean>(true);
  
  // 使用 ref 存储防抖定时器和加载状态
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isLoadingRef = useRef<boolean>(false);
  const isMountedRef = useRef<boolean>(true);

  // 组件挂载标记
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // 获取提示词数据
  const fetchPrompts = useCallback(async (pageNum: number, currentTags?: string[], currentSearch?: string, append: boolean = false) => {
    if (isLoadingRef.current || !isMountedRef.current) return;
    
    try {
      isLoadingRef.current = true;
      setLoading(true);
      setError(null);

      const response = await getPrompts({
        page: pageNum,
        limit: pageSize,
        tags: currentTags,
        search: currentSearch
      });

      if (!isMountedRef.current) return;

      if (response.success) {
        const promptsData = Array.isArray(response.data) ? response.data : [];
        
        // 从 pagination 对象获取总数
        const totalCount = response.pagination?.total || 0;
        setTotal(totalCount);
        
        if (append) {
          setPrompts(prev => {
            const newPrompts = [...prev, ...promptsData];
            setHasMore(newPrompts.length < totalCount);
            return newPrompts;
          });
        } else {
          setPrompts(promptsData);
          setHasMore(promptsData.length < totalCount);
        }
      } else {
        setError(response.message || '获取提示词失败');
        if (!append) {
          setPrompts([]);
        }
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err.message : '网络请求失败');
        if (!append) {
          setPrompts([]);
        }
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
      isLoadingRef.current = false;
    }
  }, [pageSize]);

  // 加载更多数据
  const loadMore = useCallback(async () => {
    if (!hasMore || loading) return;
    
    const nextPage = page + 1;
    setPage(nextPage);
    await fetchPrompts(nextPage, tags, search, true);
  }, [hasMore, loading, page, tags, search, fetchPrompts]);

  // 重新获取数据（重置到第一页）
  const refetch = useCallback(async () => {
    setPage(1);
    setHasMore(true);
    await fetchPrompts(1, tags, search, false);
  }, [tags, search, fetchPrompts]);

  // 当搜索或标签变化时，重置并重新加载
  useEffect(() => {
    
    // 清除之前的定时器
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // 重置状态
    setPage(1);
    setHasMore(true);

    // 如果有搜索词，使用防抖
    if (search) {
      debounceTimerRef.current = setTimeout(() => {
        fetchPrompts(1, tags, search, false);
      }, debounceMs);
    } else {
      // 没有搜索词时立即执行
      fetchPrompts(1, tags, search, false);
    }

    // 清理函数
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [tags?.join(','), search, debounceMs, fetchPrompts]);

  return {
    prompts,
    loading,
    error,
    hasMore,
    loadMore,
    refetch,
    total
  };
};
