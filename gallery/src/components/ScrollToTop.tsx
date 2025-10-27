import React, { useState, useEffect } from 'react';

interface ScrollToTopProps {
  threshold?: number;
  className?: string;
}

/**
 * ScrollToTop 组件 - 滚动到顶部按钮
 * 当页面滚动超过阈值时显示，点击平滑滚动到顶部
 * 带有优雅的动画效果
 */
export const ScrollToTop: React.FC<ScrollToTopProps> = ({
  threshold = 400,
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isScrolling, setIsScrolling] = useState(false);

  // 监听滚动事件 - 监听内容容器而不是 window
  useEffect(() => {
    const toggleVisibility = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.scrollTop > threshold) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };

    // 获取滚动容器
    const scrollContainer = document.querySelector('.ultra-smooth-scroll');
    if (scrollContainer) {
      scrollContainer.addEventListener('scroll', toggleVisibility);
      return () => scrollContainer.removeEventListener('scroll', toggleVisibility);
    }
  }, [threshold]);

  // 滚动到顶部 - 滚动内容容器而不是 window
  const scrollToTop = () => {
    setIsScrolling(true);
    
    const scrollContainer = document.querySelector('.ultra-smooth-scroll');
    if (scrollContainer) {
      scrollContainer.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }

    // 滚动完成后重置状态
    setTimeout(() => {
      setIsScrolling(false);
    }, 800);
  };

  if (!isVisible) return null;

  return (
    <button
      onClick={scrollToTop}
      disabled={isScrolling}
      className={`
        fixed bottom-8 right-8 z-50
        w-12 h-12 rounded-full
        bg-white dark:bg-slate-800
        border border-gray-200 dark:border-slate-700
        shadow-lg dark:shadow-slate-900/50
        text-gray-600 dark:text-gray-300
        hover:text-blue-600 dark:hover:text-blue-400
        hover:border-blue-300 dark:hover:border-blue-600
        hover:shadow-xl
        transition-all duration-300 ease-out
        animate-fade-in
        ${isScrolling ? 'animate-smooth-bounce' : 'hover:scale-110'}
        ${className}
      `}
      aria-label="滚动到顶部"
      title="滚动到顶部"
    >
      <svg
        className={`w-6 h-6 mx-auto transition-transform duration-300 ${
          isScrolling ? 'animate-spin' : ''
        }`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 10l7-7m0 0l7 7m-7-7v18"
        />
      </svg>
    </button>
  );
};

interface FloatingActionButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  className?: string;
  disabled?: boolean;
  ariaLabel?: string;
  title?: string;
}

/**
 * FloatingActionButton 组件 - 通用浮动操作按钮
 * 可复用的浮动按钮组件，支持自定义内容和样式
 */
export const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({
  children,
  onClick,
  className = '',
  disabled = false,
  ariaLabel,
  title
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        fixed z-50
        w-14 h-14 rounded-full
        bg-blue-500 hover:bg-blue-600
        dark:bg-blue-600 dark:hover:bg-blue-700
        text-white
        shadow-lg hover:shadow-xl
        transition-all duration-300 ease-out
        hover:scale-110
        disabled:opacity-50 disabled:cursor-not-allowed
        animate-fade-in
        ${className}
      `}
      aria-label={ariaLabel}
      title={title}
    >
      {children}
    </button>
  );
};