'use client';

import React, { useEffect, useState } from 'react';

interface NoFlashProviderProps {
  children: React.ReactNode;
}

/**
 * NoFlashProvider 组件 - 防闪屏提供者
 * 确保页面加载时不会出现白屏闪烁
 * 管理主题状态的持久化和平滑切换
 */
export const NoFlashProvider: React.FC<NoFlashProviderProps> = ({ children }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [themeInitialized, setThemeInitialized] = useState(false);

  // 初始化主题，防止闪屏
  useEffect(() => {
    const initializeTheme = () => {
      try {
        // 从 localStorage 获取保存的主题
        const savedTheme = localStorage.getItem('theme');
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        const theme = savedTheme || systemTheme;

        // 立即应用主题，防止闪屏
        document.documentElement.setAttribute('data-theme', theme);
        if (theme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }

        setThemeInitialized(true);
      } catch (error) {
        console.warn('主题初始化失败:', error);
        setThemeInitialized(true);
      }
    };

    // 立即执行主题初始化
    initializeTheme();
  }, []);

  // 页面加载完成处理
  useEffect(() => {
    if (!themeInitialized) return;

    const handleLoad = () => {
      // 移除加载状态
      document.documentElement.classList.remove('loading');
      document.documentElement.classList.add('loaded');
      
      // 安全地处理 body 元素
      if (document.body) {
        document.body.classList.remove('loading');
        document.body.classList.add('loaded');
      }
      
      setIsLoaded(true);
    };

    // 检查页面是否已经加载完成
    if (document.readyState === 'complete') {
      handleLoad();
    } else {
      window.addEventListener('load', handleLoad);
      // 备用方案：如果 load 事件没有触发，使用 DOMContentLoaded
      document.addEventListener('DOMContentLoaded', handleLoad);
    }

    return () => {
      window.removeEventListener('load', handleLoad);
      document.removeEventListener('DOMContentLoaded', handleLoad);
    };
  }, [themeInitialized]);

  // 监听系统主题变化
  useEffect(() => {
    if (!themeInitialized) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleThemeChange = (e: MediaQueryListEvent) => {
      const savedTheme = localStorage.getItem('theme');
      // 只有在用户没有手动设置主题时才跟随系统主题
      if (!savedTheme) {
        const newTheme = e.matches ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        if (newTheme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
    };

    mediaQuery.addEventListener('change', handleThemeChange);
    return () => mediaQuery.removeEventListener('change', handleThemeChange);
  }, [themeInitialized]);

  // 在主题初始化之前不渲染内容，防止闪屏
  if (!themeInitialized) {
    return (
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'var(--background, #ffffff)',
          zIndex: 9999,
        }}
      />
    );
  }

  return (
    <div className={`prevent-flash ${isLoaded ? 'loaded' : 'preload'}`}>
      {children}
    </div>
  );
};

/**
 * 防闪屏脚本 - 在页面加载前立即执行
 * 这个脚本应该内联在 HTML 的 <head> 中
 */
export const noFlashScript = `
(function() {
  try {
    // 立即设置加载状态到 documentElement（html 元素）
    document.documentElement.classList.add('loading');
    
    // 安全地设置 body 的加载状态（如果 body 存在的话）
    if (document.body) {
      document.body.classList.add('loading');
    } else {
      // 如果 body 还不存在，等待 DOM 加载后再设置
      document.addEventListener('DOMContentLoaded', function() {
        if (document.body) {
          document.body.classList.add('loading');
        }
      });
    }
    
    // 获取保存的主题或使用系统主题
    var savedTheme = localStorage.getItem('theme');
    var systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    var theme = savedTheme || systemTheme;
    
    // 立即应用主题
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    }
    
    // 设置基础样式变量
    var root = document.documentElement;
    if (theme === 'dark') {
      root.style.setProperty('--background', '#0f172a');
      root.style.setProperty('--foreground', '#f1f5f9');
    } else {
      root.style.setProperty('--background', '#ffffff');
      root.style.setProperty('--foreground', '#111827');
    }
  } catch (e) {
    console.warn('防闪屏脚本执行失败:', e);
  }
})();
`;

/**
 * ThemeScript 组件 - 内联主题脚本
 * 用于在页面加载前立即设置主题，防止闪屏
 */
export const ThemeScript: React.FC = () => {
  return (
    <script
      dangerouslySetInnerHTML={{
        __html: noFlashScript,
      }}
    />
  );
};