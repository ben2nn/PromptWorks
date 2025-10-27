import React, { useEffect, useState } from 'react';

/**
 * 性能监控组件 - 显示渲染的卡片数量
 * 用于验证虚拟滚动是否正常工作
 */
interface PerformanceMonitorProps {
  totalItems: number;
  visibleItems: number;
}

export const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({
  totalItems,
  visibleItems
}) => {
  const [isVisible, setIsVisible] = useState(true);

  // 3秒后自动隐藏
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 animate-fade-in">
      <div 
        className="rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 p-3 backdrop-blur-sm"
        style={{ backgroundColor: 'var(--card-bg)' }}
      >
        <div className="flex items-center gap-2 text-sm">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="font-medium text-gray-700 dark:text-gray-300">
            虚拟滚动已启用
          </span>
        </div>
        <div className="mt-2 text-xs text-gray-600 dark:text-gray-400 space-y-1">
          <div>总数据: <span className="font-semibold text-blue-600 dark:text-blue-400">{totalItems}</span></div>
          <div>渲染中: <span className="font-semibold text-green-600 dark:text-green-400">{visibleItems}</span></div>
          <div className="text-gray-500 dark:text-gray-500">
            性能提升: {Math.round((1 - visibleItems / totalItems) * 100)}%
          </div>
        </div>
        <button
          onClick={() => setIsVisible(false)}
          className="mt-2 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 underline"
        >
          关闭
        </button>
      </div>
    </div>
  );
};
