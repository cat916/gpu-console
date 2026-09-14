import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import type { ApiError } from '../api/client'

type ApiErrorAlertProps = {
  error: ApiError
  onRetry?: () => void
}

export function ApiErrorAlert({ error, onRetry }: ApiErrorAlertProps) {
  return (
    <Alert
      severity="error"
      action={
        onRetry ? (
          <Button color="inherit" size="small" onClick={onRetry}>
            Retry
          </Button>
        ) : undefined
      }
    >
      {error.message}
    </Alert>
  )
}
