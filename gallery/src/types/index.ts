// 导出主题相关类型
export type { Theme, ThemeContextValue } from './theme';

// 附件数据结构
export interface AttachmentRead {
  id: number;
  prompt_id: number | null;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  thumbnail_path: string | null;
  file_metadata: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  download_url: string;  // 后端返回的是 download_url，不是 url
  thumbnail_url: string | null;
}

// 提示词数据结构
export interface Prompt {
  id: number;
  name: string;  // 后端返回的是 name，不是 title
  description?: string;
  author?: string;
  content?: string;
  contentzh?: string;
  media_type: string;
  tags: PromptTagRead[];  // 后端返回的是完整的标签对象数组
  prompt_class: PromptClassRead;
  current_version?: PromptVersionRead;
  versions?: PromptVersionRead[];
  attachments?: AttachmentRead[];  // 使用明确的附件类型
  created_at: string;
  updated_at: string;
}

// 提示词分类
export interface PromptClassRead {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

// 提示词版本
export interface PromptVersionRead {
  id: number;
  prompt_id: number;
  version: string;
  content: string;
  contentzh?: string;
  created_at: string;
  updated_at: string;
}

// 提示词标签（完整信息）
export interface PromptTagRead {
  id: number;
  name: string;
  color: string;
  created_at: string;
  updated_at: string;
}

// 标签数据结构
export interface Tag {
  id: string | number;  // 支持数字和字符串类型的 ID
  name: string;
  color?: string;  // 标签颜色（可选）
  count: number;
  prompt_count?: number;  // 后端返回的字段名
  created_at?: string;
  updated_at?: string;
}

// API 响应通用结构
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

// 分页响应数据结构
export interface PaginatedResponse<T> {
  items?: T[];  // 某些接口直接返回数组
  total?: number;
  page?: number;
  pageSize?: number;
  totalPages?: number;
}

// 分页信息
export interface PaginationInfo {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

// 组件 Props 接口

// Header 组件 Props
export interface HeaderProps {
  onSearch?: (query: string) => void;
  searchQuery?: string;
  tags?: Tag[];
  selectedTags?: Set<string>;
  onTagToggle?: (tagId: string) => void;
  totalPrompts?: number;  // 总提示词数量
  filteredPrompts?: number;  // 筛选后的提示词数量
  onClearFilters?: () => void;  // 清除所有筛选
}

// TagFilter 组件 Props
export interface TagFilterProps {
  tags: Tag[];
  selectedTags: Set<string>;  // 从 selectedTag 改为 selectedTags (Set)
  onTagToggle: (tagId: string) => void;  // 从 onTagSelect 改为 onTagToggle
}

// usePrompts Hook 参数接口
export interface UsePromptsParams {
  initialPage?: number;
  limit?: number;
  tags?: string[];  // 支持多标签数组
  search?: string;
  debounceMs?: number;
}

// PromptCard 组件 Props
export interface PromptCardProps {
  prompt: Prompt;
  onClick: (prompt: Prompt) => void;
}

// PromptGrid 组件 Props
export interface PromptGridProps {
  prompts: Prompt[];
  loading: boolean;
  onCardClick: (prompt: Prompt) => void;
  hasMore?: boolean;  // 是否还有更多数据
  onLoadMore?: () => void;  // 加载更多回调
}

// PromptModal 组件 Props
export interface PromptModalProps {
  prompt: Prompt | null;
  isOpen: boolean;
  onClose: () => void;
}

// Button 组件 Props
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

// Input 组件 Props
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

// Modal 组件 Props
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
}
