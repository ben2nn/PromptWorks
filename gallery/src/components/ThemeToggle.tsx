'use client';

import React from 'react';
import { useThemeContext } from '@/contexts/ThemeContext';

/**
 * ThemeToggle 组件 - 主题切换按钮
 * 
 * 功能：
 * - 在浅色模式显示太阳图标
 * - 在深色模式显示月亮图标
 * - 提供悬停和点击动画效果
 * - 支持键盘操作和无障碍访问
 * 
 * 需求: 2.1, 2.2, 2.3, 2.5
 */
export interface ThemeToggleProps {
  className?: string;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ className = '' }) => {
  const { theme, toggleTheme } = useThemeContext();

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleTheme();
    }
  };

  // 根据当前主题生成 aria-label
  const ariaLabel = theme === 'light' 
    ? '切换到深色模式' 
    : '切换到浅色模式';

  return (
    <button
      onClick={toggleTheme}
      onKeyDown={handleKeyDown}
      className={`
        relative
        p-2 rounded-lg
        text-gray-700 dark:text-gray-200
        hover:text-gray-900 dark:hover:text-white
        transition-all duration-300 ease-out
        hover:scale-110 active:scale-95
        focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:ring-offset-2
        dark:focus:ring-blue-400/50 dark:focus:ring-offset-2
        dark:focus:ring-offset-transparent
        ${className}
      `}
      aria-label={ariaLabel}
      aria-pressed={theme === 'dark'}
      aria-live="polite"
      title={ariaLabel}
      type="button"
      role="switch"
      aria-checked={theme === 'dark'}
    >
      {/* 太阳图标 - 浅色模式 */}
      <svg
        className={`
          w-5 h-5 no-transition
          ${theme === 'light' 
            ? 'opacity-100 rotate-0 scale-100' 
            : 'opacity-0 rotate-90 scale-0 absolute inset-0 m-auto'
          }
        `}
        style={{
          transition: 'opacity 500ms ease-out, transform 500ms ease-out'
        }}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
        />
      </svg>

      {/* 月亮图标 - 深色模式 */}
      <svg
        className={`
          w-5 h-5 no-transition
          ${theme === 'dark' 
            ? 'opacity-100 rotate-0 scale-100' 
            : 'opacity-0 -rotate-90 scale-0 absolute inset-0 m-auto'
          }
        `}
        style={{
          transition: 'opacity 500ms ease-out, transform 500ms ease-out'
        }}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
        />
      </svg>
    </button>
  );
};
