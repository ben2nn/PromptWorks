export type TestRunStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface Metric {
  id: number
  result_id: number
  is_valid_json: boolean | null
  schema_pass: boolean | null
  missing_fields: Record<string, unknown> | null
  type_mismatches: Record<string, unknown> | null
  consistency_score: number | null
  numeric_accuracy: number | null
  boolean_accuracy: number | null
  created_at: string
}

export interface TestResult {
  id: number
  test_run_id: number
  run_index: number
  output: string
  parsed_output: Record<string, unknown> | null
  tokens_used: number | null
  latency_ms: number | null
  created_at: string
  metrics: Metric[]
}

export interface TestRun {
  id: number
  prompt_version_id: number
  batch_id: string | null
  model_name: string
  model_version: string | null
  temperature: number
  top_p: number
  repetitions: number
  schema: Record<string, unknown> | null
  status: TestRunStatus
  failure_reason: string | null
  notes: string | null
  created_at: string
  updated_at: string
  prompt_version?: import('./prompt').PromptVersion | null
  prompt?: import('./prompt').Prompt | null
  results: TestResult[]
}

export interface TestRunCreatePayload {
  prompt_version_id: number
  model_name: string
  model_version?: string | null
  temperature?: number
  top_p?: number
  repetitions?: number
  schema?: Record<string, unknown> | null
  notes?: string | null
  batch_id?: string | null
}

export interface ListTestRunParams {
  status?: TestRunStatus
  prompt_version_id?: number
  limit?: number
  offset?: number
}
