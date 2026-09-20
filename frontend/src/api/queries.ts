import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from './client'
import {
  deleteInstance,
  getInstance,
  launchInstance,
  listImages,
  listInstances,
  listInstanceTypes,
} from './instances'
import type { Instance } from './types'

declare module '@tanstack/react-query' {
  interface Register {
    defaultError: ApiError
  }
}

export const REFRESH_INTERVAL_MS = 2000

export const queryKeys = {
  instanceTypes: ['instance-types'] as const,
  images: ['images'] as const,
  instances: ['instances'] as const,
  instance: (instanceId: string) => ['instances', instanceId] as const,
}

export function useInstanceTypes() {
  return useQuery({
    queryKey: queryKeys.instanceTypes,
    queryFn: listInstanceTypes,
    staleTime: Infinity,
  })
}

export function useImages() {
  return useQuery({ queryKey: queryKeys.images, queryFn: listImages, staleTime: Infinity })
}

export function useInstances() {
  return useQuery({
    queryKey: queryKeys.instances,
    queryFn: listInstances,
    refetchInterval: REFRESH_INTERVAL_MS,
  })
}

export function useInstance(instanceId: string) {
  return useQuery({
    queryKey: queryKeys.instance(instanceId),
    queryFn: () => getInstance(instanceId),
    refetchInterval: (query) => (query.state.error?.status === 404 ? false : REFRESH_INTERVAL_MS),
  })
}

function useStoreInstance() {
  const queryClient = useQueryClient()
  return (instance: Instance) => {
    queryClient.setQueryData(queryKeys.instance(instance.id), instance)
    void queryClient.invalidateQueries({ queryKey: queryKeys.instances, exact: true })
  }
}

export function useLaunchInstance() {
  const storeInstance = useStoreInstance()
  return useMutation({ mutationFn: launchInstance, onSuccess: storeInstance })
}

export function useDeleteInstance() {
  const storeInstance = useStoreInstance()
  return useMutation({ mutationFn: deleteInstance, onSuccess: storeInstance })
}
