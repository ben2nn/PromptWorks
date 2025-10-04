import { request } from './http'
import type {
  ListTestRunParams,
  TestRun,
  TestRunCreatePayload,
  TestRunStatus,
  TestResult
} from '../types/testRun'

function buildSearchParams(params: ListTestRunParams = {}): string {
  const search = new URLSearchParams()
  if (params.status) {
    search.set('status', params.status)
  }
  if (typeof params.prompt_version_id === 'number') {
    search.set('prompt_version_id', String(params.prompt_version_id))
  }
  if (typeof params.limit === 'number') {
    search.set('limit', String(params.limit))
  }
  if (typeof params.offset === 'number') {
    search.set('offset', String(params.offset))
  }
  const query = search.toString()
  return query ? `?${query}` : ''
}

export function listTestRuns(params: ListTestRunParams = {}): Promise<TestRun[]> {
  const query = buildSearchParams(params)
  return request<TestRun[]>(`/test_prompt/${query}`)
}

export function createTestRun(payload: TestRunCreatePayload): Promise<TestRun> {
  return request<TestRun>('/test_prompt/', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function getTestRun(testRunId: number): Promise<TestRun> {
  return request<TestRun>(`/test_prompt/${testRunId}`)
}

export function listTestRunResults(testRunId: number): Promise<TestResult[]> {
  return request<TestResult[]>(`/test_prompt/${testRunId}/results`)
}

export type { TestRun, TestRunStatus }
