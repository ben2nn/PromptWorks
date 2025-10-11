import { request } from './http'
import type {
  PromptTestTask,
  PromptTestTaskCreatePayload,
  PromptTestExperiment,
  PromptTestExperimentCreatePayload,
  PromptTestUnit
} from '../types/promptTest'

const BASE_PATH = '/prompt-test'

export function createPromptTestTask(payload: PromptTestTaskCreatePayload): Promise<PromptTestTask> {
  return request<PromptTestTask>(`${BASE_PATH}/tasks`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function getPromptTestTask(taskId: number): Promise<PromptTestTask> {
  return request<PromptTestTask>(`${BASE_PATH}/tasks/${taskId}`, {
    method: 'GET'
  })
}

export function createPromptTestExperiment(
  unitId: number,
  payload: PromptTestExperimentCreatePayload
): Promise<PromptTestExperiment> {
  return request<PromptTestExperiment>(`${BASE_PATH}/units/${unitId}/experiments`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function listPromptTestUnits(taskId: number): Promise<PromptTestUnit[]> {
  return request<PromptTestUnit[]>(`${BASE_PATH}/tasks/${taskId}/units`, {
    method: 'GET'
  })
}

export function getPromptTestUnit(unitId: number): Promise<PromptTestUnit> {
  return request<PromptTestUnit>(`${BASE_PATH}/units/${unitId}`, {
    method: 'GET'
  })
}

export function listPromptTestExperiments(unitId: number): Promise<PromptTestExperiment[]> {
  return request<PromptTestExperiment[]>(`${BASE_PATH}/units/${unitId}/experiments`, {
    method: 'GET'
  })
}
