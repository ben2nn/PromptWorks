import { useState, useEffect, useCallback, useRef } from 'react';
import { Prompt } from '@/types';
import { getPrompts } from '@/lib/api';

interface UseSeamlessInfiniteScrollParams {
  pageSize?: number;
  tags?: string[];
  search?: string;
  debounceMs?: number;
  /** 预加载触发点 (0-1)，0.7 表示滚动到 70% 时开始预加载 */
  preloadThreshold?: number;
  /** 预加载页数，提前加载几页 */
  preloadPages?: number;
  /** 缓存页数，保留多少页的数据 */
  cachePages?: number;
}

interface UseSeamlessInfiniteScrollReturn {
  prompts: Prompt[];
  loading: boolean;
  error: string | null;
  hasMore: boolean;
  loadMore: () => Promise<void>;
  refetch: () => Promise<void>;
  total: number;
  /** 当前页码 */
  currentPage: number;
  /** 预加载状态 */
  preloading: boolean;
  /** 缓存统计 */
  cacheStats: {
    cachedPages: number;
    totalCached: number;
    hitRate: number;
  };
  /** 滚动进度处理函数 */
  handleScrollProgress: (progress: number) => void;
}

/**
 * useSeamlessInfiniteScroll Hook - 无感无限滚动
 * 智能预加载系统，提前加载数据，实现真正的无感翻页体验
 */
