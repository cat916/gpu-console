export const DNS_ZONE: string = import.meta.env.VITE_DNS_ZONE ?? 'gpu.internal'

export const MAX_INSTANCE_NAME_LENGTH = 63

const DNS_LABEL = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/

export function instanceNameProblem(name: string): string | null {
  if (name.length === 0) {
    return 'Enter a name'
  }
  if (name.length > MAX_INSTANCE_NAME_LENGTH) {
    return `Use at most ${MAX_INSTANCE_NAME_LENGTH} characters (currently ${name.length})`
  }
  if (!DNS_LABEL.test(name)) {
    return 'Use lowercase letters, digits and hyphens, starting and ending with a letter or digit'
  }
  return null
}

export function hostnameFor(name: string): string {
  return `${name}.${DNS_ZONE}`
}
