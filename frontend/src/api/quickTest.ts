import type { HttpError } from './http'
import { API_BASE_URL } from './http'
import type { ChatMessagePayload } from '../types/llm'

export interface QuickTestStreamPayload {
  providerId: number
  modelId?: number | null
  modelName?: string | null
  messages: ChatMessagePayload[]
  temperature: number
  parameters?: Record<string, unknown>
  promptId?: number | null
  promptVersionId?: number | null
}

export interface SSEMessage {
  event?: string
  data: string
}

function parseSSEChunk(chunk: string): SSEMessage | null {
  if (!chunk.trim()) return null
  let eventName: string | undefined
  const dataLines: string[] = []
  const lines = chunk.split('\n')
  for (const raw of lines) {
    const line = raw.trimEnd()
    if (!line) continue
    if (line.startsWith('event:')) {
      eventName = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }
  if (!dataLines.length) return null
  return { event: eventName, data: dataLines.join('\n') }
}

async function parseErrorPayload(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch (error) {
    void error
    return text
  }
}

export async function* streamQuickTest(
  payload: QuickTestStreamPayload,
  options: { signal?: AbortSignal } = {}
): AsyncGenerator<SSEMessage, void, undefined> {
  const url = `${API_BASE_URL}/llm-providers/${payload.providerId}/invoke/stream`
  const body: Record<string, unknown> = {
    messages: payload.messages,
    parameters: payload.parameters ?? {},
    temperature: payload.temperature
  }
  if (payload.modelId != null) {
    body.model_id = payload.modelId
  }
  if (payload.modelName) {
    body.model = payload.modelName
  }
  if (payload.promptId != null) {
    body.prompt_id = payload.promptId
  }
  if (payload.promptVersionId != null) {
    body.prompt_version_id = payload.promptVersionId
  }

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: options.signal
  })

  if (!response.ok) {
    const error: HttpError = new Error('请求接口失败')
    error.status = response.status
    error.payload = await parseErrorPayload(response)
    throw error
  }
  if (!response.body) {
    throw new Error('流式响应不可用')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let separatorIndex = buffer.indexOf('\n\n')
      while (separatorIndex !== -1) {
        const chunk = buffer.slice(0, separatorIndex)
        buffer = buffer.slice(separatorIndex + 2)
        const parsed = parseSSEChunk(chunk)
        if (parsed) {
          yield parsed
        }
        separatorIndex = buffer.indexOf('\n\n')
      }
    }
    buffer += decoder.decode()
    const remaining = buffer.trim()
    if (remaining) {
      const parsed = parseSSEChunk(remaining)
      if (parsed) {
        yield parsed
      }
    }
  } finally {
    reader.releaseLock()
  }
}
