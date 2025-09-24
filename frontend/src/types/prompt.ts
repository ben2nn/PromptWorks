export interface PromptTag {
  id: number
  name: string
  color: string
  created_at: string
  updated_at: string
}

export interface PromptClass {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface PromptVersion {
  id: number
  prompt_id: number
  version: string
  content: string
  created_at: string
  updated_at: string
}

export interface Prompt {
  id: number
  name: string
  description: string | null
  author: string | null
  prompt_class: PromptClass
  current_version: PromptVersion | null
  versions: PromptVersion[]
  tags: PromptTag[]
  created_at: string
  updated_at: string
}
