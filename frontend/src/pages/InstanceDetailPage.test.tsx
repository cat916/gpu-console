import { screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { stubApi } from '../testing/api'
import { anInstance } from '../testing/instances'
import { renderWithProviders } from '../testing/render'
import { InstanceDetailPage } from './InstanceDetailPage'

function renderDetail() {
  renderWithProviders(<InstanceDetailPage />, {
    path: '/instances/:instanceId',
    route: '/instances/inst_1234abcd',
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('InstanceDetailPage', () => {
  it('explains why a failed instance failed', async () => {
    stubApi(() => ({
      body: anInstance({
        status: 'failed',
        failure_reason: 'Launch did not complete. Delete this instance and try again.',
      }),
    }))

    renderDetail()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Launch did not complete. Delete this instance and try again.',
    )
    expect(screen.getByRole('button', { name: 'Delete' })).toBeEnabled()
  })

  it('shows the reserved ip while the instance is still provisioning', async () => {
    stubApi(() => ({ body: anInstance({ status: 'provisioning' }) }))

    renderDetail()

    expect(await screen.findByText('10.0.0.2')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete' })).toBeDisabled()
  })

  it('says so when the instance is gone', async () => {
    stubApi(() => ({ status: 404, body: { error: { code: 'not_found', message: 'No instance' } } }))

    renderDetail()

    expect(await screen.findByText(/No instance with ID inst_1234abcd/)).toBeInTheDocument()
  })
})
