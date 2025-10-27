import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

// Button 组件 - 支持不同样式和状态，增强的点击反馈动画
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  className = '',
  children,
  disabled,
  ...props
}) => {
  // 基础样式 - 添加点击动画
  const baseStyles = `
    inline-flex items-center justify-center rounded-lg font-medium
    transition-all duration-200 ease-out
    focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-900
    active:scale-95 active:shadow-sm
    transform
  `;
  
  // 变体样式 - 优化颜色和悬停效果
  const variantStyles = {
    primary: `
      bg-blue-600 text-white shadow-md
      hover:bg-blue-700 hover:shadow-lg hover:-translate-y-0.5
      focus:ring-blue-500 dark:focus:ring-blue-400
      disabled:bg-blue-300 disabled:shadow-none disabled:transform-none
    `,
    secondary: `
      bg-gray-600 dark:bg-slate-700 text-white shadow-md
      hover:bg-gray-700 dark:hover:bg-slate-600 hover:shadow-lg hover:-translate-y-0.5
      focus:ring-gray-500 dark:focus:ring-slate-400
      disabled:bg-gray-300 dark:disabled:bg-slate-600 disabled:shadow-none disabled:transform-none
    `,
    outline: `
      border-2 border-blue-600 dark:border-blue-500 text-blue-600 dark:text-blue-400 bg-white dark:bg-slate-800
      hover:bg-blue-50 dark:hover:bg-slate-700 hover:border-blue-700 dark:hover:border-blue-400 hover:shadow-md hover:-translate-y-0.5
      focus:ring-blue-500 dark:focus:ring-blue-400
      disabled:border-blue-300 dark:disabled:border-blue-700 disabled:text-blue-300 dark:disabled:text-blue-700 disabled:transform-none
    `,
    ghost: `
      text-gray-700 dark:text-gray-300 bg-transparent
      hover:bg-gray-100 dark:hover:bg-slate-700 hover:shadow-sm
      focus:ring-gray-500 dark:focus:ring-slate-400
      disabled:text-gray-300 dark:disabled:text-gray-600 disabled:transform-none
    `
  };
  
  // 尺寸样式
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-base gap-2',
    lg: 'px-6 py-3 text-lg gap-2.5'
  };
  
  // 禁用状态样式
  const disabledStyles = disabled 
    ? 'cursor-not-allowed opacity-60' 
    : 'cursor-pointer';
  
  const combinedClassName = `
    ${baseStyles}
    ${variantStyles[variant]}
    ${sizeStyles[size]}
    ${disabledStyles}
    ${className}
  `.trim().replace(/\s+/g, ' ');
  
  return (
    <button
      className={combinedClassName}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
