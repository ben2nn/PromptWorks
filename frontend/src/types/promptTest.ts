export interface PromptTestTaskCreatePayload {
  name: string
  description?: string | null
  prompt_version_id?: number | null
  owner_id?: number | null
  config?: Record<string, unknown> | null
  units?: PromptTestUnitCreatePayload[]
  auto_execute?: boolean
}

export interface PromptTestUnitCreatePayload {
  task_id?: number
  prompt_version_id?: number | null
  name: string
  description?: string | null
  model_name: string
  llm_provider_id?: number | null
  temperature?: number
  top_p?: number | null
  rounds?: number
  prompt_template?: string | null
  variables?: Record<string, unknown> | unknown[] | null
  parameters?: Record<string, unknown> | null
  expectations?: Record<string, unknown> | null
  tags?: string[] | null
  extra?: Record<string, unknown> | null
}

export interface PromptTestExperimentCreatePayload {
  unit_id?: number
  batch_id?: string | null
  sequence?: number | null
  auto_execute?: boolean
}

export interface PromptTestTask {
  id: number
  name: string
  description: string | null
  prompt_version_id: number | null
  owner_id: number | null
  config: Record<string, unknown> | null
  status: string
  created_at: string
  updated_at: string
  units?: PromptTestUnit[]
}

export interface PromptTestUnit {
  id: number
  task_id: number
  prompt_version_id: number | null
  name: string
  description: string | null
  model_name: string
  llm_provider_id: number | null
  temperature: number
  top_p: number | null
  rounds: number
  prompt_template: string | null
  variables: Record<string, unknown> | unknown[] | null
  parameters: Record<string, unknown> | null
  expectations: Record<string, unknown> | null
  tags: string[] | null
  extra: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface PromptTestExperiment {
  id: number
  unit_id: number
  batch_id: string | null
  sequence: number
  status: string
  outputs: Record<string, unknown>[] | null
  metrics: Record<string, unknown> | null
  error: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
  updated_at: string
}
