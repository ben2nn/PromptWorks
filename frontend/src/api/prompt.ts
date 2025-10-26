import { request, type HttpError } from './http'
import type { Prompt, PromptVersion, MediaType } from '../types/prompt'

export interface PromptListParams {
  q?: string
  limit?: number
  offset?: number
  media_type?: MediaType
}

export interface PromptCreatePayload {
  name: string
  description?: string | null
  author?: string | null
  class_id?: number
  class_name?: string
  class_description?: string | null
  version: string
  content: string
  contentzh?: string | null
  media_type?: MediaType
  tag_ids?: number[]
}

export interface PromptUpdatePayload {
  name?: string | null
  description?: string | null
  author?: string | null
  class_id?: number
  class_name?: string
  class_description?: string | null
  version?: string | null
  content?: string | null
  contentzh?: string | null
  media_type?: MediaType
  activate_version_id?: number | null
  tag_ids?: number[] | null
}

export async function listPrompts(params: PromptListParams = {}): Promise<Prompt[]> {
  const searchParams = new URLSearchParams()
  if (params.q) searchParams.set('q', params.q)
  if (typeof params.limit === 'number') searchParams.set('limit', String(params.limit))
  if (typeof params.offset === 'number') searchParams.set('offset', String(params.offset))
  if (params.media_type) searchParams.set('media_type', params.media_type)
  const query = searchParams.toString()
  const path = `/prompts${query ? `?${query}` : ''}`
  return request<Prompt[]>(path)
}

export async function getPrompt(promptId: number): Promise<Prompt> {
  return request<Prompt>(`/prompts/${promptId}`)
}

export async function createPrompt(payload: PromptCreatePayload): Promise<Prompt> {
  return request<Prompt>('/prompts/', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function updatePrompt(
  promptId: number,
  payload: PromptUpdatePayload
): Promise<Prompt> {
  return request<Prompt>(`/prompts/${promptId}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export async function deletePrompt(promptId: number): Promise<void> {
  await request<void>(`/prompts/${promptId}`, {
    method: 'DELETE'
  })
}

export async function createPromptVersion(
  promptId: number,
  version: string,
  content: string,
  contentzh?: string | null
): Promise<Prompt> {
  return updatePrompt(promptId, { version, content, contentzh })
}

export async function switchPromptVersion(
  promptId: number,
  version: PromptVersion
): Promise<Prompt> {
  return updatePrompt(promptId, { activate_version_id: version.id })
}

export type { HttpError }

// 媒体类型相关API
export interface MediaTypeInfo {
  value: MediaType
  label: string
  description: string
  icon?: string
  validation?: {
    maxSize: number
    allowedTypes: string[]
    allowedExtensions: string[]
  }
}

export interface MediaTypeUpdateRequest {
  media_type: MediaType
}

export async function getMediaTypes(): Promise<MediaTypeInfo[]> {
  return request<MediaTypeInfo[]>('/media-types')
}

export async function updatePromptMediaType(
  promptId: number,
  mediaType: MediaType
): Promise<Prompt> {
  return request<Prompt>(`/prompts/${promptId}/media-type`, {
    method: 'PUT',
    body: JSON.stringify({ media_type: mediaType })
  })
}

// 附件相关的提示词API扩展
export interface PromptWithAttachmentsParams {
  include_attachments?: boolean
  attachment_limit?: number
}

export async function getPromptWithAttachments(
  promptId: number,
  params: PromptWithAttachmentsParams = {}
): Promise<Prompt> {
  const searchParams = new URLSearchParams()
  if (params.include_attachments !== undefined) {
    searchParams.set('include_attachments', String(params.include_attachments))
  }
  if (params.attachment_limit !== undefined) {
    searchParams.set('attachment_limit', String(params.attachment_limit))
  }
  
  const query = searchParams.toString()
  const path = `/prompts/${promptId}${query ? `?${query}` : ''}`
  return request<Prompt>(path)
}