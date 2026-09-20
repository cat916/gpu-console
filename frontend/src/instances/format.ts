import type { InstanceStatus, InstanceType } from '../api/types'

export const DELETABLE_STATUSES: ReadonlySet<InstanceStatus> = new Set(['running', 'failed'])

export function formatGpus(instanceType: InstanceType): string {
  return `${instanceType.gpu_count}× ${instanceType.gpu_model}`
}

export function formatSpecs(instanceType: InstanceType): string {
  return `${instanceType.vcpus} vCPU · ${instanceType.memory_gb} GB RAM`
}

export function formatPricePerHour(pricePerHour: number): string {
  return `$${pricePerHour.toFixed(2)}/h`
}

export function formatTimestamp(isoTimestamp: string): string {
  return new Date(isoTimestamp).toLocaleString()
}

export function digCommand(hostname: string): string {
  return `dig @127.0.0.1 -p 1053 ${hostname}`
}
