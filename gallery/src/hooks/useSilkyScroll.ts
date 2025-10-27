import { useEffect, useRef, useCallback } from 'react';

interface SilkyScrollOptions {
  /** 滚动阻尼系数 (0-1)，越小越平滑 */
  damping?: number;
  /** 滚动刚度系数 (0-1)，影响响应速度 */
  stiffness?: number;
  /** 是否启用惯性滚动 */
  inertia?: boolean;
  /** 惯性衰减系数 */
  inertiaDecay?: number;
}

/**
 * useSilkyScroll Hook - 超丝滑滚动体验
 * 使用物理引擎模拟自然滚动行为
 */
export const useSilkyScroll = (options: SilkyScrollOptions = {}) => {
  const {
    damping = 0.1,
    stiffness = 0.1,
    inertia = true,
    inertiaDecay = 0.95
  } = options;

  const containerRef = useRef<HTMLElement>(null);
  const animationRef = useRef<number>();
  const velocityRef = useRef(0);
  const targetScrollRef = useRef(0);
  const currentScrollRef = useRef(0);
  const lastTimeRef = useRef(0);
  const isScrollingRef = useRef(false);

  // 平滑滚动动画
  const animate = useCallback((timestamp: number) => {
    if (!containerRef.current) return;

    const deltaTime = timestamp - lastTimeRef.current;
    lastTimeRef.current = timestamp;

    const target = targetScrollRef.current;
    const current = currentScrollRef.current;
    const distance = target - current;

    // 计算弹性力
    const force = distance * stiffness;
    
    // 应用阻尼
    velocityRef.current += force;
    velocityRef.current *= (1 - damping);

    // 更新位置
    currentScrollRef.current += velocityRef.current;

    // 应用滚动
    containerRef.current.scrollTop = currentScrollRef.current;

    // 检查是否需要继续动画
    if (Math.abs(distance) > 0.5 || Math.abs(velocityRef.current) > 0.1) {
      animationRef.current = requestAnimationFrame(animate);
    } else {
      isScrollingRef.current = false;
      currentScrollRef.current = target;
      containerRef.current.scrollTop = target;
    }
  }, [damping, stiffness]);

  // 滚动到指定位置
  const scrollTo = useCallback((position: number, smooth = true) => {
    if (!containerRef.current) return;

    if (!smooth) {
      containerRef.current.scrollTop = position;
      currentScrollRef.current = position;
      targetScrollRef.current = position;
      return;
    }

    targetScrollRef.current = Math.max(0, Math.min(position, 
      containerRef.current.scrollHeight - containerRef.current.clientHeight));

    if (!isScrollingRef.current) {
      isScrollingRef.current = true;
      lastTimeRef.current = performance.now();
      animationRef.current = requestAnimationFrame(animate);
    }
  }, [animate]);

  // 处理滚动事件
  const handleScroll = useCallback((event: Event) => {
    if (!containerRef.current || isScrollingRef.current) return;

    const target = event.target as HTMLElement;
    currentScrollRef.current = target.scrollTop;
    targetScrollRef.current = target.scrollTop;
  }, []);

  // 处理滚轮事件
  const handleWheel = useCallback((event: WheelEvent) => {
    if (!containerRef.current) return;

    event.preventDefault();

    const delta = event.deltaY;
    const newTarget = targetScrollRef.current + delta;
    
    scrollTo(newTarget, true);
  }, [scrollTo]);

  // 处理触摸事件（移动端）
  const touchStartRef = useRef({ y: 0, time: 0 });
  const touchVelocityRef = useRef(0);

  const handleTouchStart = useCallback((event: TouchEvent) => {
    const touch = event.touches[0];
    touchStartRef.current = {
      y: touch.clientY,
      time: Date.now()
    };
    touchVelocityRef.current = 0;
  }, []);

  const handleTouchMove = useCallback((event: TouchEvent) => {
    if (!containerRef.current) return;

    const touch = event.touches[0];
    const deltaY = touchStartRef.current.y - touch.clientY;
    const deltaTime = Date.now() - touchStartRef.current.time;
    
    touchVelocityRef.current = deltaY / deltaTime;
    
    const newTarget = targetScrollRef.current + deltaY;
    scrollTo(newTarget, true);

    touchStartRef.current = {
      y: touch.clientY,
      time: Date.now()
    };
  }, [scrollTo]);

  const handleTouchEnd = useCallback(() => {
    if (!inertia || Math.abs(touchVelocityRef.current) < 0.1) return;

    // 应用惯性滚动
    const applyInertia = () => {
      if (Math.abs(touchVelocityRef.current) < 0.01) return;

      const inertiaDistance = touchVelocityRef.current * 16; // 16ms per frame
      const newTarget = targetScrollRef.current + inertiaDistance;
      
      scrollTo(newTarget, true);
      
      touchVelocityRef.current *= inertiaDecay;
      requestAnimationFrame(applyInertia);
    };

    applyInertia();
  }, [inertia, inertiaDecay, scrollTo]);

  // 绑定事件监听器
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 禁用默认滚动行为
    container.style.scrollBehavior = 'auto';

    // 绑定事件
    container.addEventListener('scroll', handleScroll, { passive: true });
    container.addEventListener('wheel', handleWheel, { passive: false });
    container.addEventListener('touchstart', handleTouchStart, { passive: true });
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    container.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      container.removeEventListener('scroll', handleScroll);
      container.removeEventListener('wheel', handleWheel);
      container.removeEventListener('touchstart', handleTouchStart);
      container.removeEventListener('touchmove', handleTouchMove);
      container.removeEventListener('touchend', handleTouchEnd);

      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [handleScroll, handleWheel, handleTouchStart, handleTouchMove, handleTouchEnd]);

  // 清理动画
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  return {
    containerRef,
    scrollTo,
    isScrolling: isScrollingRef.current
  };
};

/**
 * 预设的丝滑滚动配置
 */
export const silkyScrollPresets = {
  /** 超级平滑 - 最丝滑的体验 */
  ultraSmooth: {
    damping: 0.08,
    stiffness: 0.12,
    inertia: true,
    inertiaDecay: 0.96
  },
  
  /** 自然滚动 - 接近原生的感觉 */
  natural: {
    damping: 0.12,
    stiffness: 0.15,
    inertia: true,
    inertiaDecay: 0.94
  },
  
  /** 快速响应 - 更快的响应速度 */
  responsive: {
    damping: 0.15,
    stiffness: 0.2,
    inertia: false,
    inertiaDecay: 0.9
  },
  
  /** 弹性滚动 - 带有弹性效果 */
  bouncy: {
    damping: 0.06,
    stiffness: 0.08,
    inertia: true,
    inertiaDecay: 0.98
  }
};