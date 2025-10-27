import { useState, useCallback, useEffect, useRef } from 'react';
import { Prompt } from '@/types';
import { searchPrompts } from '@/lib/api';

interface UseSearchReturn {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  searchResults: Prompt[];
  isSearching: boolean;
  searchError: string | null;
  clearSearch: () => void;
}

interface UseSearchParams {
  debounceMs?: number;
  minQueryLength?: number;
  limit?: number;
}

/**
 * useSearch Hook - 管理搜索功能
 * 提供防抖搜索、搜索状态管理和结果处理
 */
export const useSearch = (params: UseSearchParams = {}): UseSearchReturn => {
  const {
    debounceMs = 300,
    minQueryLength = 2,
    limit = 10000
  } = params;

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Prompt[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  
  // 使用 ref 存储定时器 ID
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 执行搜索的函数
  const performSearch = useCallback(async (query: string) => {
    if (!query || query.length < minQueryLength) {
      setSearchResults([]);
      setSearchError(null);
      return;
    }

    try {
      setIsSearching(true);
      setSearchError(null);

      const response = await searchPrompts(query, limit);

      if (response.success) {
        setSearchResults(response.data);
      } else {
        setSearchError(response.message || '搜索失败');
        setSearchResults([]);
      }
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : '搜索请求失败');
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [minQueryLength, limit]);

  // 防抖搜索效果
  useEffect(() => {
    // 清除之前的定时器
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // 如果搜索词为空，立即清空结果
    if (!searchQuery) {
      setSearchResults([]);
      setSearchError(null);
      setIsSearching(false);
      return;
    }

    // 设置新的防抖定时器
    debounceTimerRef.current = setTimeout(() => {
      performSearch(searchQuery);
    }, debounceMs);

    // 清理函数
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchQuery, debounceMs, performSearch]);

  // 清空搜索
  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setSearchResults([]);
    setSearchError(null);
    setIsSearching(false);
  }, []);

  return {
    searchQuery,
    setSearchQuery,
    searchResults,
    isSearching,
    searchError,
    clearSearch
  };
};
