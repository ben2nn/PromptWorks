// 主题类型定义
export type Theme = 'light' | 'dark';

// 主题 Context 值接口
export interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}
