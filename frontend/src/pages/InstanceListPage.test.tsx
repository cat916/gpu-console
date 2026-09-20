import { screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { stubApi } from '../testing/api'
import { anInstance } from '../testing/instances'
import { renderWithProviders } from '../testing/render'
import { InstanceListPage } from './InstanceListPage'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('InstanceListPage', () => {
  it('lists each instance with its hostname, ip and status', async () => {
    stubApi(() => ({
      body: [
        anInstance({ name: 'train-01' }),
        anInstance({
          id: 'inst_5678',
          name: 'eval-02',
          hostname: 'eval-02.gpu.internal',
          ip: '10.0.0.3',
          status: 'failed',
        }),
      ],
    }))

    renderWithProviders(<InstanceListPage />)

    const failedRow = await screen.findByRole('row', { name: /eval-02/ })
    expect(failedRow).toHaveTextContent('eval-02.gpu.internal')
    expect(failedRow).toHaveTextContent('10.0.0.3')
    expect(failedRow).toHaveTextContent('Failed')
    expect(await screen.findByRole('row', { name: /train-01/ })).toHaveTextContent('Running')
  })

  it('invites the user to launch one when there are none', async () => {
    stubApi(() => ({ body: [] }))

    renderWithProviders(<InstanceListPage />)

    expect(await screen.findByText('No instances yet')).toBeInTheDocument()
  })

  it('reports an unreachable api', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    renderWithProviders(<InstanceListPage />)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Can't reach the GPU Console API/)
    })
  })
})
