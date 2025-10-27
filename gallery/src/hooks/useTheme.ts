'use client';

import { useThemeContext } from '@/contexts/ThemeContext';

/**
 * 主题 Hook - 封装主题逻辑
 * 
 * 提供主题状态和切换功能，包括 localStorage 持久化
 * 
 * @returns {ThemeContextValue} 主题状态和操作方法
 * 
 * @example
 * ```tsx
 * const { theme, toggleTheme, setTheme } = useTheme();
 * 
 * // 切换主题
 * <button onClick={toggleTheme}>切换主题</button>
 * 
 * // 设置特定主题
 * <button onClick={() => setTheme('dark')}>深色模式</button>
 * ```
 */
export function useTheme() {
  return useThemeContext();
}
