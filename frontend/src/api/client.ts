import type { ErrorResponse, FieldError } from './types'

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fields: FieldError[]

  constructor(status: number, code: string, message: string, fields: FieldError[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fields = fields
  }
}

const UNREACHABLE_MESSAGE = "Can't reach the GPU Console API. Check that the backend is running."

type RequestOptions = {
  method?: 'GET' | 'POST' | 'DELETE'
  json?: unknown
}

function isErrorResponse(body: unknown): body is ErrorResponse {
  return typeof body === 'object' && body !== null && 'error' in body
}

export async function request<T>(path: string, { method = 'GET', json }: RequestOptions = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      method,
      headers:
        json === undefined
          ? { Accept: 'application/json' }
          : { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: json === undefined ? undefined : JSON.stringify(json),
    })
  } catch {
    throw new ApiError(0, 'unreachable', UNREACHABLE_MESSAGE)
  }

  const body: unknown = await response.json().catch(() => null)
  if (response.ok) {
    return body as T
  }
  if (isErrorResponse(body)) {
    throw new ApiError(response.status, body.error.code, body.error.message, body.error.fields ?? [])
  }
  if (response.status >= 500) {
    throw new ApiError(response.status, 'unreachable', UNREACHABLE_MESSAGE)
  }
  throw new ApiError(response.status, 'http_error', `The API responded with status ${response.status}`)
}
