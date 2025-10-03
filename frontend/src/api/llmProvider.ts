import { request } from './http'
import type {
  KnownLLMProvider,
  LLMModel,
  LLMModelCreatePayload,
  LLMProvider,
  LLMProviderCreatePayload,
  LLMProviderUpdatePayload
} from '../types/llm'

const BASE_PATH = '/llm-providers'

export function listCommonLLMProviders(): Promise<KnownLLMProvider[]> {
  return request<KnownLLMProvider[]>(`${BASE_PATH}/common`, {
    method: 'GET'
  })
}

export function listLLMProviders(): Promise<LLMProvider[]> {
  return request<LLMProvider[]>(BASE_PATH, {
    method: 'GET'
  })
}

export function createLLMProvider(payload: LLMProviderCreatePayload): Promise<LLMProvider> {
  return request<LLMProvider>(BASE_PATH, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function updateLLMProvider(
  providerId: number,
  payload: LLMProviderUpdatePayload
): Promise<LLMProvider> {
  return request<LLMProvider>(`${BASE_PATH}/${providerId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function createLLMModel(
  providerId: number,
  payload: LLMModelCreatePayload
): Promise<LLMModel> {
  return request<LLMModel>(`${BASE_PATH}/${providerId}/models`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function deleteLLMModel(providerId: number, modelId: number): Promise<void> {
  return request<void>(`${BASE_PATH}/${providerId}/models/${modelId}`, {
    method: 'DELETE'
  })
}

export function deleteLLMProvider(providerId: number): Promise<void> {
  return request<void>(`${BASE_PATH}/${providerId}`, {
    method: 'DELETE'
  })
}
