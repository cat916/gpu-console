import { request } from './client'
import type { CreateInstanceRequest, Image, Instance, InstanceType } from './types'

export function listInstanceTypes(): Promise<InstanceType[]> {
  return request('/api/instance-types')
}

export function listImages(): Promise<Image[]> {
  return request('/api/images')
}

export function listInstances(): Promise<Instance[]> {
  return request('/api/instances')
}

export function getInstance(instanceId: string): Promise<Instance> {
  return request(`/api/instances/${encodeURIComponent(instanceId)}`)
}

export function createInstance(body: CreateInstanceRequest): Promise<Instance> {
  return request('/api/instances', { method: 'POST', json: body })
}

export function deleteInstance(instanceId: string): Promise<Instance> {
  return request(`/api/instances/${encodeURIComponent(instanceId)}`, { method: 'DELETE' })
}
