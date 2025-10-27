import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}

/**
 * Modal 组件 - 修复定位问题的优化版本
 * 使用 React Portal 确保弹窗渲染在 body 最外层
 * 避免父容器样式影响弹窗定位
 */
export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  children,
  className = ''
}) => {
  const [mounted, setMounted] = useState(false);

  // 处理挂载状态
  useEffect(() => {
    setMounted(true);
  }, []);

  // ESC 键处理
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  // 优化的滚动锁定 - 锁定内容区域滚动
  useEffect(() => {
    if (isOpen) {
      // 找到滚动容器并锁定其滚动
      const scrollContainer = document.querySelector('.ultra-smooth-scroll') as HTMLElement;
      
      if (scrollContainer) {
        const originalOverflow = scrollContainer.style.overflow;
        scrollContainer.style.overflow = 'hidden';
        
        return () => {
          // 恢复滚动状态
          scrollContainer.style.overflow = originalOverflow;
        };
      }
    }
  }, [isOpen]);
  
  // 如果还没有挂载到 DOM，不渲染
  if (!mounted) return null;

  // 弹窗内容
  const modalContent = (
    <div 
      className={`
        fixed inset-0 z-[99999] 
        flex items-center justify-center 
        p-4 
        transition-all duration-300 ease-out
        ${isOpen ? 'visible opacity-100' : 'invisible opacity-0'}
      `}
      style={{
        // 确保弹窗始终在最顶层，不受其他样式影响
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 99999,
        pointerEvents: isOpen ? 'auto' : 'none'
      }}
    >
      {/* 背景遮罩 - 增强毛玻璃效果 */}
      <div
        className={`
          absolute inset-0 
          bg-gradient-to-br from-black/40 via-black/50 to-black/60
          backdrop-blur-md backdrop-saturate-150 backdrop-brightness-75
          transition-all duration-500 ease-out
          ${isOpen ? 'opacity-100 backdrop-blur-md' : 'opacity-0 backdrop-blur-none'}
        `}
        onClick={onClose}
        aria-hidden="true"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          // 增强毛玻璃效果的 CSS 属性
          backdropFilter: isOpen 
            ? 'blur(12px) saturate(150%) brightness(0.75) contrast(1.1)' 
            : 'blur(0px) saturate(100%) brightness(1) contrast(1)',
          WebkitBackdropFilter: isOpen 
            ? 'blur(12px) saturate(150%) brightness(0.75) contrast(1.1)' 
            : 'blur(0px) saturate(100%) brightness(1) contrast(1)',
          background: isOpen
            ? 'linear-gradient(135deg, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.5) 50%, rgba(0,0,0,0.6) 100%)'
            : 'transparent'
        }}
      />
      
      {/* 弹框内容 - 增强视觉效果 */}
      <div
        className={`
          relative z-10
          w-full max-w-4xl max-h-[90vh] 
          bg-white/95 dark:bg-slate-800/95
          backdrop-blur-xl backdrop-saturate-150
          rounded-2xl 
          shadow-[0_32px_64px_-12px_rgba(0,0,0,0.4)]
          dark:shadow-[0_32px_64px_-12px_rgba(0,0,0,0.8)]
          border border-white/20 dark:border-slate-600/30
          ring-1 ring-black/5 dark:ring-white/10
          overflow-hidden 
          transition-all duration-500 ease-out
          ${isOpen 
            ? 'scale-100 opacity-100 translate-y-0 rotate-0' 
            : 'scale-95 opacity-0 translate-y-8 rotate-1'
          } 
          ${className}
        `}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        style={{
          // 确保内容区域正确定位
          position: 'relative',
          zIndex: 10
        }}
      >
        {children}
      </div>
    </div>
  );

  // 使用 Portal 将弹窗渲染到 body 最外层
  return createPortal(modalContent, document.body);
};
