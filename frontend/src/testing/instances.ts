import type { Instance } from '../api/types'

export function anInstance(overrides: Partial<Instance> = {}): Instance {
  return {
    id: 'inst_1234abcd',
    name: 'train-01',
    hostname: 'train-01.gpu.internal',
    instance_type: '1x-h100',
    image: 'ubuntu-24.04-cuda-12.8',
    status: 'running',
    ip: '10.0.0.2',
    failure_reason: null,
    created_at: '2026-09-18T10:00:00Z',
    updated_at: '2026-09-18T10:00:05Z',
    ...overrides,
  }
}
