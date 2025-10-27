import React, { useEffect, useRef, useState } from 'react';

interface ScrollTransitionProps {
  children: React.ReactNode;
  isLoading?: boolean;
  className?: string;
}

/**
 * ScrollTransition 组件 - 滚动翻页动画过渡
 * 为新加载的内容提供平滑的进入动画
 * 支持交错动画效果，让卡片依次出现
 */
export const ScrollTransition: React.FC<ScrollTransitionProps> = ({
  children,
  isLoading = false,
  className = ''
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [animationKey, setAnimationKey] = useState(0);

  // 当内容变化时触发动画
  useEffect(() => {
    if (!isLoading && children) {
      setAnimationKey(prev => prev + 1);
      setIsVisible(true);
      
      // 重置动画状态
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, 600); // 动画持续时间

      return () => clearTimeout(timer);
    }
  }, [children, isLoading]);

  return (
    <div
      ref={containerRef}
      key={animationKey}
      className={`
        ${className}
        ${isVisible ? 'animate-page-slide-in' : ''}
        transition-smooth
      `}
    >
      {children}
    </div>
  );
};

interface StaggeredCardProps {
  children: React.ReactNode;
  index: number;
  isNewContent?: boolean;
  className?: string;
}

/**
 * StaggeredCard 组件 - 交错动画卡片
 * 为新加载的卡片提供交错进入动画
 */
export const StaggeredCard: React.FC<StaggeredCardProps> = ({
  children,
  index,
  isNewContent = false,
  className = ''
}) => {
  const staggerClass = `stagger-${Math.min(index % 6 + 1, 6)}`;
  
  return (
    <div
      className={`
        ${className}
        transition-smooth
        ${isNewContent ? `animate-card-stagger ${staggerClass}` : 'animate-fade-in'}
      `}
    >
      {children}
    </div>
  );
};

interface LoadingIndicatorProps {
  isVisible: boolean;
  text?: string;
}

/**
 * LoadingIndicator 组件 - 加载指示器
 * 显示加载状态的动画指示器
 */
export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  isVisible,
  text = '加载更多...'
}) => {
  if (!isVisible) return null;

  return (
    <div className="flex justify-center items-center py-8 animate-fade-in">
      <div className="flex items-center gap-3 text-gray-600 dark:text-gray-400">
        {/* 旋转加载图标 */}
        <div className="relative">
          <svg 
            className="animate-spin h-5 w-5" 
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24"
          >
            <circle 
              className="opacity-25" 
              cx="12" 
              cy="12" 
              r="10" 
              stroke="currentColor" 
              strokeWidth="4"
            />
            <path 
              className="opacity-75" 
              fill="currentColor" 
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
        
        {/* 加载文本 */}
        <span className="text-sm animate-loading-pulse">{text}</span>
        
        {/* 跳动的点 */}
        <div className="flex gap-1">
          <div className="w-1 h-1 bg-current rounded-full animate-smooth-bounce" style={{ animationDelay: '0s' }} />
          <div className="w-1 h-1 bg-current rounded-full animate-smooth-bounce" style={{ animationDelay: '0.2s' }} />
          <div className="w-1 h-1 bg-current rounded-full animate-smooth-bounce" style={{ animationDelay: '0.4s' }} />
        </div>
      </div>
    </div>
  );
};

interface ScrollProgressProps {
  scrollProgress: number;
  isVisible?: boolean;
}

/**
 * ScrollProgress 组件 - 滚动进度指示器
 * 显示当前滚动进度的可视化指示器
 */
export const ScrollProgress: React.FC<ScrollProgressProps> = ({
  scrollProgress,
  isVisible = true
}) => {
  if (!isVisible) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 h-1 bg-gray-200 dark:bg-slate-700">
      <div
        className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300 ease-out"
        style={{ width: `${Math.min(scrollProgress * 100, 100)}%` }}
      />
    </div>
  );
};