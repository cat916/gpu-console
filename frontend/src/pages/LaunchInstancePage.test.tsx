import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiError, stubApi } from '../testing/api'
import { anInstance } from '../testing/instances'
import { renderWithProviders } from '../testing/render'
import { LaunchInstancePage } from './LaunchInstancePage'

const INSTANCE_TYPES = [
  {
    id: '1x-h100',
    gpu_model: 'H100 80GB',
    gpu_count: 1,
    vcpus: 22,
    memory_gb: 185,
    price_per_hour: 2.29,
  },
]
const IMAGES = [{ id: 'ubuntu-24.04-cuda-12.8', name: 'Ubuntu 24.04 + CUDA 12.8' }]

function stubCatalog(launchReply: { status?: number; body?: unknown }) {
  return stubApi((path, init) => {
    if (path === '/api/instance-types') {
      return { body: INSTANCE_TYPES }
    }
    if (path === '/api/images') {
      return { body: IMAGES }
    }
    if (path === '/api/instances' && init?.method === 'POST') {
      return launchReply
    }
    return undefined
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('LaunchInstancePage', () => {
  it('launches an instance with the chosen type and image', async () => {
    const user = userEvent.setup()
    const fetchMock = stubCatalog({ status: 202, body: anInstance() })
    renderWithProviders(<LaunchInstancePage />)

    await user.type(await screen.findByLabelText(/Name/), 'train-01')
    await user.click(screen.getByRole('button', { name: 'Launch' }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/instances',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            name: 'train-01',
            instance_type: '1x-h100',
            image: 'ubuntu-24.04-cuda-12.8',
          }),
        }),
      )
    })
  })

  it('shows the hostname the instance will get', async () => {
    const user = userEvent.setup()
    stubCatalog({ status: 202, body: anInstance() })
    renderWithProviders(<LaunchInstancePage />)

    await user.type(await screen.findByLabelText(/Name/), 'eval-02')

    expect(screen.getByText('Hostname: eval-02.gpu.internal')).toBeInTheDocument()
  })

  it('refuses to submit a name that is not a dns label', async () => {
    const user = userEvent.setup()
    const fetchMock = stubCatalog({ status: 202, body: anInstance() })
    renderWithProviders(<LaunchInstancePage />)

    await user.type(await screen.findByLabelText(/Name/), 'Train_01')
    await user.click(screen.getByRole('button', { name: 'Launch' }))

    expect(screen.getByText(/lowercase letters, digits and hyphens/)).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalledWith('/api/instances', expect.anything())
  })

  it('puts a rejected name next to the name field', async () => {
    const user = userEvent.setup()
    stubCatalog(
      apiError(409, 'name_taken', 'An instance named train-01 already exists', [
        { field: 'name', message: 'This name is already in use' },
      ]),
    )
    renderWithProviders(<LaunchInstancePage />)

    await user.type(await screen.findByLabelText(/Name/), 'train-01')
    await user.click(screen.getByRole('button', { name: 'Launch' }))

    expect(await screen.findByText('This name is already in use')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('reports a full network above the form', async () => {
    const user = userEvent.setup()
    stubCatalog(
      apiError(409, 'network_full', 'No free IP addresses in the instance network'),
    )
    renderWithProviders(<LaunchInstancePage />)

    await user.type(await screen.findByLabelText(/Name/), 'train-01')
    await user.click(screen.getByRole('button', { name: 'Launch' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No free IP addresses in the instance network',
    )
  })
})
