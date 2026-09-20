import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, request } from './client'

function respondWith(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: status < 400, status, json: async () => body }),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('request', () => {
  it('returns the parsed body', async () => {
    respondWith(200, { id: 'inst_1234abcd' })

    await expect(request('/api/instances/inst_1234abcd')).resolves.toEqual({
      id: 'inst_1234abcd',
    })
  })

  it('sends json bodies with a content type', async () => {
    respondWith(202, {})

    await request('/api/instances', { method: 'POST', json: { name: 'train-01' } })

    expect(fetch).toHaveBeenCalledWith(
      '/api/instances',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        body: '{"name":"train-01"}',
      }),
    )
  })

  it('turns an api error body into an ApiError', async () => {
    respondWith(409, {
      error: {
        code: 'network_full',
        message: 'No free IP addresses in the instance network',
        fields: [],
      },
    })

    await expect(request('/api/instances')).rejects.toMatchObject({
      status: 409,
      code: 'network_full',
      message: 'No free IP addresses in the instance network',
    })
  })

  it('keeps the field errors of a validation failure', async () => {
    respondWith(422, {
      error: {
        code: 'validation_failed',
        message: 'The request has invalid fields',
        fields: [{ field: 'name', message: 'Enter a name' }],
      },
    })

    await expect(request('/api/instances')).rejects.toMatchObject({
      fields: [{ field: 'name', message: 'Enter a name' }],
    })
  })

  it('reports an unreachable api when fetch fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    const error = await request('/api/instances').catch((thrown: ApiError) => thrown)

    expect(error).toMatchObject({ status: 0, code: 'unreachable' })
  })

  it('reports an unreachable api for a server error without a body', async () => {
    respondWith(502, null)

    await expect(request('/api/instances')).rejects.toMatchObject({ code: 'unreachable' })
  })
})
