import { vi } from 'vitest'

type Reply = { status?: number; body?: unknown }
type Handler = (path: string, init?: RequestInit) => Reply | undefined

export function stubApi(handler: Handler) {
  const fetchMock = vi.fn(async (path: string, init?: RequestInit) => {
    const reply = handler(path, init) ?? { status: 404, body: null }
    const status = reply.status ?? 200
    return {
      ok: status < 400,
      status,
      json: async () => reply.body ?? null,
    } as Response
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

export function apiError(status: number, code: string, message: string, fields: unknown[] = []) {
  return { status, body: { error: { code, message, fields } } }
}
