import React, { useEffect, useState, useRef } from 'react';

interface PerformanceMetrics {
  fps: number;
  frameTime: number;
  scrollFps: number;
  memoryUsage?: number;
  renderTime: number;
}

interface SilkyPerformanceMonitorProps {
  enabled?: boolean;
  showOverlay?: boolean;
  onPerformanceChange?: (metrics: PerformanceMetrics) => void;
}

/**
 * SilkyPerformanceMonitor 组件 - 丝滑性能监控
 * 实时监控 FPS、滚动性能、内存使用等指标
 * 确保应用保持丝滑的用户体验
 */
export const SilkyPerformanceMonitor: React.FC<SilkyPerformanceMonitorProps> = ({
  enabled = process.env.NODE_ENV === 'development',
  showOverlay = false,
  onPerformanceChange
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    frameTime: 16.67,
    scrollFps: 60,
    renderTime: 0
  });

  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(performance.now());
  const scrollFrameCountRef = useRef(0);
  const lastScrollTimeRef = useRef(performance.now());
  const animationFrameRef = useRef<number>();
  const renderStartRef = useRef(0);

  // FPS 监控
  useEffect(() => {
    if (!enabled) return;

    const measureFPS = () => {
      const now = performance.now();
      frameCountRef.current++;

      // 每秒更新一次 FPS
      if (now - lastTimeRef.current >= 1000) {
        const fps = Math.round((frameCountRef.current * 1000) / (now - lastTimeRef.current));
        const frameTime = (now - lastTimeRef.current) / frameCountRef.current;

        setMetrics(prev => ({
          ...prev,
          fps,
          frameTime
        }));

        frameCountRef.current = 0;
        lastTimeRef.current = now;
      }

      animationFrameRef.current = requestAnimationFrame(measureFPS);
    };

    measureFPS();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [enabled]);

  // 滚动性能监控
  useEffect(() => {
    if (!enabled) return;

    const measureScrollFPS = () => {
      const now = performance.now();
      scrollFrameCountRef.current++;

      if (now - lastScrollTimeRef.current >= 1000) {
        const scrollFps = Math.round((scrollFrameCountRef.current * 1000) / (now - lastScrollTimeRef.current));
        
        setMetrics(prev => ({
          ...prev,
          scrollFps
        }));

        scrollFrameCountRef.current = 0;
        lastScrollTimeRef.current = now;
      }
    };

    const handleScroll = () => {
      measureScrollFPS();
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    document.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
      document.removeEventListener('scroll', handleScroll);
    };
  }, [enabled]);

  // 内存使用监控
  useEffect(() => {
    if (!enabled) return;

    const measureMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const memoryUsage = Math.round(memory.usedJSHeapSize / 1024 / 1024);
        
        setMetrics(prev => ({
          ...prev,
          memoryUsage
        }));
      }
    };

    const interval = setInterval(measureMemory, 2000);
    return () => clearInterval(interval);
  }, [enabled]);

  // 渲染时间监控
  useEffect(() => {
    if (!enabled) return;

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.entryType === 'measure') {
          setMetrics(prev => ({
            ...prev,
            renderTime: entry.duration
          }));
        }
      });
    });

    observer.observe({ entryTypes: ['measure'] });

    return () => observer.disconnect();
  }, [enabled]);

  // 性能变化回调
  useEffect(() => {
    if (onPerformanceChange) {
      onPerformanceChange(metrics);
    }
  }, [metrics, onPerformanceChange]);

  // 性能警告
  useEffect(() => {
    if (!enabled) return;

    const { fps, scrollFps, frameTime } = metrics;
    
    // FPS 过低警告
    if (fps < 30) {
      console.warn('🐌 FPS 过低:', fps, '建议优化渲染性能');
    }
    
    // 滚动 FPS 过低警告
    if (scrollFps < 30) {
      console.warn('🐌 滚动 FPS 过低:', scrollFps, '建议优化滚动性能');
    }
    
    // 帧时间过长警告
    if (frameTime > 33.33) {
      console.warn('🐌 帧时间过长:', frameTime.toFixed(2), 'ms');
    }
  }, [metrics, enabled]);

  if (!enabled || !showOverlay) return null;

  const getPerformanceColor = (value: number, thresholds: [number, number]) => {
    if (value >= thresholds[1]) return 'text-green-500';
    if (value >= thresholds[0]) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="fixed top-4 right-4 z-50 bg-black/80 text-white p-3 rounded-lg text-xs font-mono backdrop-blur-sm">
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span>FPS:</span>
          <span className={getPerformanceColor(metrics.fps, [30, 50])}>
            {metrics.fps}
          </span>
        </div>
        
        <div className="flex justify-between gap-4">
          <span>Frame:</span>
          <span className={getPerformanceColor(33.33 - metrics.frameTime, [16.67, 25])}>
            {metrics.frameTime.toFixed(1)}ms
          </span>
        </div>
        
        <div className="flex justify-between gap-4">
          <span>Scroll:</span>
          <span className={getPerformanceColor(metrics.scrollFps, [30, 50])}>
            {metrics.scrollFps}
          </span>
        </div>
        
        {metrics.memoryUsage && (
          <div className="flex justify-between gap-4">
            <span>Memory:</span>
            <span className={getPerformanceColor(100 - metrics.memoryUsage, [50, 80])}>
              {metrics.memoryUsage}MB
            </span>
          </div>
        )}
        
        {metrics.renderTime > 0 && (
          <div className="flex justify-between gap-4">
            <span>Render:</span>
            <span className={getPerformanceColor(50 - metrics.renderTime, [16, 33])}>
              {metrics.renderTime.toFixed(1)}ms
            </span>
          </div>
        )}
      </div>
      
      {/* 性能状态指示器 */}
      <div className="mt-2 flex items-center gap-2">
        <div 
          className={`w-2 h-2 rounded-full ${
            metrics.fps >= 50 && metrics.scrollFps >= 50 
              ? 'bg-green-500' 
              : metrics.fps >= 30 && metrics.scrollFps >= 30
              ? 'bg-yellow-500'
              : 'bg-red-500'
          }`}
        />
        <span className="text-xs">
          {metrics.fps >= 50 && metrics.scrollFps >= 50 
            ? '丝滑' 
            : metrics.fps >= 30 && metrics.scrollFps >= 30
            ? '良好'
            : '卡顿'
          }
        </span>
      </div>
    </div>
  );
};

/**
 * 性能优化建议 Hook
 */
export const usePerformanceOptimization = () => {
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const analyzePerfomance = (metrics: PerformanceMetrics) => {
    const newSuggestions: string[] = [];

    if (metrics.fps < 30) {
      newSuggestions.push('减少 DOM 操作和重绘');
      newSuggestions.push('使用 CSS transform 代替改变 layout 属性');
      newSuggestions.push('启用硬件加速 (transform: translateZ(0))');
    }

    if (metrics.scrollFps < 30) {
      newSuggestions.push('优化滚动事件处理');
      newSuggestions.push('使用 passive 事件监听器');
      newSuggestions.push('减少滚动时的计算量');
    }

    if (metrics.frameTime > 33.33) {
      newSuggestions.push('分解长时间运行的任务');
      newSuggestions.push('使用 requestIdleCallback');
      newSuggestions.push('优化 React 组件渲染');
    }

    if (metrics.memoryUsage && metrics.memoryUsage > 100) {
      newSuggestions.push('检查内存泄漏');
      newSuggestions.push('清理未使用的事件监听器');
      newSuggestions.push('优化图片和资源加载');
    }

    setSuggestions(newSuggestions);
  };

  return { suggestions, analyzePerfomance };
};