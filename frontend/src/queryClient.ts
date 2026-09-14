import { QueryClient } from '@tanstack/react-query'

const MAX_SERVER_ERROR_RETRIES = 2

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: (failureCount, error) =>
          error.status >= 500 && failureCount < MAX_SERVER_ERROR_RETRIES,
      },
    },
  })
}