export const useSeamlessInfiniteScroll = (
  params: UseSeamlessInfiniteScrollParams = {}
): UseSeamlessInfiniteScrollReturn => {
  const {
    pageSize = 20,
    tags,
    search,
    debounceMs = 300,
    preloadThreshold = 0.7,
    preloadPages = 2,
    cachePages = 5
  } = params;

  // 基础状态
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [preloading, setPreloading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [hasMore, setHasMore] = useState<boolean>(true);

  // 缓存系统
  const cacheRef = useRef<Map<string, Prompt[]>>(new Map());
  const loadingPagesRef = useRef<Set<number>>(new Set());
  const cacheStatsRef = useRef({ hits: 0, misses: 0 });

  // 控制状态
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isLoadingRef = useRef<boolean>(false);
  const isMountedRef = useRef<boolean>(true);
  const preloadQueueRef = useRef<number[]>([]);

  // 组件挂载标记
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // 生成缓存键
  const getCacheKey = useCallback((page: number, currentTags?: string[], currentSearch?: string) => {
    const tagsKey = currentTags?.sort().join(',') || '';
    const searchKey = currentSearch || '';
    return `${page}-${tagsKey}-${searchKey}`;
  }, []);

  // 从缓存获取数据
  const getFromCache = useCallback((page: number, currentTags?: string[], currentSearch?: string) => {
    const key = getCacheKey(page, currentTags, currentSearch);
    const cached = cacheRef.current.get(key);
    if (cached) {
      cacheStatsRef.current.hits++;
      return cached;
    }
    cacheStatsRef.current.misses++;
    return null;
  }, [getCacheKey]);

  // 存储到缓存
  const setToCache = useCallback((page: number, data: Prompt[], currentTags?: string[], currentSearch?: string) => {
    const key = getCacheKey(page, currentTags, currentSearch);
    cacheRef.current.set(key, data);

    // 清理过期缓存
    if (cacheRef.current.size > cachePages * 2) {
      const keys = Array.from(cacheRef.current.keys());
      const keysToDelete = keys.slice(0, keys.length - cachePages);
      keysToDelete.forEach(k => cacheRef.current.delete(k));
    }
  }, [getCacheKey, cachePages]);

  // 获取提示词数据
  const fetchPrompts = useCallback(async (
    pageNum: number, 
    currentTags?: string[], 
    currentSearch?: string, 
    isPreload = false
  ): Promise<Prompt[]> => {
    // 检查缓存
    const cached = getFromCache(pageNum, currentTags, currentSearch);
    if (cached) {
      return cached;
    }

    // 防止重复加载同一页
    if (loadingPagesRef.current.has(pageNum)) {
      return [];
    }

    loadingPagesRef.current.add(pageNum);

    try {
      if (!isPreload) {
        setLoading(true);
      } else {
        setPreloading(true);
      }
      setError(null);

      const response = await getPrompts({
        page: pageNum,
        limit: pageSize,
        tags: currentTags,
        search: currentSearch
      });

      if (!isMountedRef.current) return [];

      if (response.success) {
        const promptsData = Array.isArray(response.data) ? response.data : [];
        
        // 更新总数（只在非预加载时更新）
        if (!isPreload) {
          const totalCount = response.pagination?.total || 0;
          setTotal(totalCount);
          setHasMore(pageNum * pageSize < totalCount);
        }

        // 存储到缓存
        setToCache(pageNum, promptsData, currentTags, currentSearch);
        
        return promptsData;
      } else {
        if (!isPreload) {
          setError(response.message || '获取提示词失败');
        }
        return [];
      }
    } catch (err) {
      if (isMountedRef.current && !isPreload) {
        setError(err instanceof Error ? err.message : '网络请求失败');
      }
      return [];
    } finally {
      loadingPagesRef.current.delete(pageNum);
      if (isMountedRef.current) {
        if (!isPreload) {
          setLoading(false);
        } else {
          setPreloading(false);
        }
      }
    }
  }, [pageSize, getFromCache, setToCache]);

  // 预加载下一页数据
  const preloadNextPages = useCallback(async (fromPage: number, currentTags?: string[], currentSearch?: string) => {
    const pagesToPreload = [];
    for (let i = 1; i <= preloadPages; i++) {
      const nextPage = fromPage + i;
      if (!getFromCache(nextPage, currentTags, currentSearch) && !loadingPagesRef.current.has(nextPage)) {
        pagesToPreload.push(nextPage);
      }
    }

    // 并行预加载
    const preloadPromises = pagesToPreload.map(page => 
      fetchPrompts(page, currentTags, currentSearch, true)
    );

    try {
      await Promise.all(preloadPromises);
    } catch (error) {
      console.warn('预加载失败:', error);
    }
  }, [preloadPages, getFromCache, fetchPrompts]);

  // 加载更多数据（无感版本）
  const loadMore = useCallback(async () => {
    if (!hasMore || isLoadingRef.current) return;

    isLoadingRef.current = true;
    const nextPage = currentPage + 1;

    try {
      // 尝试从缓存获取
      let nextPageData = getFromCache(nextPage, tags, search);
      
      if (!nextPageData) {
        // 缓存未命中，立即加载
        nextPageData = await fetchPrompts(nextPage, tags, search, false);
      }

      if (nextPageData.length > 0) {
        setPrompts(prev => [...prev, ...nextPageData]);
        setCurrentPage(nextPage);
        
        // 启动预加载
        preloadNextPages(nextPage, tags, search);
      }
    } finally {
      isLoadingRef.current = false;
    }
  }, [hasMore, currentPage, tags, search, getFromCache, fetchPrompts, preloadNextPages]);

  // 智能滚动检测和预加载
  const handleScrollProgress = useCallback((progress: number) => {
    // 当滚动到预加载阈值时，开始预加载
    if (progress >= preloadThreshold && hasMore && !preloading) {
      preloadNextPages(currentPage, tags, search);
    }
  }, [preloadThreshold, hasMore, preloading, currentPage, tags, search, preloadNextPages]);

  // 重新获取数据
  const refetch = useCallback(async () => {
    // 清空缓存
    cacheRef.current.clear();
    loadingPagesRef.current.clear();
    cacheStatsRef.current = { hits: 0, misses: 0 };

    setCurrentPage(1);
    setHasMore(true);
    setPrompts([]);

    const firstPageData = await fetchPrompts(1, tags, search, false);
    if (firstPageData.length > 0) {
      setPrompts(firstPageData);
      // 立即预加载后续页面
      preloadNextPages(1, tags, search);
    }
  }, [tags, search, fetchPrompts, preloadNextPages]);

  // 当搜索或标签变化时，重置并重新加载
  useEffect(() => {
    // 清除之前的定时器
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    const resetAndLoad = async () => {
      // 清空缓存
      cacheRef.current.clear();
      loadingPagesRef.current.clear();
      
      setCurrentPage(1);
      setHasMore(true);
      setPrompts([]);

      const firstPageData = await fetchPrompts(1, tags, search, false);
      if (firstPageData.length > 0) {
        setPrompts(firstPageData);
        // 立即预加载
        preloadNextPages(1, tags, search);
      }
    };

    // 如果有搜索词，使用防抖
    if (search) {
      debounceTimerRef.current = setTimeout(resetAndLoad, debounceMs);
    } else {
      resetAndLoad();
    }

    // 清理函数
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [tags?.join(','), search, debounceMs, fetchPrompts, preloadNextPages]);

  // 计算缓存统计
  const cacheStats = {
    cachedPages: cacheRef.current.size,
    totalCached: Array.from(cacheRef.current.values()).reduce((sum, data) => sum + data.length, 0),
    hitRate: cacheStatsRef.current.hits + cacheStatsRef.current.misses > 0 
      ? cacheStatsRef.current.hits / (cacheStatsRef.current.hits + cacheStatsRef.current.misses) 
      : 0
  };

  return {
    prompts,
    loading,
    error,
    hasMore,
    loadMore,
    refetch,
    total,
    currentPage,
    preloading,
    cacheStats,
    handleScrollProgress
  };
};