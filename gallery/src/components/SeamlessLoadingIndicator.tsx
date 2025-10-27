import React from 'react';

interface SeamlessLoadingIndicatorProps {
  /** 是否正在预加载 */
  preloading?: boolean;
  /** 缓存统计信息 */
  cacheStats?: {
    cachedPages: number;
    totalCached: number;
    hitRate: number;
  };
  /** 是否显示详细信息 */
  showDetails?: boolean;
  /** 位置 */
  position?: 'top' | 'bottom' | 'fixed';
}

/**
 * SeamlessLoadingIndicator 组件 - 无感加载指示器
 * 显示预加载状态和缓存信息，让用户了解系统正在智能工作
 */
export const SeamlessLoadingIndicator: React.FC<SeamlessLoadingIndicatorProps> = ({
  preloading = false,
  cacheStats,
  showDetails = false,
  position = 'bottom'
}) => {
  if (!preloading && !showDetails) return null;

  const positionClasses = {
    top: 'fixed top-4 left-1/2 transform -translate-x-1/2 z-40',
    bottom: 'flex justify-center py-4',
    fixed: 'fixed bottom-4 right-4 z-40'
  };

  return (
    <div className={positionClasses[position]}>
      {preloading && (
        <div className="flex items-center gap-3 px-4 py-2 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm rounded-full shadow-lg border border-gray-200 dark:border-slate-700 animate-fade-in">
          {/* 智能预加载图标 */}
          <div className="relative">
            <svg 
              className="w-4 h-4 text-blue-500 animate-spin" 
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
            
            {/* 智能指示点 */}
            <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          </div>
          
          <span className="text-sm text-gray-700 dark:text-gray-300 font-medium">
            智能预加载中...
          </span>
          
          {/* 进度指示器 */}
          <div className="flex gap-1">
            <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
            <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
            <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
          </div>
        </div>
      )}

      {showDetails && cacheStats && (
        <div className="mt-2 px-3 py-2 bg-gray-50 dark:bg-slate-800 rounded-lg text-xs text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span>缓存: {cacheStats.cachedPages} 页</span>
            </div>
            
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full" />
              <span>命中率: {(cacheStats.hitRate * 100).toFixed(1)}%</span>
            </div>
            
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-purple-500 rounded-full" />
              <span>已缓存: {cacheStats.totalCached} 项</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

interface SmartPreloadBadgeProps {
  /** 预加载状态 */
  status: 'idle' | 'predicting' | 'preloading' | 'cached';
  /** 预加载进度 (0-1) */
  progress?: number;
  /** 点击回调 */
  onClick?: () => void;
}

/**
 * SmartPreloadBadge 组件 - 智能预加载徽章
 * 显示当前预加载状态的小徽章
 */
export const SmartPreloadBadge: React.FC<SmartPreloadBadgeProps> = ({
  status,
  progress = 0,
  onClick
}) => {
  const statusConfig = {
    idle: {
      color: 'bg-gray-500',
      text: '待机',
      icon: '⏸️'
    },
    predicting: {
      color: 'bg-yellow-500',
      text: '预测中',
      icon: '🔮'
    },
    preloading: {
      color: 'bg-blue-500',
      text: '预加载',
      icon: '⚡'
    },
    cached: {
      color: 'bg-green-500',
      text: '已缓存',
      icon: '✅'
    }
  };

  const config = statusConfig[status];

  return (
    <div 
      className={`
        fixed top-20 right-4 z-50
        flex items-center gap-2 px-3 py-1
        ${config.color} text-white text-xs font-medium
        rounded-full shadow-lg
        transition-all duration-300 ease-out
        ${onClick ? 'cursor-pointer hover:scale-105' : ''}
        animate-fade-in
      `}
      onClick={onClick}
      title={`智能预加载状态: ${config.text}`}
    >
      <span>{config.icon}</span>
      <span>{config.text}</span>
      
      {status === 'preloading' && progress > 0 && (
        <div className="w-8 h-1 bg-white/30 rounded-full overflow-hidden">
          <div 
            className="h-full bg-white transition-all duration-300"
            style={{ width: `${progress * 100}%` }}
          />
        </div>
      )}
    </div>
  );
};

interface SeamlessStatusBarProps {
  /** 当前页码 */
  currentPage: number;
  /** 总页数 */
  totalPages?: number;
  /** 预加载状态 */
  preloading: boolean;
  /** 缓存统计 */
  cacheStats: {
    cachedPages: number;
    totalCached: number;
    hitRate: number;
  };
  /** 滚动进度 (0-1) */
  scrollProgress: number;
}

/**
 * SeamlessStatusBar 组件 - 无感滚动状态栏
 * 显示详细的滚动和预加载状态信息
 */
export const SeamlessStatusBar: React.FC<SeamlessStatusBarProps> = ({
  currentPage,
  totalPages,
  preloading,
  cacheStats,
  scrollProgress
}) => {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm border-t border-gray-200 dark:border-slate-700 px-4 py-2 z-40">
      <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
        {/* 左侧：页面信息 */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span>页面:</span>
            <span className="font-mono font-medium text-blue-600 dark:text-blue-400">
              {currentPage}{totalPages ? `/${totalPages}` : ''}
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            <span>进度:</span>
            <div className="w-16 h-1 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${scrollProgress * 100}%` }}
              />
            </div>
            <span className="font-mono text-xs">
              {(scrollProgress * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* 中间：预加载状态 */}
        <div className="flex items-center gap-3">
          {preloading && (
            <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <span>智能预加载</span>
            </div>
          )}
        </div>

        {/* 右侧：缓存信息 */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span>缓存:</span>
            <span className="font-mono font-medium text-green-600 dark:text-green-400">
              {cacheStats.cachedPages}页
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            <span>命中率:</span>
            <span className="font-mono font-medium text-purple-600 dark:text-purple-400">
              {(cacheStats.hitRate * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};