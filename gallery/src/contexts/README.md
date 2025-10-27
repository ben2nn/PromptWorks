# Contexts 目录

本目录包含 React Context 提供者，用于管理全局状态。

## ThemeContext

主题 Context 提供全局的主题管理功能，支持浅色和深色模式切换。

### 功能特性

- ✅ 浅色/深色模式切换
- ✅ localStorage 持久化
- ✅ 系统主题偏好检测
- ✅ 服务端渲染支持（避免闪烁）
- ✅ TypeScript 类型安全

### 使用方法

#### 1. 在根布局中集成 ThemeProvider

```tsx
// app/layout.tsx
import { ThemeProvider } from '@/contexts/ThemeContext';

export default function RootLayout({ children }) {
  return (
    <html lang="zh-CN">
      <body>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

#### 2. 在组件中使用主题

```tsx
'use client';

import { useTheme } from '@/hooks/useTheme';

export function MyComponent() {
  const { theme, toggleTheme, setTheme } = useTheme();

  return (
    <div>
      <p>当前主题: {theme}</p>
      
      {/* 切换主题 */}
      <button onClick={toggleTheme}>
        切换主题
      </button>
      
      {/* 设置特定主题 */}
      <button onClick={() => setTheme('dark')}>
        深色模式
      </button>
      
      <button onClick={() => setTheme('light')}>
        浅色模式
      </button>
    </div>
  );
}
```

### API 参考

#### ThemeContextValue

```typescript
interface ThemeContextValue {
  theme: 'light' | 'dark';      // 当前主题
  toggleTheme: () => void;       // 切换主题
  setTheme: (theme: Theme) => void;  // 设置特定主题
}
```

### 实现细节

- **持久化**: 使用 localStorage 的 `theme-preference` 键存储用户偏好
- **DOM 更新**: 通过 `data-theme` 属性和 `dark` class 应用主题
- **初始化**: 优先级为 localStorage > 系统偏好 > 默认浅色
- **SSR 兼容**: 使用 `mounted` 状态避免服务端渲染闪烁
