import { useState, useEffect, useCallback, useRef } from 'react';
import { Prompt, UsePromptsParams } from '@/types';
import { getPrompts } from '@/lib/api';

interface UsePromptsReturn {
  prompts: Prompt[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  total: number;
  page: number;
  setPage: (page: number) => void;
}

/**
 * usePrompts Hook - 管理提示词数据和状态
 * 负责获取、缓存和管理提示词列表数据
 * 包含搜索防抖功能以优化性能
 */
export const usePrompts = (params: UsePromptsParams = {}): UsePromptsReturn => {
  
  const {
    initialPage = 1,
    limit = 20,  // 每页显示20个
    tags,
    search,
    debounceMs = 300
  } = params;

  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(initialPage);
  
  // 使用 ref 存储防抖定时器和请求控制
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const requestIdRef = useRef<number>(0);
  const isMountedRef = useRef<boolean>(true);

  // 标记组件挂载状态
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // 当依赖变化时重新获取数据（带防抖）
  useEffect(() => {
    
    // 清除之前的定时器
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // 创建新的请求 ID
    const currentRequestId = ++requestIdRef.current;

    const fetchData = async () => {
      if (!isMountedRef.current) return;

      try {
        setLoading(true);
        setError(null);

        const response = await getPrompts({
          page,
          limit,
          tags,
          search
        });

        // 检查是否是最新的请求且组件仍然挂载
        if (currentRequestId !== requestIdRef.current || !isMountedRef.current) {
          return;
        }

        if (response.success) {
          const promptsData = Array.isArray(response.data) ? response.data : [];
          
          // 修复分页逻辑：根据页码决定是追加还是替换数据
          if (page === 1) {
            // 第一页或重新搜索时，替换数据
            setPrompts(promptsData);
          } else {
            // 后续页面，追加数据
            setPrompts(prev => [...prev, ...promptsData]);
          }
          
          setTotal(response.pagination?.total || promptsData.length);
        } else {
          setError(response.message || '获取提示词失败');
          if (page === 1) {
            setPrompts([]);
          }
        }
      } catch (err) {
        if (currentRequestId !== requestIdRef.current || !isMountedRef.current) {
          return;
        }
        
        setError(err instanceof Error ? err.message : '网络请求失败');
        if (page === 1) {
          setPrompts([]);
        }
      } finally {
        if (currentRequestId === requestIdRef.current && isMountedRef.current) {
          setLoading(false);
        }
      }
    };

    // 如果有搜索词，使用防抖
    if (search) {
      debounceTimerRef.current = setTimeout(() => {
        fetchData();
      }, debounceMs);
    } else {
      // 没有搜索词时立即执行
      fetchData();
    }

    // 清理函数
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [page, limit, JSON.stringify(tags), search, debounceMs]);

  // 重新获取数据的方法
  const refetch = useCallback(async () => {
    const currentRequestId = ++requestIdRef.current;
    
    try {
      setLoading(true);
      setError(null);

      const response = await getPrompts({
        page,
        limit,
        tags,
        search
      });

      if (currentRequestId !== requestIdRef.current || !isMountedRef.current) {
        return;
      }

      if (response.success) {
        const promptsData = Array.isArray(response.data) ? response.data : [];
        setPrompts(promptsData);
        setTotal(response.pagination?.total || promptsData.length);
      } else {
        setError(response.message || '获取提示词失败');
        setPrompts([]);
      }
    } catch (err) {
      if (currentRequestId !== requestIdRef.current || !isMountedRef.current) {
        return;
      }
      setError(err instanceof Error ? err.message : '网络请求失败');
      setPrompts([]);
    } finally {
      if (currentRequestId === requestIdRef.current && isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [page, limit, tags, search]);

  return {
    prompts,
    loading,
    error,
    refetch,
    total,
    page,
    setPage
  };
};
