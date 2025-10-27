import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  error?: string;
}

// Input 组件 - 搜索框样式，增强的视觉效果
export const Input: React.FC<InputProps> = ({
  icon,
  error,
  className = '',
  ...props
}) => {
  return (
    <div className="w-full">
      <div className="relative group">
        {/* 图标容器 */}
        {icon && (
          <div className="
            absolute left-4 top-1/2 -translate-y-1/2
            text-gray-400 dark:text-gray-500 group-focus-within:text-blue-500 dark:group-focus-within:text-blue-400
            transition-colors duration-200
          ">
            {icon}
          </div>
        )}
        
        {/* 输入框 */}
        <input
          className={`
            w-full rounded-xl border-2 border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800
            px-4 py-3 text-base
            text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500
            transition-all duration-200 ease-out
            hover:border-gray-300 dark:hover:border-slate-600 hover:shadow-md dark:hover:shadow-slate-900/50
            focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900/50
            disabled:bg-gray-100 dark:disabled:bg-slate-900 disabled:cursor-not-allowed disabled:hover:border-gray-200 dark:disabled:hover:border-slate-700
            ${icon ? 'pl-11' : ''}
            ${error ? 'border-red-500 dark:border-red-600 focus:border-red-500 dark:focus:border-red-600 focus:ring-red-100 dark:focus:ring-red-900/50' : ''}
            ${className}
          `}
          {...props}
        />
        
        {/* 底部装饰线 - 聚焦时显示 */}
        <div className="
          absolute bottom-0 left-1/2 -translate-x-1/2
          w-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500
          transition-all duration-300 ease-out
          group-focus-within:w-full
        " />
      </div>
      
      {/* 错误提示 */}
      {error && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center gap-1 animate-slide-up">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
};
