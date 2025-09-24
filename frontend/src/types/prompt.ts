export interface PromptSummary {
  id: string
  name: string
  description: string
  tags: string[]
  owner: string
  scenario: string
  updatedAt: string
  latestVersion: string
}

export interface PromptVersion {
  version: string
  createdAt: string
  author: string
  content: string
  changeLog: string
}

export interface PromptDetail extends PromptSummary {
  versions: PromptVersion[]
}
