'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { Theme, ThemeContextValue } from '@/types/theme';

// 创建主题 Context
const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

// localStorage 的 key
const THEME_STORAGE_KEY = 'theme-preference';

// 获取初始主题 - 优化防闪屏
const getInitialTheme = (): Theme => {
  // 服务端渲染时返回默认主题
  if (typeof window === 'undefined') {
    return 'light';
  }

  // 尝试从 localStorage 读取
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') {
      return stored;
    }
  } catch (error) {
    console.warn('无法读取主题偏好设置:', error);
  }

  // 检测系统主题偏好
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }

  return 'light';
};

// 获取当前已应用的主题 - 从 DOM 读取，避免闪屏
const getCurrentTheme = (): Theme => {
  if (typeof window === 'undefined') return 'light';
  
  const currentTheme = document.documentElement.getAttribute('data-theme');
  return (currentTheme === 'dark' || currentTheme === 'light') ? currentTheme : 'light';
};

// ThemeProvider 组件 - 优化防闪屏
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // 从 DOM 读取当前主题，避免状态不一致
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      return getCurrentTheme();
    }
    return 'light';
  });
  const [mounted, setMounted] = useState(false);

  // 初始化主题 - 确保与 DOM 状态同步
  useEffect(() => {
    const currentTheme = getCurrentTheme();
    const preferredTheme = getInitialTheme();
    
    // 如果 DOM 中没有设置主题，使用偏好主题
    const finalTheme = currentTheme !== 'light' ? currentTheme : preferredTheme;
    
    setThemeState(finalTheme);
    setMounted(true);
  }, []);

  // 应用主题到 DOM - 优化过渡效果
  useEffect(() => {
    if (!mounted) return;

    const root = document.documentElement;
    
    // 添加过渡类，确保平滑切换
    root.classList.add('theme-transition');
    
    // 设置主题属性
    root.setAttribute('data-theme', theme);
    
    // 同时添加 class 以支持 Tailwind 的 dark: 变体
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // 持久化到 localStorage
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (error) {
      console.warn('无法保存主题偏好设置:', error);
    }

    // 移除过渡类，避免影响其他动画
    const timer = setTimeout(() => {
      root.classList.remove('theme-transition');
    }, 300);

    return () => clearTimeout(timer);
  }, [theme, mounted]);

  // 切换主题
  const toggleTheme = () => {
    setThemeState(prev => prev === 'light' ? 'dark' : 'light');
  };

  // 设置主题
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const value: ThemeContextValue = {
    theme,
    toggleTheme,
    setTheme,
  };

  // 始终提供 Context，即使在服务端渲染时
  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

// 自定义 Hook 用于访问主题 Context
export function useThemeContext() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useThemeContext 必须在 ThemeProvider 内部使用');
  }
  return context;
}
